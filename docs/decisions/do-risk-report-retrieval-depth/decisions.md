# Architectural Decisions: Perplexity Retrieval Timeout Extension & Comprehensive Research Extraction

**Created Datetime**: 2026-11-03T15:55:00+05:30  
**Last Updated Datetime**: 2026-11-03T15:55:00+05:30  

## Decision 1: Extend Perplexity HTTP Timeout to 60.0 Seconds
- **Context**: Deep underwriting search queries across 11 parallel sections can experience queue latency at Perplexity. A 15-second timeout caused frequent `httpx.ReadTimeout` errors, leading to missing data.
- **Decision**: Extend `DEFAULT_PERPLEXITY_TIMEOUT` to 60.0 seconds.
- **Consequence**: Perplexity queries have sufficient runway to crawl, verify sources, and return grounded answers without throwing premature timeouts.

## Decision 2: Remove Hard Boolean `site:` Operators in Favor of Natural Search
- **Context**: Restricting Perplexity queries with `(site:reuters.com OR site:wsj.com)` causes Perplexity to fail or return empty content when those specific sites paywall financial tables or legal dockets.
- **Decision**: Remove hard boolean `site:` operators from the query string. Let Perplexity search across all relevant authoritative web sources (Yahoo Finance, MarketWatch, Bloomberg, SEC, S&P Global, PitchBook, CourtListener).
- **Consequence**: Perplexity returns extensive data tables (such as 52-analyst consensus breakdowns, stock betas, short interest, and executive names) that were previously blocked by paywalls.

## Decision 3: Comprehensive Grounded Synthesis Snippet Delivery
- **Context**: Previously, `_execute_live_search` mapped citation URL `i` to line `i` of the response text. When the response began with table borders or markdown headers, the snippet was reduced to a few non-substantive characters, causing Groq's extraction role to extract 0 claims.
- **Decision**: Always include the full synthesized answer content (up to 1,500 characters) as the primary research entry, followed by cited source references.
- **Consequence**: Groq receives the full multi-paragraph answer with all figures and dates, enabling extraction of 5–15 atomic claims per section.
