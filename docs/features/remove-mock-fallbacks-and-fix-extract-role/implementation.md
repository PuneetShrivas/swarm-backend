# Implementation Log: Remove Mock Fallbacks and Fix Extract Role

## Datetime
`2026-11-04T15:25:00+05:30`

### Step 1: Remove Mock Data Fallbacks in `edgar.py`
- **Files changed**: `backend/app/workflows/do_risk_report/edgar.py`
- **Reason**: Ensure that live report generation never injects fake Apple Cupertino addresses, Apple XBRL financials ($383B revenue), or fake synthetic CIK hashes.
- **Tests added/updated**: `TestAccuracyAndPipelineFixes` in `backend/test_do_risk_report.py`.
- **Status**: Completed (2026-11-04T15:26:00+05:30).

### Step 2: Remove Mock Data Fallbacks in `retrieval.py`
- **Files changed**: `backend/app/workflows/do_risk_report/retrieval.py`
- **Reason**: Prohibit silent synthetic search results when `PERPLEXITY_API_KEY` is missing in live mode; require valid configuration and return authentic results only.
- **Tests added/updated**: `TestAccuracyAndPipelineFixes` in `backend/test_do_risk_report.py`.
- **Status**: Completed (2026-11-04T15:27:00+05:30).

### Step 3: Fix Azure Multi-Block Aggregation, Thinking Block Stripping, and Retry Handling in `roles.py`
- **Files changed**: `backend/app/workflows/do_risk_report/roles.py`
- **Reason**: Resolve root cause of `RuntimeError: Role 'extract' Azure Foundry execution failed across models ['claude-sonnet-4-6'] after 5 retry rounds:` with empty error string.
- **Tests added/updated**: `test_extract_json_thinking_blocks_and_bare_arrays` and `test_azure_parse_error_retry_and_descriptive_message` in `backend/test_do_risk_report.py`.
- **Status**: Completed (2026-11-04T15:32:00+05:30).

### Step 4: Add Defensive Orchestrator Wrapping in `orchestrator.py`
- **Files changed**: `backend/app/workflows/do_risk_report/orchestrator.py`
- **Reason**: Protect the pipeline from crashing if an individual search extraction or gap check encounters an unhandled LLM glitch.
- **Tests added/updated**: `TestAccuracyAndPipelineFixes` in `backend/test_do_risk_report.py`.
- **Status**: Completed (2026-11-04T15:33:00+05:30).
