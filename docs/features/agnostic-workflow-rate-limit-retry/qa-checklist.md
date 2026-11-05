# QA Checklist: Agnostic Workflow Azure Rate Limit (HTTP 429) Retry & Non-Skipping Recovery

## Datetime
`2026-11-05T13:42:30+05:30`

## Pre-Release QA Checks

- [x] **Rate Limit Parsing Resilience**:
  - `parse_retry_delay` correctly parses `"Please wait X seconds before retrying"`.
  - `parse_retry_delay` handles floating numbers (e.g. `"retry after 12.5 seconds"`).
  - Handles errors with no explicit seconds and applies exponential fallback.
- [x] **Model Sequence Failover & Cooldown**:
  - `run_role` fails over to fallback model if configured and rate-limited.
  - `run_role` runs up to 5 outer rounds (`AZURE_MAX_RETRY_ROUNDS`) with live progress countdowns.
- [x] **Zero Section Skipping**:
  - `_process_section` retries drafting up to 4 times (`DRAFT_MAX_RETRIES`) with incremental backoff.
  - Section is never prematurely populated with `- Section drafting unavailable due to upstream error:` on the first transient 429 error.
  - Stage 3 cross-section synthesis retries up to 4 times (`SYNTH_MAX_RETRIES`).
- [x] **Scope Enforcement**:
  - Code changes made **only** in `backend/app/workflows/agnostic_research_report/`.
- [x] **Unit Testing**:
  - All 20 tests in `backend/test_agnostic_research_report.py` pass.
- [x] **Documentation Integrity**:
  - Feature plan, implementation log, verification report, and QA checklist completed with datetimes.
  - Architecture decisions recorded in `docs/decisions/agnostic-workflow-rate-limit-retry/decisions.md`.
