# Feature Plan: Multi-Provider LLM Switching Flag (`gemini`, `qwen`, `gpt-oss`, `iteracompute`)

**Datetime**: 2026-11-03T18:01:00+05:30  
**Feature Slug**: `multi-provider-llm-switching`  
**Status**: Implemented & Verified (Unit Tests Passing; Awaiting Live Run Approval)

---

## 1. Goal
Provide a unified CLI flag and configuration setting (`--provider {gpt-oss,qwen,gemini,iteracompute}`, `--llm-provider`, `--model-family`, or `LLM_PROVIDER` environment variable) that allows the user to switch seamlessly between model families for all non-Perplexity tasks (claim extraction, gap analysis, narrative drafting, executive synthesis, deterministic repair, and post-generation validation audit) without changing code.

---

## 2. Scope

### In Scope
- Define provider tiers in `backend/app/workflows/do_risk_report/roles.py`:
  - `gpt-oss`: `openai/gpt-oss-20b` (fast/medium) & `openai/gpt-oss-120b` (reasoning/synthesis) on Groq LPUs.
  - `qwen`: `qwen/qwen3.8-27b` on Groq LPUs.
  - `gemini`: `gemini-3.5-flash` (with optional `gemini-3.5-flash-lite` or custom override via `GEMINI_MODEL`) via Google GenAI SDK.
  - `iteracompute`: OpenAI-compatible API (`https://api.iteracompute.com/v1`) using `ITERACOMPUTE_API_KEY`, defaulting to the free-tier model `qwen/qwen3.8-27b` (or custom override via `ITERACOMPUTE_MODEL`).
- Add Google GenAI client handling to `roles.py` with structured JSON output (`response_mime_type="application/json"`).
- Add IteraCompute OpenAI-compatible client handling to `roles.py` via asynchronous `httpx` with `response_format={"type": "json_object"}`.
- Add `--provider` (`--llm-provider`, `--model-family`) CLI argument in `backend/app/workflows/do_risk_report/cli.py` and pass to `DORiskReportOrchestrator.run()`.
- Thread `provider` to `ValidationAgent` in `backend/app/workflows/do_risk_report/validator.py`.
- Update telemetry and timing tree display to clearly indicate the active provider and models used.
- Add unit tests verifying provider resolution, model mapping, and configuration switching.

### Out of Scope
- Changing Perplexity search retrieval logic (web search remains routed strictly via Perplexity Search API).
- Running live report generation tests prematurely before explicit user approval.

---

## 3. Current Behavior vs. Proposed Behavior

### Current Behavior
- Model tiers were hardcoded in `roles.py` and `validator.py`:
  - `GROQ_FAST_TIER = "openai/gpt-oss-20b"`
  - `GROQ_MEDIUM_TIER = "openai/gpt-oss-20b"`
  - `GROQ_REASONING_TIER = "openai/gpt-oss-120b"`
- Switching between Qwen, GPT-OSS, Gemini, or Iteracompute required modifying source code.

### Proposed Behavior
- CLI flag `--provider {gpt-oss,qwen,gemini,iteracompute}` (or `LLM_PROVIDER` env var) controls model selection across all roles.
- `roles.py` dispatches to Groq LPUs, Google GenAI, or Iteracompute gateway seamlessly.
- Active provider is reported in the CLI banner, progress logs, telemetry, and timings tree.

---

## 4. Implementation Steps
1. **Feature Documentation**: Create plan, decisions, implementation doc, verification doc, and QA checklist.
2. **Environment Configuration**: Add `ITERACOMPUTE_API_KEY`, `ITERACOMPUTE_BASE_URL`, and `ITERACOMPUTE_MODEL` to `backend/.env`.
3. **`roles.py` Multi-Provider Engine**:
   - Add `PROVIDER_MODELS` dictionary defining models per role for `gpt-oss`, `qwen`, `gemini`, and `iteracompute`.
   - Implement `_execute_gemini_chat()` and `_execute_iteracompute_chat()` with JSON response parsing and backoff.
   - Update `run_role()` and `run_role_with_timings()` to accept `provider_override`.
   - Provide `set_active_provider(provider)` and `get_active_provider()`.
4. **`validator.py`**:
   - Accept `provider` in `ValidationAgent.__init__` and pass `provider_override=self.provider` to `run_role("repair")`.
5. **`orchestrator.py` & `cli.py`**:
   - Accept `--provider` / `provider` argument in CLI parser and `DORiskReportOrchestrator.run()`.
   - Update telemetry to include `llm_provider` and dynamic model descriptions.
6. **Testing & Verification**:
   - Add unit tests verifying provider selection, aliases, and model mapping.
   - Run unit test suite in mock mode to confirm 100% pass rate.
