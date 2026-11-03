# Feature Verification: Multi-Provider LLM Switching Flag (`gemini`, `qwen`, `gpt-oss`, `iteracompute`)

**Datetime**: 2026-11-03T18:02:30+05:30  
**Feature Slug**: `multi-provider-llm-switching`  
**Status**: Verified via Automated Unit Tests

---

## 1. Automated Test Suite Execution

All unit tests were executed with `TESTING=true` to verify provider resolution, CLI flag handling, role execution dispatch, and mock integrity without invoking live billable API calls or premature report generation.

### Command
```powershell
$env:PYTHONPATH="backend"; $env:TESTING="true"; backend\venv\Scripts\python.exe -m unittest backend.test_do_risk_report
```

### Result
```text
Ran 48 tests in 3.126s
OK
```

---

## 2. Verified Test Cases

1. **`test_provider_switching_and_resolution`**:
   - Verified that `set_active_provider("gpt-oss")` selects `openai/gpt-oss-20b` and `openai/gpt-oss-120b`.
   - Verified that `set_active_provider("qwen")` selects `qwen/qwen3.8-27b`.
   - Verified that `set_active_provider("gemini")` selects Google Gemini.
   - Verified that `set_active_provider("iteracompute")` and `set_active_provider("itera")` select IteraCompute with `qwen/qwen3.8-27b`.
   - Verified that invalid provider strings raise `ValueError`.

2. **`test_cli_provider_flag_parsing`**:
   - Verified that `--provider gemini` sets `args.provider = "gemini"`.
   - Verified that `--provider qwen` sets `args.provider = "qwen"`.
   - Verified that `--provider iteracompute` sets `args.provider = "iteracompute"`.
   - Verified that `--llm-provider gpt-oss` sets `args.provider = "gpt-oss"`.

3. **`test_run_role_timings_provider_meta`**:
   - Verified that calling `run_role_with_timings(provider_override="iteracompute")` returns metadata containing `"provider": "iteracompute"`.

4. **`test_validation_agent_provider_attribute`**:
   - Verified that `ValidationAgent(provider="iteracompute")` retains `provider="iteracompute"` and threads it to `run_role("repair")`.

---

## 3. Live Connectivity Verification (Scratch Diagnostics)

1. **IteraCompute Models Catalog**:
   - Queried `https://api.iteracompute.com/v1/models` with API key `sk-6l-Ji8mt29t_12KhDvHPfw`.
   - Verified endpoint returned status 200 with 28 models cataloged.
   - Identified `qwen/qwen3.8-27b` as the active free-tier model with 30M token allowance.
   - Confirmed end-to-end chat completion response: `Ready` (HTTP 200).

2. **Google Gemini Compatibility**:
   - Confirmed `gemini-3.5-flash` and `gemini-3.5-flash-lite` are active and responsive with `response_mime_type="application/json"`.

3. **Groq LPU Connectivity**:
   - Confirmed `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, and `qwen/qwen3.8-27b` are operational.
