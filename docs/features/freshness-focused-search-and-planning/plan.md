# Feature Plan: Freshness-Focused Search and Planning in Agnostic Research Workflow

**Created**: 2026-11-05T22:15:00+05:30  
**Status**: In progress  
**Feature Slug**: `freshness-focused-search-and-planning`

---

## 1. Goal

Heavily focus search query planning and retrieval execution in the agnostic research workflow on acquiring the latest and freshest data possible. Ensure all search queries, gap evaluations, extraction filters, and search agent prompts prioritize contemporary information (breaking news, recent quarters/years, latest regulatory actions, recent benchmarks, latest financial filings) over stale historical web data.

---

## 2. Scope

### In Scope
1. **Planning Role (`PLAN_SYSTEM` in `roles.py`)**:
   - Instruct the query planner that extreme temporal freshness is of utmost importance.
   - Enforce embedding temporal anchors and freshness signals directly into query strings (e.g. current year "2025"/"2026", "latest", "recent developments", "Q3/Q4 2025", "breaking", "current roadmap").
   - Set output query schema default `"recency": "month"` or `"week"` to trigger upstream date filtering.
2. **Gap Analysis Role (`GAP_SYSTEM` in `roles.py`)**:
   - Direct follow-up queries strictly toward the freshest available data points and recent updates rather than broad historical searches.
   - Default recency to `"month"` / `"week"`.
3. **Extraction Role (`EXTRACT_SYSTEM` in `roles.py`)**:
   - Add explicit freshness resolution priority: favor recent data points when sources report conflicting figures over time, record exact dates (`as_of` / `published`), and penalize outdated data.
4. **Dynamic Section Planning Input (`orchestrator.py`)**:
   - Update `plan_input` and `gap_prompt` to inject strict freshness guidelines into runtime LLM context.
   - Update planner fallback query to include latest temporal markers (`f"{subject} {section.title} latest developments 2026"`).
5. **Retrieval Engine (`retrieval.py` in backend & standalone)**:
   - Wire `recency` directly into Perplexity Search API payload as `search_recency_filter` (supporting `"month"`, `"week"`, `"year"`, `"day"`).
   - Default to `"month"` for queries without explicit recency to guarantee recent search index results.
6. **Research Agent System Instructions (`backend/app/agents/researcher/prompt.md`)**:
   - Update research agent prompt to elevate extreme data freshness and contemporary accuracy to a top-tier operating constraint.
7. **Symmetry & Standalone Parity**:
   - Synchronize identically between `backend/app/workflows/agnostic_research_report/` and `agnostic_workflow/`.
   - Repack `agnostic_workflow.zip`.
   - Update unit test suites in `backend/test_agnostic_research_report.py` and `agnostic_workflow/test_standalone_workflow.py`.

### Out of Scope
- Modifying UI components or CSS diagrams.
- Changing markdown report styling or PDF canvas layout.

---

## 3. Current Behavior

- `PLAN_SYSTEM` formulates 4–6 queries without strict recency requirements, often omitting temporal anchors (e.g. "Solid State Batteries market size" instead of "Solid State Batteries market size 2025 2026 latest").
- Default `"recency"` key in JSON is `"year"`, and in `retrieval.py` the `recency` argument was not passed into the `https://api.perplexity.ai/search` request payload, relying solely on Perplexity's default unconstrained web crawl.
- `EXTRACT_SYSTEM` lacks explicit instructions on handling older vs. newer conflicting statistics.

---

## 4. Proposed Behavior

1. **Planner (`roles.py` & `orchestrator.py`)**:
   - `PLAN_SYSTEM` mandates that every query formulated includes temporal freshness anchors (e.g., current year, recent quarters, "latest developments", "current status", "2025 2026").
   - Explicitly instructs: `FRESHNESS IS PARAMOUNT: Stale, historical data from prior years must be actively avoided unless explicitly analyzing historical trends.`
   - Planner sets `"recency": "month"` or `"week"` by default.
2. **Gap Role (`GAP_SYSTEM`)**:
   - Directs the LLM to formulate follow-up queries with explicit freshness cues to fill remaining evidentiary gaps with the most recent reports and announcements.
3. **Extract Role (`EXTRACT_SYSTEM`)**:
   - Adds rule: `5. RECENCY & TEMPORAL INTEGRITY: Prioritize the freshest, most recent facts and figures. Record explicit 'as_of' and 'published' timestamps.`
4. **Perplexity Retrieval Queue (`retrieval.py`)**:
   - Passes `search_recency_filter` in the Perplexity search payload (or maps `"month"`, `"week"`, `"day"`, `"year"`).
   - In fallback / live calls, passes `search_recency_filter` so Perplexity natively filters index for fresh content.
5. **Research Agent (`prompt.md`)**:
   - Emphasizes real-time, latest verified data, and deprecating stale sources.

---

## 5. Files to Change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/agnostic_research_report/roles.py` | Update `PLAN_SYSTEM`, `GAP_SYSTEM`, `EXTRACT_SYSTEM` | Enforce extreme data freshness in prompts |
| `agnostic_workflow/roles.py` | Symmetrical update to `PLAN_SYSTEM`, `GAP_SYSTEM`, `EXTRACT_SYSTEM` | Standalone parity |
| `backend/app/workflows/agnostic_research_report/orchestrator.py` | Update `plan_input`, `gap_prompt`, fallback query | Enforce freshness context in section execution |
| `agnostic_workflow/orchestrator.py` | Symmetrical update to `orchestrator.py` | Standalone parity |
| `backend/app/workflows/agnostic_research_report/retrieval.py` | Wire `search_recency_filter` to Perplexity API call | Enable native search index freshness filtering |
| `agnostic_workflow/retrieval.py` | Wire `search_recency_filter` to Perplexity API call | Standalone parity |
| `backend/app/agents/researcher/prompt.md` | Update system prompt for Research Agent | Emphasize extreme temporal recency |
| `backend/test_agnostic_research_report.py` | Add unit tests for freshness prompts & recency filtering | Test coverage |
| `agnostic_workflow/test_standalone_workflow.py` | Add unit tests for standalone freshness prompts | Standalone test coverage |
| `agnostic_workflow.zip` | Rebuild zip archive | Keep standalone package distribution current |

---

## 6. Verification

- Run backend tests: `.\backend\venv\Scripts\python.exe -m unittest backend/test_agnostic_research_report.py`
- Run standalone tests: `.\backend\venv\Scripts\python.exe agnostic_workflow/test_standalone_workflow.py`
- Verify both runner scripts work with `--help`.
