# QA Checklist: Multi-Provider LLM Switching Flag (`gemini`, `qwen`, `gpt-oss`, `iteracompute`)

**Datetime**: 2026-11-03T18:03:00+05:30  
**Feature Slug**: `multi-provider-llm-switching`

---

## Pre-Release Verification Checklist

- [x] **CLI Flag Parsing**:
  - [x] `python backend/run_do_risk_report.py --help` shows `--provider`, `--llm-provider`, `--model-family` choices: `[gpt-oss, qwen, gemini, iteracompute]`.
  - [x] Environment variable `LLM_PROVIDER` serves as the fallback default when no CLI flag is passed.

- [x] **Provider Routing Engine**:
  - [x] `gpt-oss`: Dispatches to Groq LPUs (`openai/gpt-oss-20b`, `openai/gpt-oss-120b`).
  - [x] `qwen`: Dispatches to Groq LPUs (`qwen/qwen3.8-27b`).
  - [x] `gemini`: Dispatches to Google GenAI SDK (`gemini-3.5-flash` or `GEMINI_MODEL`).
  - [x] `iteracompute`: Dispatches to IteraCompute API (`https://api.iteracompute.com/v1`) using `ITERACOMPUTE_API_KEY` and model `qwen/qwen3.8-27b`.

- [x] **Pipeline Preservation**:
  - [x] Perplexity Search API retrieval (`search_via_perplexity_search_api`) remains untouched and dedicated to web search.
  - [x] SEC EDGAR XBRL facts parser remains deterministic and 0-token cost.
  - [x] Validation agent inherits active provider for repair loop.

- [x] **Telemetry & Reporting**:
  - [x] CLI banner displays active provider name.
  - [x] Tree and table formatting dynamically display active provider and model name.
  - [x] Telemetry dictionary records `"llm_provider"`.

- [x] **Safety & Constraints**:
  - [x] User instruction observed: live test execution was NOT triggered automatically.
  - [x] Unit test suite passed with 48/48 tests OK.
