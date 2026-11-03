# Architectural Decisions: Perplexity Search API vs. Completions Endpoint

**Datetime**: 2026-11-03T16:46:15+05:30  
**Slug**: `perplexity-search-api-integration`

---

## Decision 1: Use Raw Search Endpoint (`POST /search`) Instead of Chat Completions (`POST /chat/completions`)

### Context
The D&O Underwriting pipeline previously queried `https://api.perplexity.ai/chat/completions` using the `sonar` model. Although Sonar produced cited prose summaries, it had notable drawbacks:
1. High generation latency (2.5–5.0 seconds per query).
2. Perplexity LLM token consumption on every query.
3. Burst-query throttling resulting in HTTP 429 errors.
4. Loss of original full-text excerpts from authoritative sources (court dockets, SEC filings, rating agencies).

### Decision
Switch to Perplexity's raw Search API endpoint (`POST https://api.perplexity.ai/search`).

### Rationale
- **Zero LLM Token Usage**: The Search API queries Perplexity's real-time web search index directly without LLM completion tokens.
- **Lower Latency**: Pure search latency is ~0.8–1.8 seconds (2–3x faster).
- **Rich Context Snippets**: With `search_context_size: "high"`, the endpoint returns deep contextual snippets (up to 8,000+ chars) preserving verbatim quotes, docket numbers, dates, and names.
- **Clear Separation of Concerns**: Perplexity performs fast factual retrieval; Groq LPUs (`openai/gpt-oss-20b` and `openai/gpt-oss-120b`) perform high-speed claim extraction, reasoning, and synthesis.

---

## Decision 2: Concurrency & Backoff Strategy
- **Concurrency Limit**: Set `max_concurrency = 2` on the async search queue.
- **Exponential Backoff**: Up to 4 attempts with delays of 2s, 4s, 8s on HTTP 429 or network errors.
- **Polite Inter-Request Gap**: 0.3s sleep after successful requests to prevent bursts.
- **No Mock Fallback in Live Mode**: In live production mode, transient network failures return empty lists rather than polluting underwriting reports with synthetic mock data.
