# Implementation Log: Perplexity Retrieval Timeout Extension & Comprehensive Research Extraction

**Created Datetime**: 2026-11-03T15:55:00+05:30  
**Last Updated Datetime**: 2026-11-03T16:10:00+05:30  

## Status

Complete. Timeout extended to 60s, restrictive site filters eliminated, Groq model tier upgraded to `openai/gpt-oss-20b` and `openai/gpt-oss-120b`, and live standard mode executed end-to-end.

## Log Entries

### Step 1: Extended Perplexity Timeout & Natural Query Ingestion
- **Datetime**: 2026-11-03T15:58:00+05:30
- **Files Changed**:
  - `backend/app/workflows/do_risk_report/retrieval.py`
- **Reason**: 15-second timeout caused frequent `httpx.ReadTimeout` errors, and hard boolean `(site:...)` filters caused empty results on paywalled domains.
- **Changes**:
  - Extended `DEFAULT_PERPLEXITY_TIMEOUT = float(os.environ.get("PERPLEXITY_TIMEOUT_SECONDS", "60.0"))`.
  - Removed restrictive boolean `(site:domain1 OR site:domain2)` query string concatenation; transitioned domain guidance to system prompt instructions.
  - Refactored `_execute_live_search` to deliver full grounded research summaries (up to 1,500 chars) as primary results, plus structured individual cited sources.
  - Increased `ResultCompactor.clean_snippet` default limit from 800 to 1,500 characters.
- **Tests Added/Updated**:
  - `test_clean_snippet_length_and_formatting`
  - `test_perplexity_queue_search_and_batch`
- **Result**: Passed. Unit tests green, and standalone test extracted 6 verified analyst consensus claims.

### Step 2: Groq Model Tier Upgrade & OTPM Rate-Limit Fix
- **Datetime**: 2026-11-03T16:02:00+05:30
- **Files Changed**:
  - `backend/app/workflows/do_risk_report/roles.py`
- **Reason**: Live run revealed that `qwen/qwen3.8-27b` enforces a strict 1,000 Output Tokens Per Minute (OTPM) limit on the user's Groq organization, causing 429 errors when generating comprehensive multi-paragraph section narratives.
- **Changes**:
  - Added `import asyncio` to `roles.py`.
  - Upgraded fast and medium tiers to `openai/gpt-oss-20b` (`GROQ_FAST_TIER = "openai/gpt-oss-20b"` and `GROQ_MEDIUM_TIER = "openai/gpt-oss-20b"`), which has no 1,000 OTPM ceiling.
  - Kept reasoning tier as `openai/gpt-oss-120b`.
  - Added safe exponential backoff retry loop with exception handling for live Groq calls.
- **Tests Added/Updated**:
  - `test_roles_with_timings`
  - `test_run_role_execution`
- **Result**: Passed. 0 Groq rate limit errors during live parallel drafting.

### Step 3: End-to-End Live Standard Execution
- **Datetime**: 2026-11-03T16:08:00+05:30
- **Command Run**:
  ```powershell
  $env:PYTHONPATH="backend"; backend\venv\Scripts\python.exe backend\run_do_risk_report.py AAPL --mode standard --format tree
  ```
- **Result**:
  - Wall-clock time: 376.12s (6.2 minutes, down from 8.1 minutes).
  - Compute time: 2,342.10s (6.23x concurrency speedup).
  - Generated: `DO_Risk_Report_AAPL_54e1f291.md` (15.6 KB), `DO_Risk_Report_AAPL_54e1f291.docx` (39.6 KB), `DO_Risk_Report_AAPL_54e1f291.pdf` (13.8 KB, 5 pages).
