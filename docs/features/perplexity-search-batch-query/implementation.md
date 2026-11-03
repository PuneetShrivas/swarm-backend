# Implementation: Batch Search Query Method for Perplexity Search API

**Datetime**: 2026-11-03T17:11:30+05:30  
**Feature Slug**: `perplexity-search-batch-query`

---

## 1. Summary of Changes
Updated `search_via_perplexity_search_api` and `async_search_via_perplexity_search_api` in `backend/app/agents/researcher/tools.py` to support multi-query batch searching by sending a list of query strings (`query: List[str]`) directly in a single HTTP request to `POST https://api.perplexity.ai/search`. Upgraded `PerplexitySearchQueue.batch_search` in `backend/app/workflows/do_risk_report/retrieval.py` to consolidate uncached section queries into single multi-query calls.

---

## 2. Changes Made

### `backend/app/agents/researcher/tools.py`
- Upgraded `search_via_perplexity_search_api` and `async_search_via_perplexity_search_api`:
  - Parameter signature: `query: Union[str, List[str]]`.
  - Normalizes string and list inputs, cleans whitespace, and caps batch size to 50 Query Units per request.
  - Passes JSON array directly to Perplexity's `"query"` field (`payload = {"query": query_payload, ...}`).
  - Formats and aggregates returned multi-query results with titles, URLs, high-context snippets, dates, and domains.

### `backend/app/workflows/do_risk_report/retrieval.py`
- Updated `PerplexitySearchQueue._get_cache_key`:
  - Handles tuple representation of query lists (`query_repr = tuple(query) if isinstance(query, (list, tuple)) else query`).
- Updated `PerplexitySearchQueue.batch_search`:
  - Checks individual cache entries first for all incoming queries.
  - Consolidates all uncached queries in the section into a single multi-query batch request sent to `async_search_via_perplexity_search_api`.
  - Populates cache for both the consolidated batch and individual query keys.
  - Reduces live HTTP calls per section from 4–5 calls down to 1 call.

### `backend/test_do_risk_report.py`
- Added `test_search_via_perplexity_search_api_batch_query_list`:
  - Verifies that passing a list of query strings correctly sets `payload["query"]` to the query list.
- Added `test_async_search_via_perplexity_search_api_batch_query_list`:
  - Verifies async invocation with multi-query list and mock response parsing.
