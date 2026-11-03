# QA Checklist: Batch Search Query Method for Perplexity Search API

**Datetime**: 2026-11-03T17:12:00+05:30  
**Feature Slug**: `perplexity-search-batch-query`

---

## Pre-Release QA Items

- [x] **`Union[str, List[str]]` Support**: `search_via_perplexity_search_api` and `async_search_via_perplexity_search_api` accept single string or query list.
- [x] **Batch Query Request Payload**: `query` field in payload contains the string list directly when passed.
- [x] **50 Query Limit**: Input lists exceeding 50 queries are safely capped at 50 to respect Perplexity QU limits.
- [x] **Section Consolidation in D&O Workflow**: `PerplexitySearchQueue.batch_search` sends all uncached section queries in a single HTTP request.
- [x] **Cache Integrity**: Individual and batch query cache entries are preserved and retrievable.
- [x] **Unit Tests**: Added unit tests for sync and async multi-query execution.
- [x] **Regression Suite**: All 44 tests pass.
- [x] **Changelog Entry**: Concise entry added to `CHANGELOG.md`.
