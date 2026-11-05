# QA Checklist: Freshness-Focused Search and Planning

**Created**: 2026-11-05T22:15:00+05:30  
**Updated**: 2026-11-05T22:24:00+05:30  
**Feature**: `freshness-focused-search-and-planning`  
**Status**: Completed & Verified

---

## Pre-Implementation Quality Gates
- [x] Feature plan created adhering to `AGENTS.md` and `docs/development-process.md`.
- [x] Identified all prompt locations: `roles.py`, `orchestrator.py`, `prompt.md`.
- [x] Identified API payload enhancement for `search_recency_filter` in `retrieval.py` and `tools.py`.

---

## Implementation Quality Gates
- [x] `PLAN_SYSTEM` updated in `backend` and `agnostic_workflow` with strict freshness rules and temporal query anchors.
- [x] `GAP_SYSTEM` updated with freshness priority for gap resolution.
- [x] `EXTRACT_SYSTEM` updated with recency priority rule.
- [x] `orchestrator.py` updated with freshness context in `plan_input`, `gap_prompt`, and fallback query.
- [x] `retrieval.py` passes `search_recency_filter` to Perplexity API endpoint in both packages.
- [x] `backend/app/agents/researcher/prompt.md` updated with freshness directives.
- [x] `backend/test_agnostic_research_report.py` updated with new unit tests (33 tests pass).
- [x] `agnostic_workflow/test_standalone_workflow.py` updated with new standalone unit tests (19 tests pass).
- [x] Symmetrical parity verified (zero logic differences).
- [x] `agnostic_workflow.zip` repacked (53,467 bytes).

---

## Post-Implementation Quality Gates
- [x] All backend tests pass.
- [x] All standalone tests pass.
- [x] Documentation updated (`implementation.md`, `verification.md`, `qa-checklist.md`, `CHANGELOG.md`).
- [x] Changes committed and pushed.
