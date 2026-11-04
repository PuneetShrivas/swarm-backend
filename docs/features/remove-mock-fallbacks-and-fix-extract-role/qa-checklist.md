# QA Checklist: Remove Mock Fallbacks and Fix Extract Role

## Datetime
`2026-11-04T15:25:00+05:30`

- [x] `edgar.py` does not return mock Cupertino / Apple data when SEC requests fail.
- [x] `edgar.py` does not generate synthetic MD5 hashes for unknown tickers.
- [x] `retrieval.py` raises `RuntimeError` if `PERPLEXITY_API_KEY` is missing in live report generation mode.
- [x] `roles.py` aggregates all text blocks in `_execute_azure_chat`.
- [x] `roles.py` strips `<thinking>` tags in `_extract_json_from_llm_response`.
- [x] `roles.py` normalizes raw list outputs into `{"items": [...]}` for the extract role.
- [x] `roles.py` logs explicit parse failure messages and retries rather than silently breaking with an empty error.
- [x] `roles.py` increases `extract` `max_tokens` to 4000 to prevent truncated JSON.
- [x] `orchestrator.py` wraps `extract` and `gap` calls in defensive try-except handlers.
- [x] All unit tests pass in `backend/test_do_risk_report.py`.
- [x] Python syntax passes `py_compile`.
- [x] CHANGELOG.md is updated.
