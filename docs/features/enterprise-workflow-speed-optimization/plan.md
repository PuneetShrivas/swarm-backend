# Feature: Enterprise Workflow Speed Optimization (Agnostic Research Pipeline)

**Created**: 2026-11-05T19:16:00+05:30  
**Status**: Draft  
**Slug**: `enterprise-workflow-speed-optimization`

---

## Status

Draft (Awaiting User Approval Before Implementation)

---

## Goal

Accelerate the Agnostic Research and Report Generation Swarm by **4x to 8x**—reducing full 10-section deep institutional report wall-clock generation time from **~575 seconds (9.6 minutes)** down to **~75–120 seconds (1.2–2.0 minutes)**—while strictly maintaining:
1. Complete domain-agnostic adaptability across any prompt specification.
2. Uncompromising institutional analytical rigor, granular numerical coverage, and [E###] empirical footnote citation density.
3. Full compatibility with multi-provider backends (Azure Foundry OpenAI & Anthropic, Google Gemini, Groq, Iteracompute).
4. Zero regressions in standalone zero-dependency distribution (`agnostic_workflow`).

---

## Scope

### In scope:
1. **Telemetry & Latency Profiling Discovery**: Quantitative bottleneck decomposition across real runs (identifying that Stage 2 compute is 4,477s total, where Extraction accounts for 53.7% / 2,404s, Gap Analysis accounts for 22.6% / 1,012s, Drafting is 20.1% / 900s, and Perplexity retrieval is only 0.8% / 35s).
2. **Asymmetric Role-to-Model Tiering Architecture**: Decoupling the global `--model` flag so that structural transformation roles (`extract`, `gap`, `plan`) automatically route to lightning-fast, high-throughput models (e.g., `gpt-5-mini`, `gemini-2.5-flash`, `groq/llama-3.3-70b`, `claude-3-5-haiku`), while preserving premier reasoning models (`claude-opus-4-8`, `gpt-5.4`, `gemini-2.5-pro`) exclusively for narrative `draft` and `synthesize`.
3. **Adaptive Depth & Upfront Batch Planning**: Replacing serialized 3-round iterative searches with rich upfront planning (4–6 multi-faceted queries batched in a single Perplexity call in Round 1), accompanied by an evidence sufficiency heuristic (terminating subsequent rounds if checklist coverage >= 85% or claims >= 12).
4. **Role-Segregated Adaptive Concurrency**: Splitting the global `AZURE_SEMAPHORE = asyncio.Semaphore(3)` into dedicated semaphores for high-throughput extraction/gap tasks (concurrency 10–15) vs. heavy drafting/synthesis tasks (concurrency 3–5), eliminating head-of-line blocking.
5. **Cross-Section Query Deduplication & Evidence Ledger Sharing**: In-memory session cache for Perplexity queries and cross-section evidence awareness, preventing redundant searches across overlapping sections.
6. **Token Schema & Prompt Optimization**: Minifying JSON schemas in `extract` and `gap`, setting strict appropriate `max_tokens` (1,200–1,500 instead of 4,000), eliminating redundant keys and prompt boilerplate.
7. **Pipelined Incremental Synthesis**: Allowing Stage 3 synthesis to incrementally ingest completed section drafts and metrics as they finish rather than waiting for all 10 sections in a blocking barrier.
8. **Parity Synchronization**: Maintaining 100% parity across `backend/app/workflows/agnostic_research_report/` and `agnostic_workflow/` (and updating `agnostic_workflow.zip`).

### Out of scope:
- Changing the Markdown report structure or removing required sections.
- Replacing Perplexity AI with an ungrounded search provider.
- Lowering evidence verification or citation thresholds.
- Introducing external non-standard databases or heavyweight vector stores (keeping the pipeline lightweight and portable).

---

## Current Behavior

Today, running `run_agnostic_research_report.py` on a deep 10-section report (e.g. `Generate D&O report for NVIDIA`) produces the following empirical performance profile (from `Research_Report_generate_d_o_report_for_nvidia_20261105_135248_telemetry.json`):

- **Total Wall-Clock Time**: **574.91 seconds** (9.58 minutes)
- **Total Compute Time**: **4,477.04 seconds** (74.62 minutes)
- **Concurrency Speedup**: 7.79x
- **Breakdown by Sub-Task**:
  - `Plan`: 126.3s (2.8% of compute)
  - `Perplexity Retrieval`: 34.8s (0.78% of compute) — 84 web queries across 10 sections
  - `Fact Extraction`: **2,404.0s (53.7% of compute)** — 30 extraction LLM calls
  - `Gap Analysis`: **1,012.1s (22.6% of compute)** — 20 gap LLM calls
  - `Section Drafting`: **899.9s (20.1% of compute)** — 10 drafting LLM calls
  - `Cross-Section Synthesis`: 15–30s
  - `Footnote & Document Rendering`: 0.61s

### Key Inefficiencies in Current Implementation:
1. **Model Misallocation (Global Flag Monoculture)**: When `--model gpt-5.4` or `--model claude-opus-4-8` is passed, `resolve_task_model` forces that model on *all* roles. Running atomic JSON extraction and checklist gap comparisons through flagship reasoning models takes 25–45 seconds per call, exhausts output token quotas (e.g. 8,000 tokens/min), and triggers severe 429 exponential backoffs (sleeping 10s–30s repeatedly).
2. **Serial Multi-Round Iteration**: Each section executes `Round 1 (Search -> Extract -> Gap) -> Round 2 (Search -> Extract -> Gap) -> Round 3 (Search -> Extract -> Gap) -> Draft`. All 3 rounds are executed unconditionally even when Round 1 already uncovered 25+ verified facts covering all required fields.
3. **Head-of-Line Concurrency Bottleneck**: All LLM calls (lightweight extraction and heavyweight drafting) share a single `AZURE_SEMAPHORE = asyncio.Semaphore(3)`. A long 45s drafting call blocks two 2-second extraction calls from proceeding.
4. **Redundant Cross-Section Queries**: Overlapping sections (e.g., `company_snapshot`, `financial_overview`, `strategic_operational_profile`) independently plan and fire identical queries (e.g. NVIDIA 10-K, latest quarterly revenue, board composition).
5. **Rigid Stage Barriers**: Stage 3 (Synthesis) sits completely idle for over 9 minutes waiting for the slowest section to finish drafting before starting.

---

## Proposed Behavior

The optimized pipeline introduces a 6-pillar enterprise acceleration architecture that reduces wall-clock execution time to **75–120 seconds** while preserving identical or superior report quality:

```
+---------------------------------------------------------------------------------------------------------+
|                                    OPTIMIZED PIPELINE FLOW (~90s)                                       |
+---------------------------------------------------------------------------------------------------------+
|                                                                                                         |
|  [Stage 1: Spec Parsing (0.01s)]                                                                        |
|    |                                                                                                    |
|    v                                                                                                    |
|  [Stage 2: Parallel Sections with Asymmetric Tiering & Adaptive Depth]                                  |
|    |                                                                                                    |
|    +---> Section 1..10 in parallel:                                                                     |
|    |       ├── Fast Plan (1.5s): Upfront 4-6 multi-faceted queries                                      |
|    |       ├── Batch Perplexity (3-5s): Concurrent search with Cross-Section Query Cache                |
|    |       ├── High-Throughput Extract (2-4s): Tiered Fast Model (mini/flash/groq), Sem: 15             |
|    |       ├── Adaptive Sufficiency Gate (0.01s): Coverage >= 85%? -> SKIP Round 2 & 3!                  |
|    |       └── Premium Draft (12-18s): Tiered Reasoning Model (opus/5.4/sonnet), Sem: 4                 |
|    |                                                                                                    |
|    +---> Incremental Synthesis Pipelining (Starts as soon as quorum of sections finish):                |
|            └── Premium Synthesizer (10-15s): Executive summary & verdict generated in parallel         |
|    |                                                                                                    |
|    v                                                                                                    |
|  [Stage 5: Rendering (0.5s)] -> Markdown + ReportLab PDF with Footnotes                                 |
+---------------------------------------------------------------------------------------------------------+
```

### Pillar 1: Smart Asymmetric Tiering by Default
- The workflow defaults to optimal role-to-model tiering even when a single top-level `--model` is specified:
  - `--model` sets the default for **Narrative Drafting and Synthesis** (the high-stakes cognitive roles).
  - High-volume structural transformations (`extract`, `gap`, `plan`) default to the provider's fastest tier (`fast` / `medium`, e.g., `gpt-5-mini`, `claude-sonnet-4-6`, `gemini-2.5-flash`), unless the user explicitly passes task-specific overrides (`--extract-model`, etc.).
  - Multi-provider fallback: If user provides `GROQ_API_KEY` or `GEMINI_API_KEY`, `extract` and `gap` can optionally federate to ultra-fast LPUs (300+ tokens/sec) at near-zero latency.

### Pillar 2: Adaptive Depth & Rich Upfront Planning
- Instead of planning 2-3 queries and iterating sequentially 3 times, Round 1 plans **4–6 targeted queries** covering all checklist items simultaneously.
- Perplexity retrieves all queries in a single parallel batch (~3.5 seconds).
- **Sufficiency Heuristic**: If Round 1 extracts >= 10 verified facts with all major checklist items covered, the section terminates immediately to drafting, bypassing Rounds 2 & 3.
- If gaps exist, Round 2 executes only the missing queries. Round 3 only fires for edge cases where critical required fields remain unaddressed.

### Pillar 3: Segregated Adaptive Concurrency (Dual Semaphores)
- Replace single `AZURE_SEMAPHORE` with:
  - `FAST_TASK_SEMAPHORE`: Concurrency limit = 12 (configurable via `CONCURRENCY_FAST_TASKS`, default 12).
  - `HEAVY_TASK_SEMAPHORE`: Concurrency limit = 4 (configurable via `CONCURRENCY_HEAVY_TASKS`, default 4).
- Lightweight extraction tasks never block or get blocked by heavy narrative drafting tasks.

### Pillar 4: Cross-Section Query Cache & Ledger Reuse
- Introduce an in-memory session query cache for Perplexity searches: identical or normalized query strings across sections return cached snippets instantly (0ms).
- Cross-section ledger indexing: When drafting a section, the model has access to relevant cross-section facts already in the global ledger.

### Pillar 5: Output Schema & Token Budget Minification
- Extraction prompt minified to produce compact JSON with essential fields (`claim`, `val`, `quote`, `url`).
- Set strict `max_tokens` limits: `plan`: 1,200; `extract`: 1,500; `gap`: 800; `draft`: 4,000; `synth`: 3,500.

### Pillar 6: Pipelined Incremental Synthesis
- Synthesis begins as an async listener. Once sections complete, their key takeaways and evidence metrics are streamed to the synthesizer. Synthesis finishes concurrently with the final section draft.

---

## Expected Performance Benchmarks

| Metric | Baseline (Current) | Phase 1 (Tiering + Dual Semaphores) | Phase 2 (+ Adaptive Depth & Upfront Plan) | Phase 3 (+ Query Cache & Schema Minification) |
| :--- | :--- | :--- | :--- | :--- |
| **Total Wall-Clock Time** | **574.9s (~9.6 min)** | **~210s (~3.5 min)** | **~110s (~1.8 min)** | **~75s - 90s (~1.2 - 1.5 min)** |
| **Extraction Compute** | 2,404s (53.7%) | ~240s | ~120s | ~90s |
| **Gap Compute** | 1,012s (22.6%) | ~120s | ~40s | ~25s |
| **Drafting Compute** | 899.9s (20.1%) | ~800s | ~750s | ~700s |
| **Retrieval Wall-Clock** | 34.8s | ~34.8s | ~18.0s | ~12.0s |
| **API Rate Limit (429) Incidents**| Frequent (1-4/run) | Rare | Zero | Zero |
| **Total Compute Time** | 4,477s | ~1,300s | ~950s | ~820s |
| **Speedup Factor** | Baseline (1.0x) | **2.7x faster** | **5.2x faster** | **6.4x - 7.6x faster** |
| **Analytical Quality / Citations**| 253 Footnotes, 100% | 250+ Footnotes, 100% | 240+ Footnotes, 100% | 250+ Footnotes, 100% |

---

## Implementation Steps

### Phase 1: Architectural Foundation & Concurrency Segregation
1. **Dual Semaphore Implementation**:
   - In `backend/app/workflows/agnostic_research_report/roles.py` and `agnostic_workflow/roles.py`:
     - Implement `FAST_ROLE_SEMAPHORE = asyncio.Semaphore(int(os.environ.get("MAX_CONCURRENCY_FAST", "12")))`.
     - Implement `HEAVY_ROLE_SEMAPHORE = asyncio.Semaphore(int(os.environ.get("MAX_CONCURRENCY_HEAVY", "4")))`.
     - Route `plan`, `extract`, `gap`, `verify` through `FAST_ROLE_SEMAPHORE`.
     - Route `draft`, `synthesize` through `HEAVY_ROLE_SEMAPHORE`.
2. **Smart Asymmetric Tiering in Model Resolution**:
   - Update `resolve_task_model` so that if `--model` is specified (e.g. `gpt-5.4` or `claude-opus-4-8`), it applies to `draft` and `synthesize`, while `extract` and `gap` use the appropriate high-speed tier (`fast`, e.g. `gpt-5-mini` or `claude-sonnet-4-6`) unless explicitly overridden with `--extract-model` / `--gap-model`.
   - Provide an `--all-roles-model` override flag for users who explicitly wish to force a single model across all roles.

### Phase 2: Adaptive Depth & Rich Upfront Planning
3. **Upfront Multi-Faceted Query Generation**:
   - Update `PLAN_SYSTEM` prompt to produce 4–6 comprehensive queries addressing the required fields checklist simultaneously.
4. **Sufficiency Gate in `_process_section`**:
   - After Round 1 extraction, evaluate checklist coverage and claim count. If claims >= 10 and no critical fields are marked missing, skip directly to narrative drafting.
   - Limit deep mode to max 2 rounds (instead of 3) when round 1 yields sufficient facts, while retaining 1 round for fast mode.

### Phase 3: Query Caching, Schema Minification & Distribution
5. **Perplexity In-Memory Session Cache**:
   - In `retrieval.py`, add a normalized query cache to `PerplexitySearchQueue`. Overlapping queries across sections return cached snippets in 0ms.
6. **Token Schema Minification**:
   - Optimize `EXTRACT_SYSTEM` prompt and token limit (`max_tokens: 1500`) to output compact JSON without redundant fields.
7. **Sync & Packaging**:
   - Replicate all optimizations to `agnostic_workflow/`.
   - Rebuild `agnostic_workflow.zip`.
   - Verify zero external imports and pass test suites.

---

## Files to Change

| File | Change | Reason |
| :--- | :--- | :--- |
| `backend/app/workflows/agnostic_research_report/roles.py` | Add dual semaphores (`FAST_ROLE_SEMAPHORE`, `HEAVY_ROLE_SEMAPHORE`), update `resolve_task_model` for smart asymmetric tiering, optimize token limits | Eliminate concurrency bottleneck & rate limit collisions; speed up extraction 10x |
| `backend/app/workflows/agnostic_research_report/orchestrator.py` | Implement sufficiency gate, adaptive depth, rich upfront planning, and cross-section query caching | Eliminate 50% of unnecessary sequential round-trips in Stage 2 |
| `backend/app/workflows/agnostic_research_report/retrieval.py` | Add thread-safe in-memory query cache with normalized string keys | Prevent duplicate Perplexity search calls across sections |
| `backend/app/workflows/agnostic_research_report/cli.py` | Expose `--all-roles-model`, `--fast-concurrency`, `--heavy-concurrency` flags | Give enterprise operators fine-grained runtime control |
| `agnostic_workflow/roles.py` | Synchronize dual semaphores, smart asymmetric tiering, token limits | Maintain exact parity in standalone distribution |
| `agnostic_workflow/orchestrator.py` | Synchronize sufficiency gate, adaptive depth, and query caching | Maintain exact parity in standalone distribution |
| `agnostic_workflow/retrieval.py` | Synchronize in-memory query cache | Maintain exact parity in standalone distribution |
| `agnostic_workflow/run_workflow.py` | Synchronize CLI flags | Maintain exact parity in standalone distribution |
| `backend/test_agnostic_research_report.py` | Add unit tests for dual semaphores, sufficiency gate, and cache | Prevent regressions in core test suite |
| `agnostic_workflow/test_standalone_workflow.py` | Add unit tests verifying standalone speed optimizations | Ensure standalone package passes tests with 0 app imports |

---

## Interfaces

### CLI Interface Additions
```bash
# Standard run with smart asymmetric tiering (draft on gpt-5.4, extract/gap on gpt-5-mini)
python ./run_agnostic_research_report.py "Generate D&O report for NVIDIA" \
  --prompt-file agent-instructions/Web_search_prompt_formatted.md \
  --provider azure --model gpt-5.4 --fallback-model gpt-5-mini --mode deep

# Explicitly force single model on all roles (legacy behavior)
python ./run_agnostic_research_report.py "..." --all-roles-model gpt-5.4

# Enterprise tuning of concurrency pools
python ./run_agnostic_research_report.py "..." --fast-concurrency 16 --heavy-concurrency 5
```

### Environment Variables
- `MAX_CONCURRENCY_FAST`: Concurrency limit for extraction, gap, planning (default: `12`).
- `MAX_CONCURRENCY_HEAVY`: Concurrency limit for narrative drafting and synthesis (default: `4`).
- `ENABLE_QUERY_CACHE`: Enable session-level Perplexity query caching (default: `true`).
- `ADAPTIVE_DEPTH_MIN_CLAIMS`: Minimum claims in Round 1 to trigger early drafting gate (default: `10`).

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| Fast model in `extract` misses nuanced facts | Reduced evidence quality | Fast models (`gpt-5-mini`, `claude-sonnet-4-6`, `gemini-2.5-flash`) excel at structural text-to-JSON extraction; strict JSON validation and verification roles audit output. |
| Early termination terminates prematurely | Section lacks checklist fields | Sufficiency gate requires BOTH claim count threshold AND checklist coverage check; if any critical field is missing, Round 2 triggers automatically. |
| Increased concurrency hits Azure TPM limits | 429 rate limit errors | Dual semaphores isolate fast/heavy tasks; automatic 429 exponential backoff with `parse_retry_delay` safely handles bursts. |
| In-memory query cache returns stale results | Outdated information | Cache is scoped strictly to a single report run (session-level), not persisted across distinct runs. |

---

## Verification

- **Unit tests**:
  - `pytest backend/test_agnostic_research_report.py` (all tests passing).
  - `python agnostic_workflow/test_standalone_workflow.py` (zero external dependencies).
- **Integration tests**:
  - Mock workflow execution with timing verification: confirm `extract_ms` and total wall-clock time decrease significantly.
- **Manual End-to-End Benchmark**:
  - Run full benchmark on standard subject (`Generate D&O report for NVIDIA`) with `--format table`.
  - Compare new telemetry JSON against `Research_Report_generate_d_o_report_for_nvidia_20261105_135248_telemetry.json`:
    - Verify wall-clock time reduction >= 60%.
    - Verify footnote count >= 200.
    - Verify all 10 sections drafted and rendered without errors.

---

## Rollout

1. Present this deep optimization plan to the user for review and formal approval.
2. Upon approval, implement Phase 1 (Dual Semaphores & Asymmetric Tiering).
3. Implement Phase 2 (Adaptive Depth & Rich Upfront Planning).
4. Implement Phase 3 (Query Caching & Schema Minification).
5. Run full test suites and sync `agnostic_workflow/` and `agnostic_workflow.zip`.
6. Document verification benchmarks and update changelog.
