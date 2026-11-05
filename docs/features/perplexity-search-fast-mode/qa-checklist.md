# QA Checklist: Switch Perplexity Search API Everywhere to Fast Mode

## Datetime
`2026-11-05T13:15:55+05:30`

- [x] **Fast search parameter on Search API**: `backend/app/agents/researcher/tools.py` transmits `"search_type": "fast"` on `search_via_perplexity_search_api()` and `async_search_via_perplexity_search_api()`.
- [x] **Fast search parameter in standalone workflow**: `agnostic_workflow/retrieval.py` transmits `"search_type": "fast"` on `async_search_via_perplexity_search_api()`.
- [x] **Config discovery**: `agnostic_workflow/config.py` and `agnostic_workflow/.env.example` expose `PERPLEXITY_SEARCH_TYPE = "fast"`.
- [x] **Fast search parameter on Chat Completions**: `backend/app/agents/researcher/tools.py` (`search_via_perplexity`), `backend/app/main.py` (both Sonar endpoints), and `backend/app/workflows/engine.py` pass `"search_type": "fast"`.
- [x] **Unit test assertions**:
  - `backend/test_do_risk_report.py`: `test_search_via_perplexity_search_api_batch_query_list` and `test_async_search_via_perplexity_search_api_batch_query_list` verify `payload["search_type"] == "fast"`.
  - `agnostic_workflow/test_standalone_workflow.py`: `test_05b_perplexity_fast_search_payload` verifies `payload["search_type"] == "fast"`.
- [x] **Zero regressions**: All backend and standalone test suites pass.
- [x] **Feature documentation**: Lifecycle docs in `docs/features/perplexity-search-fast-mode/` and decisions in `docs/decisions/perplexity-search-fast-mode/decisions.md`.
- [x] **Changelog updated**: Entry added to `CHANGELOG.md`.
