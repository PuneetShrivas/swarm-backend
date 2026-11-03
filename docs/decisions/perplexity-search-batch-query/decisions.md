# Architectural Decisions: Perplexity Search API Batch Query Support

**Datetime**: 2026-11-03T17:07:30+05:30  
**Slug**: `perplexity-search-batch-query`

---

## Decision 1: Accept `Union[str, List[str]]` in Search API Functions

### Context
Perplexity's Search API endpoint (`POST https://api.perplexity.ai/search`) natively supports passing a JSON array of query strings in the `"query"` field (e.g. `{"query": ["q1", "q2", "q3"]}`). Perplexity handles up to 50 Query Units (QU) per second. Previously, the client wrapped each query in a distinct HTTP request, creating 40–55 separate HTTP roundtrips across 11 parallel sections.

### Decision
Allow both single string queries and lists of query strings in `search_via_perplexity_search_api` and `async_search_via_perplexity_search_api`. In `PerplexitySearchQueue.batch_search`, consolidate uncached section queries into a single multi-query request.

### Rationale
- **75–80% Drop in HTTP Requests**: A section with 4 queries makes 1 HTTP call instead of 4.
- **Lower Latency**: Roundtrip overhead is eliminated; Perplexity searches all queries concurrently on its index.
- **Backwards Compatibility**: Code that passes a single query string continues to work unchanged.
- **Safe Chunking**: If query list exceeds 50 items, it automatically chunks to stay within Perplexity's 50 QU/request limit.
