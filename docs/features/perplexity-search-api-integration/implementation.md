# Implementation: Perplexity Search API Integration for D&O Workflow

**Datetime**: 2026-11-03T16:50:30+05:30  
**Feature Slug**: `perplexity-search-api-integration`

---

## 1. Summary of Changes
Replaced the generative `chat/completions` endpoint on Perplexity with the dedicated raw Search API endpoint (`POST https://api.perplexity.ai/search`) for all web research in the D&O Public Risk Underwriting system.

---

## 2. Changes Made

### `backend/app/agents/researcher/tools.py`
- Implemented `search_via_perplexity_search_api()`:
  - Connects to `POST https://api.perplexity.ai/search`.
  - Sends payload `{"query": query, "max_results": max_results, "search_context_size": "high"}`.
  - Returns structured results with `title`, `url`, `snippet`, `date`, and `domain`.
- Implemented `async_search_via_perplexity_search_api()`:
  - Asynchronous implementation with 4-attempt exponential backoff retry.
  - Handles rate limits (HTTP 429) and transient network disconnects gracefully.
  - Adds polite 0.2s pause between calls.

### `backend/app/workflows/do_risk_report/retrieval.py`
- Imported `async_search_via_perplexity_search_api`.
- Updated `PerplexitySearchQueue._execute_live_search()` to use the Search API with `search_context_size="high"`.
- Eliminated all synthetic mock fallback in live mode (`not is_mock`).
- Separated live vs. mock cache keys with prefix hashing.

### `backend/app/workflows/do_risk_report/validator.py`
- Added section preservation guard to prevent LLM summarization from dropping sections or truncating the multi-page report.

### `backend/app/workflows/do_risk_report/roles.py`
- Expanded `max_tokens` across roles (`extract`: 2500, `draft`: 3000, `synthesize`: 3000, `repair`: 3500) to allow full, comprehensive institutional-grade reporting.

### `backend/test_do_risk_report.py`
- Added `TestPerplexitySearchAPI` test suite covering synchronous and asynchronous Search API functions.
- Verified mock handling, schema parsing, and domain extraction.
