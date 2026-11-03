# Feature Plan: Batch Query Method for Perplexity Search API

**Datetime**: 2026-11-03T17:07:00+05:30  
**Feature Slug**: `perplexity-search-batch-query`  
**Status**: Approved / In progress

---

## 1. Goal
Upgrade `search_via_perplexity_search_api` and `async_search_via_perplexity_search_api` in `backend/app/agents/researcher/tools.py` to support multi-query batch searching by sending a list of query strings (`query: List[str]`) directly in a single HTTP request to `POST https://api.perplexity.ai/search`, leveraging Perplexity's capacity of up to 50 Query Units (QU) per second. Update `PerplexitySearchQueue.batch_search` in `backend/app/workflows/do_risk_report/retrieval.py` to batch section queries into single multi-query calls, reducing network roundtrips by ~75% and minimizing overall pipeline latency and token overhead.

---

## 2. Scope

### In Scope
- Support `Union[str, List[str]]` in `search_via_perplexity_search_api()` and `async_search_via_perplexity_search_api()`.
- Update `PerplexitySearchQueue.batch_search()` and `search()` in `backend/app/workflows/do_risk_report/retrieval.py` to pass the entire query list in a single batch request.
- Update cache reading/writing to handle both multi-query batch results and individual query entries.
- Add unit tests for list-of-strings query payloads.
- Verify end-to-end speedup and output fidelity on target ticker (`NVDA`).

### Out of Scope
- Modifying offline/mock result generation logic.
- Altering Groq LLM extraction or drafting schemas.

---

## 3. Current Behavior vs. Proposed Behavior

### Current Behavior
- `search_via_perplexity_search_api` accepts a single string `query: str`.
- When a section has 4–5 static queries, `PerplexitySearchQueue.batch_search()` fires 4–5 individual HTTP calls via `asyncio.gather(*[self.search(q) for q in queries])`.
- Across 11 sections, this generated 40–55 separate HTTP roundtrips, increasing latency, semaphore contention, and HTTP connection overhead.

### Proposed Behavior
- `search_via_perplexity_search_api` and `async_search_via_perplexity_search_api` accept `query: Union[str, List[str]]`.
- If a list of strings is provided, it sends `{"query": query_list, "max_results": 10, "search_context_size": "high"}` in a single HTTP POST request.
- `PerplexitySearchQueue.batch_search()` gathers all uncached queries in a section and executes them in **one single HTTP request**.
- The number of live HTTP calls per section drops from 4–5 down to 1 (a ~75–80% reduction in network requests), fully utilizing Perplexity's 50 QU/s capacity.

---

## 4. Implementation Steps
1. **Feature Documentation**: Create `plan.md`, `decisions.md`, `implementation.md`, `verification.md`, `qa-checklist.md`.
2. **`backend/app/agents/researcher/tools.py`**:
   - Update `search_via_perplexity_search_api` and `async_search_via_perplexity_search_api` to accept `query: Union[str, List[str]]`.
   - Normalize string vs list, validate list length (cap at 50 queries), and structure return results.
3. **`backend/app/workflows/do_risk_report/retrieval.py`**:
   - Update `PerplexitySearchQueue.batch_search()` to send query lists to `search()` / `_execute_live_search()`.
   - Update caching for batch queries.
4. **Automated Testing**:
   - Add unit tests in `backend/test_do_risk_report.py` testing list-of-strings query payloads for sync and async tools.
5. **End-to-End Verification**:
   - Run automated test suite (40+ tests).
   - Test live report generation with tree timing visualization.
6. **Documentation & Changelog**:
   - Update `CHANGELOG.md` and feature docs.

---

## 5. Files to Change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/agents/researcher/tools.py` | Add `Union[str, List[str]]` multi-query support | Native batch query support for Search API |
| `backend/app/workflows/do_risk_report/retrieval.py` | Batch section queries into single multi-query calls | Eliminate individual query HTTP roundtrips |
| `backend/test_do_risk_report.py` | Add test cases for query list payload | Verify batch query schema and mock parsing |
| `docs/features/perplexity-search-batch-query/*` | Feature docs | Compliance with AGENTS.md |
| `docs/decisions/perplexity-search-batch-query/decisions.md` | Architectural decision record | Architectural record for batch query dispatch |
| `CHANGELOG.md` | Release notes | Definition of Done |

---

## 6. Risks and Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Mixed cache keys with query lists | Inaccurate cache hits | Sort and hash string lists into a deterministic cache key |
| Max query limit per request | HTTP 400 if list > 50 | Chunk query list to max 50 queries if input exceeds limit |
| Results deduplication | Overlapping snippets across queries | `ResultCompactor.deduplicate_results` collapses duplicate URLs and identical snippets |
