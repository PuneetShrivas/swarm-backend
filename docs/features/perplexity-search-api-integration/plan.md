# Feature Plan: Perplexity Search API Integration for D&O Workflow

**Datetime**: 2026-11-03T16:46:00+05:30  
**Feature Slug**: `perplexity-search-api-integration`  
**Status**: Approved / In progress

---

## 1. Goal
Integrate Perplexity's dedicated raw Search API endpoint (`POST https://api.perplexity.ai/search`) into `backend/app/agents/researcher/tools.py` and replace the slower LLM chat completions endpoint (`https://api.perplexity.ai/chat/completions`) in the D&O Public Risk Underwriting workflow (`retrieval.py`). This delivers 3-5x faster web retrieval speeds, eliminates Perplexity LLM generation latency and token usage, returns rich contextual snippets (up to 8,000+ characters), and passes these factual excerpts directly to Groq LPUs for claim extraction and synthesis.

---

## 2. Scope

### In Scope
- Create `search_via_perplexity_search_api()` and async equivalent in `backend/app/agents/researcher/tools.py`.
- Integrate the Search API into `backend/app/workflows/do_risk_report/retrieval.py` (`PerplexitySearchQueue._execute_live_search()`).
- Add robust exponential backoff retry (up to 4 attempts) on HTTP 429 and transient connection drops.
- Clean and compact the returned rich snippets (`snippet`, `title`, `url`, `date`, `last_updated`) for feeding into Groq `extract` and `draft`.
- Unit tests covering `search_via_perplexity_search_api` and the updated retrieval queue.
- Live execution and benchmark quality comparison for NVIDIA (`NVDA`).

### Out of Scope
- Deprecating DuckDuckGo or other fallback search providers.
- Changing Groq model assignments.

---

## 3. Current Behavior vs. Proposed Behavior

### Current Behavior
- `retrieval.py` called `POST https://api.perplexity.ai/chat/completions` using the `sonar` generative model.
- Each query triggered a full LLM completion cycle on Perplexity (generating prose text with inline bracket citations).
- Latency per query was 2.5–5.0 seconds and consumed LLM completion tokens on Perplexity.
- Under parallel burst queries, Perplexity's completions endpoint frequently throttled with HTTP 429.

### Proposed Behavior
- `backend/app/agents/researcher/tools.py` introduces `search_via_perplexity_search_api()` querying `POST https://api.perplexity.ai/search`.
- Payload sends `{"query": query, "max_results": max_results, "search_context_size": "high"}`.
- Response returns structured `results[]` array with `title`, `url`, `snippet`, `date`, `last_updated`.
- Latency drops to ~0.8–1.8 seconds per query with **zero completion token spend** on Perplexity.
- Raw snippets contain rich contextual text (up to 8,000 chars) preserving quotes, dockets, executive names, and dates for Groq extraction.

---

## 4. Implementation Steps
1. **Feature Documentation**: Create feature plan, decisions record, implementation doc, verification doc, and QA checklist.
2. **`backend/app/agents/researcher/tools.py`**:
   - Implement `search_via_perplexity_search_api(query, api_key, max_results=5, search_context_size="high")`.
   - Implement `async_search_via_perplexity_search_api(...)` with retry and rate-limit handling.
3. **`backend/app/workflows/do_risk_report/retrieval.py`**:
   - Update `_execute_live_search()` to use the Search API function.
   - Map `results[]` to internal snippet structure and compact them.
4. **Verification**:
   - Add unit tests in `backend/test_do_risk_report.py`.
   - Execute live report generation for NVIDIA (`NVDA`) with `--mode standard --format tree`.
   - Validate timings, page count, and quality parity.
5. **Changelog & Documentation Updates**: Update `CHANGELOG.md` and feature docs.

---

## 5. Files to Change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/agents/researcher/tools.py` | Add `search_via_perplexity_search_api` and async helper | Dedicated raw search function returning ranked snippets |
| `backend/app/workflows/do_risk_report/retrieval.py` | Route live search through Search API endpoint with backoff | Fast, token-efficient web retrieval for D&O pipeline |
| `backend/test_do_risk_report.py` | Add test coverage for new Search API function | Prevent regression and verify mock/live compatibility |
| `docs/features/perplexity-search-api-integration/*` | Feature documentation | Compliance with AGENTS.md |
| `docs/decisions/perplexity-search-api-integration/decisions.md` | Architectural decision record | Traceability of API endpoint selection |
| `CHANGELOG.md` | Add release notes | Definition of Done |

---

## 6. Risks and Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Perplexity Search API key permissions | 401/403 if key lacks search scope | Validated live: user's API key returned HTTP 200 with 5 rich snippets in 1.84s |
| Rate limits on Search API | 429 status during burst queries | Exponential backoff (2s, 4s, 8s) + semaphore concurrency limit of 2 |
| Varying snippet sizes | Excessively large snippets exceeding context | `ResultCompactor.clean_snippet(max_chars=1500)` ensures concise ingestion |
