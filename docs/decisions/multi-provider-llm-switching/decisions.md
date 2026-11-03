# Architecture Decision Record: Multi-Provider LLM Switching Engine

**Datetime**: 2026-11-03T18:03:30+05:30  
**Slug**: `multi-provider-llm-switching`  
**Status**: Accepted

---

## Context
The D&O Risk Underwriting Report pipeline coordinates several distinct LLM roles:
1. `extract`: Atomic factual extraction adhering to strict entity guard and evidence schemas.
2. `gap`: Identification of missing disclosures and formulation of follow-up queries.
3. `draft`: Section narrative drafting with strict `[E###]` citation tokens.
4. `synthesize`: Executive synthesis and overall risk verdict tiering.
5. `repair`: Validation agent repair and text patching under zero-web-access constraints.

Previously, these roles were bound to Groq models (`openai/gpt-oss-20b` and `openai/gpt-oss-120b`). The user required the ability to switch between model families (`gpt-oss`, `qwen`, `gemini`, and `iteracompute`) simply by passing CLI flags or setting environment variables, without changing source code.

---

## Decision
1. **Separation of Search vs. Inference**:
   - Web search retrieval remains strictly routed through the Perplexity Search API (`search_via_perplexity_search_api`), benefiting from batch multi-query speedups and low token usage.
   - Non-retrieval LLM roles are managed by a centralized provider dispatcher in `roles.py`.

2. **Provider Hierarchy & Model Mapping**:
   - **`gpt-oss` (Groq LPUs)**:
     - Fast / Medium: `openai/gpt-oss-20b`
     - Reasoning: `openai/gpt-oss-120b`
   - **`qwen` (Groq LPUs)**:
     - Fast / Medium / Reasoning: `qwen/qwen3.8-27b`
   - **`gemini` (Google GenAI SDK)**:
     - Fast / Medium / Reasoning: `gemini-3.5-flash` (configurable via `GEMINI_MODEL`)
     - Schema Enforcement: `response_mime_type="application/json"`
   - **`iteracompute` (IteraCompute OpenAI-Compatible Gateway)**:
     - Endpoint: `https://api.iteracompute.com/v1/chat/completions`
     - Default Model: `qwen/qwen3.8-27b` (Active free tier on user account)
     - Configurable via `ITERACOMPUTE_MODEL` and `ITERACOMPUTE_BASE_URL`
     - Transport: Asynchronous `httpx` with JSON object formatting and 130s timeout to accommodate queue spikes.

3. **Validation Agent Consistency**:
   - `ValidationAgent` in `validator.py` previously had a hardcoded `model_override="openai/gpt-oss-120b"`. This was updated to inherit the active provider (`provider_override=self.provider`), guaranteeing end-to-end provider parity.

4. **CLI Flag Precedence**:
   - Priority 1: CLI flag `--provider <name>` (or `--llm-provider`, `--model-family`).
   - Priority 2: Environment variable `LLM_PROVIDER`.
   - Priority 3: Default fallback `gpt-oss`.

---

## Consequences
- Zero downtime during provider rate limit or quota events: developers can fail over between Groq LPUs, Google GenAI, and IteraCompute instantly via `--provider <choice>`.
- Preserves 100% offline testability: `TESTING=true` returns deterministic mock objects without invoking external network requests.
