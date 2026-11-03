# Feature Verification: Rate Limit Fallback Model (`--fallback-model`, `AZURE_FALLBACK_MODEL`)

**Datetime**: 2026-11-03T21:22:00+05:30  
**Feature Slug**: `rate-limit-fallback-model`  
**Status**: Verified via Automated Unit Tests & Live Endpoint Health Checks

---

## 1. Automated Test Suite Execution

All 50 unit tests were executed with `TESTING=true` to verify fallback model failover logic without invoking full report generation.

### Command
```powershell
$env:PYTHONPATH="backend"; $env:TESTING="true"; backend\venv\Scripts\python.exe -m unittest backend.test_do_risk_report
```

### Result
```text
Ran 50 tests in 3.170s
OK
[RATE LIMIT 429] Role 'synthesize' hit TPM rate limit on 'claude-opus-4-8'. Failing over to fallback model 'claude-sonnet-4-6'...
[FALLBACK SUCCESS] Role 'synthesize' succeeded with fallback model 'claude-sonnet-4-6'
```

---

## 2. Verified Test Cases

1. **`test_fallback_model_get_set`**:
   - Verified that `set_fallback_model("claude-sonnet-4-6")` sets `get_fallback_model() == "claude-sonnet-4-6"`.
   - Verified that `set_fallback_model(None)` resets the fallback model.

2. **`test_cli_fallback_model_parsing`**:
   - Verified that `--fallback-model claude-sonnet-4-6` is parsed by `build_parser()`.

3. **`test_azure_rate_limit_failover_to_fallback`**:
   - Simulated an HTTP 429 TPM rate limit error on `claude-opus-4-8`.
   - Verified that the role dispatcher intercepted the 429 error and executed `claude-sonnet-4-6`.
   - Verified that the fallback model output was successfully extracted and returned.

---

## 3. Live Deployment Health Checks

1. **`claude-opus-4-8` Deployment**:
   - Verified response on `https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages`.
2. **`claude-sonnet-4-6` Deployment**:
   - Verified response on `https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages` (HTTP 200, returned `"Sonnet Ready"` in ~3.8s).
