# Feature Implementation: Multi-Provider LLM Switching Flag (`gemini`, `qwen`, `gpt-oss`, `iteracompute`)

**Datetime**: 2026-11-03T18:02:00+05:30  
**Feature Slug**: `multi-provider-llm-switching`  
**Status**: Implemented

---

## 1. Overview
This implementation introduces dynamic multi-provider routing across all non-retrieval pipeline roles (claim extraction, gap checking, narrative section drafting, executive synthesis, deterministic repair, and validation audit). Web search remains routed through the fast Perplexity Search API.

---

## 2. Supported LLM Providers & Model Tiers

| Provider Flag | Backend Infrastructure | Fast Tier (`extract`, `gap`) | Medium Tier (`plan`, `draft`) | Reasoning Tier (`synthesize`, `repair`, `verify`) | Auth / Config Variables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`gpt-oss`** (Default) | Groq LPUs | `openai/gpt-oss-20b` | `openai/gpt-oss-20b` | `openai/gpt-oss-120b` | `GROQ_API_KEY` |
| **`qwen`** | Groq LPUs | `qwen/qwen3.8-27b` | `qwen/qwen3.8-27b` | `qwen/qwen3.8-27b` | `GROQ_API_KEY` |
| **`gemini`** | Google GenAI SDK | `gemini-3.5-flash` | `gemini-3.5-flash` | `gemini-3.5-flash` | `GEMINI_API_KEY` (override: `GEMINI_MODEL`) |
| **`iteracompute`** (alias: `itera`) | IteraCompute OpenAI-compatible API (`https://api.iteracompute.com/v1`) | `qwen/qwen3.8-27b` | `qwen/qwen3.8-27b` | `qwen/qwen3.8-27b` | `ITERACOMPUTE_API_KEY` (override: `ITERACOMPUTE_MODEL`, `ITERACOMPUTE_BASE_URL`) |
| **`azure`** (aliases: `azure-foundry`, `foundry`) | Azure AI Foundry Anthropic Endpoint (`https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages`) | `claude-opus-4-8` | `claude-opus-4-8` | `claude-opus-4-8` | `AZURE_API_KEY` (override: `AZURE_MODEL`, `AZURE_FOUNDRY_ENDPOINT`) |

---

## 3. Modified Files

1. **`backend/.env`**:
   - Added `ITERACOMPUTE_API_KEY="sk-6l-Ji8mt29t_12KhDvHPfw"`
   - Added `ITERACOMPUTE_BASE_URL="https://api.iteracompute.com/v1"`
   - Added `ITERACOMPUTE_MODEL="qwen/qwen3.8-27b"`

2. **`backend/app/workflows/do_risk_report/roles.py`**:
   - Added `ACTIVE_PROVIDER = os.environ.get("LLM_PROVIDER", "gpt-oss").lower()`
   - Added `PROVIDER_MODELS` mapping covering `gpt-oss`, `qwen`, `gemini`, `iteracompute`, and alias `itera`.
   - Implemented `set_active_provider(provider: str)` and `get_active_provider() -> str`.
   - Implemented `_execute_gemini_chat()` using `google.genai` SDK with `response_mime_type="application/json"`.
   - Implemented `_execute_iteracompute_chat()` using asynchronous `httpx.AsyncClient` with `response_format={"type": "json_object"}` and exponential backoff retry.
   - Updated `run_role()` and `run_role_with_timings()` to accept `provider_override` and dispatch seamlessly to the requested LLM provider.

3. **`backend/app/workflows/do_risk_report/validator.py`**:
   - Updated `ValidationAgent.__init__(self, current_date=None, provider="gpt-oss")` to store `self.provider`.
   - In `ValidationAgent.run()`, replaced hardcoded `model_override="openai/gpt-oss-120b"` with `provider_override=self.provider`.

4. **`backend/app/workflows/do_risk_report/orchestrator.py`**:
   - Added `provider: str = "gpt-oss"` parameter to `DORiskReportOrchestrator.run()`.
   - Calls `set_active_provider(provider)` at start of execution.
   - Passes active provider to `ValidationAgent(current_date=current_date, provider=active_prov)`.
   - Updated Stage 3 and Stage 4 telemetry to record model and provider dynamically.
   - Appended `"llm_provider": active_prov` to `ReportTelemetry`.

5. **`backend/app/workflows/do_risk_report/cli.py`**:
   - Added `--provider`, `--llm-provider`, `--model-family` CLI flags with choices `["gpt-oss", "qwen", "gemini", "iteracompute"]`.
   - Printed active provider in CLI banner (`LLM Provider: {provider.upper()}`).
   - Passed `provider=provider` to `orchestrator.run(...)`.
   - Updated `render_tree()` to show provider name dynamically instead of hardcoded "Groq".

6. **`backend/test_do_risk_report.py`**:
   - Added unit test cases for provider switching, alias resolution, CLI flag parsing, and ValidationAgent provider retention.
