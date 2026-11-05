# Implementation Spec: Enterprise Workflow Speed Optimization

**Created**: 2026-11-05T19:19:30+05:30  
**Feature**: `enterprise-workflow-speed-optimization`  
**Status**: Plan Approved Pending / Pre-Implementation

---

## 1. Executive Summary & Optimization Architecture

The current Agnostic Research & Report Generation Swarm exhibits a 7.79x concurrency speedup across 10 sections, but takes **574.91 seconds (9.58 minutes)** of wall-clock time and **4,477.04 seconds (74.6 minutes)** of total compute time.

Mathematical analysis of `backend/artifacts/Research_Report_generate_d_o_report_for_nvidia_20261105_135248_telemetry.json` reveals that:
- **Perplexity Web Search** takes only **34.8s (0.78%)** of compute.
- **Section Drafting** takes **899.9s (20.1%)** of compute.
- **Fact Extraction + Gap Analysis** consumes **3,416.1s (76.3%)** of total compute!

The root cause of this latency is twofold:
1. **Model Misallocation**: Flagship reasoning models (`claude-opus-4-8`, `gpt-5.4`) are being used for high-volume atomic JSON extraction (53.7%) and checklist gap checks (22.6%), operating at slow token generation speeds and hitting tight output token quotas.
2. **Serial Multi-Round Loops & Semaphore Head-of-Line Blocking**: All 10 sections execute 3 sequential rounds of Search -> Extract -> Gap, and all 71 LLM calls share a single `asyncio.Semaphore(3)`.

This implementation plan details the code changes required to reduce wall-clock execution time to **75–120 seconds** without reducing evidence density or analytical quality.

---

## 2. Component Design & Code Modifications

### 2.1 Component 1: Role-Segregated Concurrency Semaphores (`roles.py`)
Replace the single `AZURE_SEMAPHORE` with dual task-tier semaphores:

```python
# Concurrency configuration per task tier
FAST_CONCURRENCY = int(os.environ.get("MAX_CONCURRENCY_FAST", "12"))
HEAVY_CONCURRENCY = int(os.environ.get("MAX_CONCURRENCY_HEAVY", "4"))

SEMAPHORE_FAST = asyncio.Semaphore(FAST_CONCURRENCY)
SEMAPHORE_HEAVY = asyncio.Semaphore(HEAVY_CONCURRENCY)

ROLE_SEMAPHORE_MAPPING: Dict[str, asyncio.Semaphore] = {
    "plan": SEMAPHORE_FAST,
    "extract": SEMAPHORE_FAST,
    "gap": SEMAPHORE_FAST,
    "verify": SEMAPHORE_FAST,
    "draft": SEMAPHORE_HEAVY,
    "synthesize": SEMAPHORE_HEAVY,
}
```

In `_execute_azure_chat_with_tokens`:
```python
# Acquire semaphore corresponding to role
sem = ROLE_SEMAPHORE_MAPPING.get(role, SEMAPHORE_HEAVY)
async with sem:
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(...)
```

### 2.2 Component 2: Smart Asymmetric Model Resolution (`roles.py`)
Modify `resolve_task_model` to distinguish between flagship narrative drafting vs. high-throughput structural extraction:

```python
def resolve_task_model(
    role: str,
    task_models: Optional[Dict[str, str]] = None,
    model_override: Optional[str] = None,
    provider: Optional[str] = None,
    force_all_roles: bool = False,
) -> str:
    norm_role = "synthesize" if role.lower().strip() in ["synth", "synthesize"] else role.lower().strip()
    
    # 1. Explicit per-task override takes highest precedence
    if task_models:
        cand = task_models.get(norm_role) or task_models.get(role)
        if cand and cand.strip():
            return cand.strip()

    if ACTIVE_TASK_MODELS.get(norm_role):
        return ACTIVE_TASK_MODELS[norm_role].strip()

    prov = (provider or ACTIVE_PROVIDER).lower()
    prov_models = PROVIDER_MODELS.get(prov, PROVIDER_MODELS.get("azure", {}))
    role_tier = ROLE_TIER_MAPPING.get(norm_role, "medium")

    # 2. If force_all_roles is set, use model_override across all roles
    if force_all_roles and model_override and model_override.strip():
        return model_override.strip()

    # 3. Smart Asymmetric Tiering:
    # Heavy cognitive roles (draft, synthesize) adopt the top-level --model override
    if norm_role in ["draft", "synthesize"]:
        if model_override and model_override.strip():
            return model_override.strip()
        return prov_models.get("reasoning", "claude-opus-4-8")

    # Fast structural transformation roles (extract, gap, plan) adopt the fast/medium tier
    return prov_models.get(role_tier, "claude-sonnet-4-6")
```

### 2.3 Component 3: Adaptive Depth & Sufficiency Gate (`orchestrator.py`)
Enhance `_process_section` with an early sufficiency check:

