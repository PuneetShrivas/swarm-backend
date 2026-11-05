# Implementation Spec: Freshness-Focused Search and Planning in Agnostic Research Workflow

**Created**: 2026-11-05T22:15:00+05:30  
**Updated**: 2026-11-05T22:23:00+05:30  
**Feature**: `freshness-focused-search-and-planning`  
**Status**: Completed & Verified

---

## 1. Executive Summary

This feature updates the planning role (`plan`), gap checking role (`gap`), extraction role (`extract`), and the research/search agent to heavily focus on acquiring the latest and freshest data available.

### Core Changes
1. **Prompt Updates (`roles.py`)**:
   - `PLAN_SYSTEM`: Mandates embedding explicit temporal markers (e.g., current year "2025"/"2026", "latest", "recent developments", "Q3/Q4 2025") into query strings and setting `"recency": "month"` (or `"week"`) in output JSON.
   - `GAP_SYSTEM`: Directs follow-up queries strictly toward the freshest data points and latest disclosures to close evidence gaps.
   - `EXTRACT_SYSTEM`: Enforces a new rule prioritizing recent information, capturing precise `as_of` / `published` dates, and favoring recent updates when data evolves.
2. **Orchestrator Injections (`orchestrator.py`)**:
   - Updates `plan_input` with explicit instructions prioritizing freshness and recent developments.
   - Updates `gap_prompt` to emphasize fresh data.
   - Updates query planner fallback to include `"latest developments 2026"`.
3. **Retrieval Integration (`retrieval.py` and `tools.py`)**:
   - Extended `async_search_via_perplexity_search_api` to accept `search_recency_filter` and `search_domain_filter`.
   - Wired `search_recency_filter` into Perplexity Search API payload (`"month"`, `"week"`, `"day"`, `"year"`), defaulting to `"month"` for maximum freshness.
4. **Research Agent System Instructions (`prompt.md`)**:
   - Elevated real-time timeliness, recent filing analysis, and contemporary truth to top-level directives.

---

## 2. Execution Log

### 2026-11-05T22:23:00+05:30 — Implementation Step 1: Freshness Directives Across Roles, Retrieval, and Agent Prompts
- **Files Changed**:
  - `backend/app/workflows/agnostic_research_report/roles.py`
  - `agnostic_workflow/roles.py`
  - `backend/app/workflows/agnostic_research_report/orchestrator.py`
  - `agnostic_workflow/orchestrator.py`
  - `backend/app/workflows/agnostic_research_report/retrieval.py`
  - `agnostic_workflow/retrieval.py`
  - `backend/app/agents/researcher/tools.py`
  - `backend/app/agents/researcher/prompt.md`
  - `backend/test_agnostic_research_report.py`
  - `agnostic_workflow/test_standalone_workflow.py`
  - `agnostic_workflow.zip`
- **Reason**:
  - Addressed user requirement: "update the prompt of the search role and whatever role is planning what queries to be sent in the agnostic workflow files to search to heavily focus on bringing as latest data as possible, being extremely fresh in data. This is of utmost importance."
- **Diagnostics & Resolutions Encountered**:
  - *Diagnosis*: `agnostic_workflow/orchestrator.py` had `except Exception:` while backend had `except Exception as e:`.
  - *Resolution*: Adapted replacement script to match each file's specific exception syntax.
- **Tests Added/Updated**:
  - `TestAgnosticFreshnessSearchAndPlanning.test_plan_system_prompt_freshness_directives`
  - `TestAgnosticFreshnessSearchAndPlanning.test_gap_system_prompt_freshness_directives`
  - `TestAgnosticFreshnessSearchAndPlanning.test_extract_system_prompt_temporal_integrity`
  - `TestAgnosticFreshnessSearchAndPlanning.test_researcher_agent_prompt_freshness`
  - `TestAgnosticFreshnessSearchAndPlanning.test_perplexity_api_search_recency_filter_parameter`
  - `TestStandaloneAgnosticWorkflow.test_18_freshness_search_and_planning`
- **Commands Run**:
  - `.\backend\venv\Scripts\python.exe -m unittest backend/test_agnostic_research_report.py` -> Passed (33 tests OK, 2.157s).
  - `.\backend\venv\Scripts\python.exe agnostic_workflow/test_standalone_workflow.py` -> Passed (19 tests OK, 1.487s, 0 external app imports).
  - `.\backend\venv\Scripts\python.exe backend/run_agnostic_research_report.py --help` -> OK.
  - `.\backend\venv\Scripts\python.exe agnostic_workflow/run_workflow.py --help` -> OK.
  - Repacked `agnostic_workflow.zip` (53,467 bytes).
- **Result**: Step 1 complete with 100% test pass and full symmetry.
