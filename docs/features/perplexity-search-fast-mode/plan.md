# Feature: Switch Perplexity Search API Everywhere to Fast Mode

## Datetime
`2026-11-05T13:10:30+05:30`

## Status
In progress

## Goal
Switch all Perplexity API calls across the entire repository (Search API endpoint `POST https://api.perplexity.ai/search` and chat completions endpoints) to **Fast Search mode** (`search_type: "fast"`), leveraging Perplexity's low-latency, cost-optimized Photon retrieval engine across all workflows, agents, and standalone packages.

## Scope
- In scope:
  - Add `"search_type": "fast"` parameter to `search_via_perplexity_search_api()` and `async_search_via_perplexity_search_api()` in `backend/app/agents/researcher/tools.py`.
  - Add `"search_type": "fast"` parameter to `async_search_via_perplexity_search_api()` in `agnostic_workflow/retrieval.py`.
  - Add `"search_type": "fast"` in `search_via_perplexity()` in `backend/app/agents/researcher/tools.py`.
  - Add `"search_type": "fast"` in `backend/app/main.py` and `backend/app/workflows/engine.py` chat completion requests.
  - Expose default configuration `PERPLEXITY_SEARCH_TYPE = "fast"` in `agnostic_workflow/config.py` and `agnostic_workflow/.env.example`.
  - Update unit test assertions in `backend/test_do_risk_report.py`, `agnostic_workflow/test_standalone_workflow.py`, and `backend/test_agnostic_research_report.py` to verify that `"search_type": "fast"` is always transmitted.
  - Document architectural decisions in `docs/decisions/perplexity-search-fast-mode/decisions.md`.
  - Update `docs/features/perplexity-search-fast-mode/` lifecycle docs (`implementation.md`, `verification.md`, `qa-checklist.md`).
  - Update `CHANGELOG.md`.
- Out of scope:
  - Changing non-Perplexity LLM provider parameters.

## Current behavior
Perplexity Search API requests omit the `search_type` parameter (or pass only `query`, `max_results`, `search_context_size`), which defaults to standard comprehensive web search depth with higher latency and higher cost ($5.00/1k vs $1.00/1k).

## Proposed behavior
Every Perplexity API request in the codebase explicitly transmits `"search_type": "fast"` (or defaults to `"fast"` via `os.environ.get("PERPLEXITY_SEARCH_TYPE", "fast")`), ensuring that all research steps, agent tool calls, and standalone workflow queries run on Perplexity's low-latency Fast Search tier.

## Implementation steps
1. Update `backend/app/agents/researcher/tools.py` (`search_via_perplexity_search_api`, `async_search_via_perplexity_search_api`, `search_via_perplexity`) to include `search_type: "fast"`.
2. Update `agnostic_workflow/retrieval.py` (`async_search_via_perplexity_search_api`) to include `search_type: "fast"`.
3. Update `agnostic_workflow/config.py` and `agnostic_workflow/.env.example` with `PERPLEXITY_SEARCH_TYPE = "fast"`.
4. Update `backend/app/main.py` and `backend/app/workflows/engine.py` Perplexity calls with `"search_type": "fast"`.
5. Update unit tests in `backend/test_do_risk_report.py` and `agnostic_workflow/test_standalone_workflow.py` to assert payload contains `"search_type": "fast"`.
6. Run full test suites (`backend/test_do_risk_report.py`, `backend/test_agnostic_research_report.py`, `agnostic_workflow/test_standalone_workflow.py`).
7. Update documentation (`implementation.md`, `verification.md`, `qa-checklist.md`, `decisions.md`, `CHANGELOG.md`).
8. Commit and push.

## Files to change / create
| File | Change | Reason |
|---|---|---|
| `backend/app/agents/researcher/tools.py` | Modify | Transmit `"search_type": "fast"` on all Search API & completions calls |
| `agnostic_workflow/retrieval.py` | Modify | Transmit `"search_type": "fast"` on standalone Search API calls |
| `agnostic_workflow/config.py` | Modify | Expose `PERPLEXITY_SEARCH_TYPE = "fast"` |
| `agnostic_workflow/.env.example` | Modify | Add `PERPLEXITY_SEARCH_TYPE="fast"` |
| `backend/app/main.py` | Modify | Add `"search_type": "fast"` to Sonar chat completion calls |
| `backend/app/workflows/engine.py` | Modify | Add `"search_type": "fast"` to Sonar chat completion calls |
| `backend/test_do_risk_report.py` | Modify | Assert `"search_type": "fast"` in payload tests |
| `agnostic_workflow/test_standalone_workflow.py` | Modify | Assert `"search_type": "fast"` in standalone payload tests |
| `docs/decisions/perplexity-search-fast-mode/decisions.md` | Create | Architecture decisions on Fast Search tier |
| `docs/features/perplexity-search-fast-mode/*` | Create | Feature lifecycle documentation |
| `CHANGELOG.md` | Modify | Release notes |

## Verification
- Run `backend/test_do_risk_report.py`
- Run `agnostic_workflow/test_standalone_workflow.py`
- Run `backend/test_agnostic_research_report.py`
- Verify payload inspection in mock tests.