```python
# After Round 1 extraction:
claims_count = len(ledger.for_section(section.name))
checklist_count = len(section.required_fields)

# Sufficiency heuristic:
# If Round 1 uncovered >= 10 verifiable claims AND addressed major checklist fields:
if rnd == 0 and mode == "deep" and claims_count >= 10:
    # Run a fast gap evaluation; if gap returns 0 queries or coverage is sufficient, exit early
    if not next_queries:
        _sec_notify("adaptive_exit", f"[ADAPTIVE GATE] [{section.title}] 100% checklist coverage achieved in R1 ({claims_count} facts). Proceeding directly to drafting.")
        break
```

In `PLAN_SYSTEM`, expand initial query capacity:
```python
PLAN_SYSTEM = """You are the Plan role in an analytical research pipeline.
Given a subject and a section specification, formulate 4 to 6 highly targeted, distinct web search queries
that simultaneously address ALL items in the section checklist.
Output format: JSON object with key "queries": [{"text": "query string", "domains": ["example.com"], "recency": "year"}]"""
```

### 2.4 Component 4: In-Memory Cross-Section Perplexity Query Cache (`retrieval.py`)
Add an in-memory session cache:

```python
class PerplexitySearchQueue:
    def __init__(self, ...):
        self._query_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_lock = asyncio.Lock()

    def _normalize_query(self, query: str) -> str:
        return " ".join(query.lower().strip().split())

    async def search(self, query: str, ...):
        norm_key = self._normalize_query(query)
        async with self._cache_lock:
            if norm_key in self._query_cache:
                return self._query_cache[norm_key], {"cached": True, "duration_ms": 0.0}

        # Execute network search...
        results, meta = await self._network_search(...)
        async with self._cache_lock:
            self._query_cache[norm_key] = results
        return results, meta
```

### 2.5 Component 5: Schema Minification & Token Budgeting (`roles.py`)
Minify `EXTRACT_SYSTEM` and reduce `max_tokens`:
```python
ROLES_CONFIG["extract"]["max_tokens"] = 1500  # Reduced from 4000
ROLES_CONFIG["plan"]["max_tokens"] = 1200     # Reduced from 4000
ROLES_CONFIG["gap"]["max_tokens"] = 800       # Reduced from 1000
```

---

## 3. Parity and Packaging Plan

All changes will be symmetrically applied to:
1. `backend/app/workflows/agnostic_research_report/`
2. `agnostic_workflow/`
3. `agnostic_workflow.zip` (repackaged using `scratch/repack_zip.py`)

No third-party packages beyond existing requirements (`httpx`, `asyncio`, `reportlab`, `dotenv`) will be added. Standalone execution will remain 100% self-contained.


---

## 4. Execution Log

### 2026-11-05T20:05:00+05:30 — Step 1: Session-Level In-Memory Perplexity Query Cache (Pillar 4)
- **Files Changed**:
  - `backend/app/workflows/agnostic_research_report/retrieval.py`
  - `agnostic_workflow/retrieval.py`
  - `backend/test_agnostic_research_report.py`
  - `agnostic_workflow/test_standalone_workflow.py`
- **Reason**:
  - Implemented session-scoped in-memory query caching with query normalization (whitespace collapse, lowercase canonicalization, domain sorting) to provide instant 0ms retrieval on overlapping queries across sections, avoiding repeated disk and network lookups.
- **Diagnostics & Resolutions Encountered**:
  - *Failure*: Initial test run in `backend/test_agnostic_research_report.py` failed with `NameError: name 'uuid' is not defined`.
  - *Resolution*: Imported `uuid` at the top of `backend/test_agnostic_research_report.py`.
- **Tests Added/Updated**:
  - `TestPerplexitySessionQueryCache.test_session_query_cache_hit_and_stats` in backend unit test suite.
  - `TestStandaloneAgnosticWorkflow.test_15_perplexity_session_query_cache` in standalone package test suite.
- **Commands Run**:
  - `.\backend\venv\Scripts\python.exe -m unittest backend/test_agnostic_research_report.py -v` -> Passed (24 tests OK, 2.226s).
  - `.\backend\venv\Scripts\python.exe agnostic_workflow/test_standalone_workflow.py` -> Passed (16 tests OK, 1.484s, 0 external app imports).
- **Result**: Step 1 complete with 100% test pass and verified parity.

### 2026-11-05T20:07:00+05:30 — Step 2: Adaptive Depth & Upfront Batch Planning (Pillar 3)
- **Files Changed**:
  - `backend/app/workflows/agnostic_research_report/roles.py`
  - `agnostic_workflow/roles.py`
  - `backend/app/workflows/agnostic_research_report/orchestrator.py`
  - `agnostic_workflow/orchestrator.py`
  - `backend/test_agnostic_research_report.py`
  - `agnostic_workflow/test_standalone_workflow.py`
