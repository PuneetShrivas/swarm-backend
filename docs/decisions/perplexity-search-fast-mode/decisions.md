# Architecture Decision: Global Perplexity Fast Search Mode (`search_type: "fast"`)

## Datetime
`2026-11-05T13:10:35+05:30`

## Context
Perplexity's API provides two web search tiers:
1. **Standard Search**: Deep web search with multi-hop synthesis queries ($5.00 / 1,000 requests).
2. **Fast Search** (`search_type: "fast"`): Low-latency, cost-optimized retrieval powered by Perplexity's high-speed Photon engine ($1.00 / 1,000 requests, typical response latency sub-250ms).

For our high-concurrency swarms and agent workflows (such as parallel multi-section research across 11+ sections in D&O and Agnostic pipelines), standard search adds unnecessary network latency and higher cost.

## Decision
Configure `"search_type": "fast"` across all Perplexity Search API and chat completion requests throughout the entire repository.
Specifically:
1. `backend/app/agents/researcher/tools.py`:
   - `search_via_perplexity_search_api()`: Pass `"search_type": os.environ.get("PERPLEXITY_SEARCH_TYPE", "fast")`
   - `async_search_via_perplexity_search_api()`: Pass `"search_type": os.environ.get("PERPLEXITY_SEARCH_TYPE", "fast")`
   - `search_via_perplexity()`: Pass `"search_type": "fast"`
2. `agnostic_workflow/retrieval.py`:
   - `async_search_via_perplexity_search_api()`: Pass `"search_type": os.environ.get("PERPLEXITY_SEARCH_TYPE", "fast")`
3. Default environment configuration:
   - Expose `PERPLEXITY_SEARCH_TYPE = "fast"` in `agnostic_workflow/config.py` and `.env.example`.
4. Endpoint calls in `backend/app/main.py` and `backend/app/workflows/engine.py`:
   - Include `"search_type": "fast"` in request payloads.

## Consequences
- 3x to 5x lower search retrieval latencies on all web queries.
- 80% reduction in Perplexity API usage costs ($1.00 vs $5.00 per 1,000 queries).
- Consistent behavior across backend workflows, agents, and the standalone `agnostic_workflow/` package.
