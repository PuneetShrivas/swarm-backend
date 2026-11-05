# QA Checklist: Enterprise Workflow Speed Optimization

**Created**: 2026-11-05T19:20:00+05:30  
**Updated**: 2026-11-05T22:12:00+05:30  
**Feature**: `enterprise-workflow-speed-optimization`  
**Status**: Completed & Verified

---

## Pre-Implementation Quality Gates
- [x] Comprehensive telemetry audit performed on baseline NVIDIA D&O run (`574.9s` wall-clock, `4,477s` compute).
- [x] Root causes identified: 76.3% of compute spent in `extract` and `gap` running on reasoning tier; global semaphore serialized to 3; fixed 3-round iteration loop.
- [x] Telemetry rework audit performed on run `20261105_210115` revealing 2,952.7s spent in Round 2 rework and gap checking.
- [x] Strict adherence to AGENTS.md: Feature plan created from `docs/templates/feature-plan.md`.
- [x] User authorization received to implement Pillars 3 and 4, followed by Strategy 1 and Strategy 4.

---

## Implementation Quality Gates
- [x] **Pillar 4: Session-Level In-Memory Perplexity Query Cache**:
  - In-memory normalized query cache implemented in `backend/app/workflows/agnostic_research_report/retrieval.py`.
  - Symmetrically implemented in `agnostic_workflow/retrieval.py`.
  - Cache hits return instant results with 0ms network latency.
  - Thread-safe and async-safe via `asyncio.Lock`.
  - Added `clear_session_cache()` and `get_cache_stats()`.
- [x] **Pillar 3: Adaptive Depth & Upfront Batch Planning**:
  - `PLAN_SYSTEM` prompt updated to formulate 4 to 6 comprehensive search queries covering all checklist fields simultaneously in both backend and standalone roles.
  - Initial planning prompt in `_process_section` expanded to request 4–6 queries addressing all checklist fields.
- [x] **Strategy 1: Direct Single-Pass Execution (Rework Elimination)**:
  - If Round 1 yields $\ge 12$ claims (`min_adaptive_claims`, default 12, configurable via `ADAPTIVE_DEPTH_MIN_CLAIMS`), bypass Gap Analysis entirely (`gap_ms = 0.0`) and fast-track directly to Narrative Drafting in 1 round.
  - Symmetrically implemented in `backend/app/workflows/agnostic_research_report/orchestrator.py` and `agnostic_workflow/orchestrator.py`.
- [x] **Strategy 4: Strict Cap on Round 2 Queries & Snippets**:
  - `GAP_SYSTEM` prompt updated to instruct generating at most 2 targeted follow-up queries.
  - Round 2 query list strictly sliced with `[:2]`.
  - Round 2 extraction input capped at 6 snippets (instead of 10) to prevent token rate-limit explosions.
  - Symmetrically implemented in `roles.py` and `orchestrator.py`.
- [x] **Parity & Packaging**:
  - `backend/app/workflows/agnostic_research_report/` and `agnostic_workflow/` are 100% synchronized.
  - `agnostic_workflow/` contains zero external imports from `backend/app`.
  - `agnostic_workflow.zip` rebuilt and verified.
  - Both CLI entrypoints (`backend/run_agnostic_research_report.py` and `agnostic_workflow/run_workflow.py`) verified functional with identical argument parsing.

---

## Post-Implementation Quality Gates
- [x] All unit tests pass in `backend/test_agnostic_research_report.py` (28/28 tests OK).
- [x] All standalone tests pass in `agnostic_workflow/test_standalone_workflow.py` (18/18 tests OK).
- [x] Zero regressions across existing features and fallback models.
- [x] Documentation updated in `implementation.md`, `verification.md`, and `qa-checklist.md`.