- **Reason**:
  - Expanded Round 1 planning to formulate 4 to 6 multi-faceted search queries covering all checklist items simultaneously in a single concurrent Perplexity batch.
  - Implemented the Adaptive Sufficiency Gate in `_process_section`: if Round 1 produces solid evidence (`len(sec_rows) >= min_adaptive_claims`, default 10) and checklist requirements are satisfied (0 gap queries), or if 15+ claims are achieved across 2 rounds, the section fast-tracks directly to narrative drafting, bypassing redundant search and extraction iterations.
- **Diagnostics & Resolutions Encountered**:
  - None; both backend and standalone modules cleanly applied the adaptive gate and passed all assertions without error.
- **Tests Added/Updated**:
  - `TestAgnosticAdaptiveDepth.test_plan_system_prompt_expanded_queries` in backend unit test suite.
  - `TestAgnosticAdaptiveDepth.test_adaptive_gate_triggers_on_sufficient_evidence` in backend unit test suite.
  - `TestStandaloneAgnosticWorkflow.test_16_adaptive_depth_sufficiency_gate` in standalone package test suite.
- **Commands Run**:
  - `.\backend\venv\Scripts\python.exe -m unittest backend/test_agnostic_research_report.py -v` -> Passed (26 tests OK, 2.792s).
  - `.\backend\venv\Scripts\python.exe agnostic_workflow/test_standalone_workflow.py` -> Passed (17 tests OK, 2.166s, 0 external app imports).
- **Result**: Step 2 complete with 100% test pass and verified parity.


### 2026-11-05T22:10:00+05:30 — Step 3: Rework Elimination via Direct Single-Pass & Query/Snippet Caps (Strategies 1 & 4)
- **Files Changed**:
  - `backend/app/workflows/agnostic_research_report/roles.py`
  - `agnostic_workflow/roles.py`
  - `backend/app/workflows/agnostic_research_report/orchestrator.py`
  - `agnostic_workflow/orchestrator.py`
  - `backend/test_agnostic_research_report.py`
  - `agnostic_workflow/test_standalone_workflow.py`
  - `agnostic_workflow/run_workflow.py`
  - `agnostic_workflow.zip`
- **Reason**:
  - In telemetry analysis of run `20261105_210115`, Round 2 rework and Gap Analysis accounted for 2,952.7 seconds (~49.2 minutes) of cumulative compute (39.4% of total pipeline compute). Round 1 had already yielded 147 claims across 10 sections (~15 facts/section).
  - **Strategy 1 (Adaptive Fast-Track Bypass)**: If Round 1 extraction achieves $\ge 12$ verified claims (`min_adaptive_claims`, default 12, configurable via `ADAPTIVE_DEPTH_MIN_CLAIMS`), bypass Gap Analysis entirely (`gap_ms = 0.0`) and fast-track directly to Narrative Drafting in 1 round. This completely eliminates the ~80s gap analysis call and the ~350s Round 2 rework loop for compliant sections.
  - **Strategy 4 (Strict Cap on Round 2 Queries & Snippets)**: If Round 1 yields $< 12$ claims, `GAP_SYSTEM` prompt instructs generating at most 2 targeted follow-up queries (`[:2]`). In Round 2 extraction, snippet input is capped at 6 snippets (instead of 10) to prevent token rate-limit explosions and fallback cascades.
- **Diagnostics & Resolutions Encountered**:
  - *Failure*: Powershell invocation without explicit virtual environment path failed with `The term '.\backend\venv\Scripts\python.exe' is not recognized`.
  - *Resolution*: Navigated to project root (`cd "C:\Users\punee\OneDrive\Documents\GitHub\swarm-backend"`) and used full relative path to virtual environment python.
- **Tests Added/Updated**:
  - `TestAgnosticReworkReduction.test_gap_system_prompt_capped_at_two_queries` in backend test suite.
  - `TestAgnosticReworkReduction.test_strategy_1_bypasses_gap_when_r1_claims_sufficient` in backend test suite.
  - `TestStandaloneAgnosticWorkflow.test_17_strategy_1_and_4_rework_reduction` in standalone test suite.
- **Commands Run**:
  - `.\backend\venv\Scripts\python.exe -m unittest backend/test_agnostic_research_report.py` -> Passed (28 tests OK, 2.620s).
  - `.\backend\venv\Scripts\python.exe agnostic_workflow/test_standalone_workflow.py` -> Passed (18 tests OK, 1.569s, 0 external app imports).
  - `.\backend\venv\Scripts\python.exe backend/run_agnostic_research_report.py --help` -> Verified options and help text.
  - `.\backend\venv\Scripts\python.exe agnostic_workflow/run_workflow.py --help` -> Verified 100% options parity.
  - Repacked `agnostic_workflow.zip` (52,247 bytes).
- **Result**: Step 3 complete with 100% test pass, verified symmetrical parity, and repacked zip distribution.
