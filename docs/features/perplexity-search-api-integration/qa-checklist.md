# QA Checklist: Perplexity Search API Integration for D&O Workflow

**Datetime**: 2026-11-03T16:51:00+05:30  
**Feature Slug**: `perplexity-search-api-integration`

---

## Pre-Release QA Items

- [x] **New Function Availability**: `search_via_perplexity_search_api` is exported and usable in `backend/app/agents/researcher/tools.py`.
- [x] **Async Support**: `async_search_via_perplexity_search_api` handles async workflows with exponential backoff.
- [x] **Live Endpoint Connectivity**: `POST https://api.perplexity.ai/search` returns HTTP 200 with user's `PERPLEXITY_API_KEY`.
- [x] **High-Context Snippets**: `search_context_size: "high"` delivers deep factual snippets (up to 8,000+ chars) to Groq.
- [x] **Zero Mock Fallback**: Live runs never inject synthetic mock data on network errors.
- [x] **Section Retention**: All 11 underwriting sections are preserved without LLM truncation.
- [x] **Unit Tests**: All test suites pass without regression.
- [x] **Deliverables Verification**: MD, DOCX, and PDF generate with running headers and `Page X of Y` footers.
- [x] **Changelog Entry**: Concise entry added to `CHANGELOG.md`.
