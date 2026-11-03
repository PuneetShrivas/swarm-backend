# Feature Implementation: Rate Limit Fallback Model (`--fallback-model`, `AZURE_FALLBACK_MODEL`)

**Datetime**: 2026-11-03T21:21:30+05:30  
**Feature Slug**: `rate-limit-fallback-model`  
**Status**: Implemented

---

## 1. Overview
This feature introduces automatic rate-limit failover from a primary LLM model (such as `claude-opus-4-8` on Azure AI Foundry) to a secondary/fallback model (`claude-sonnet-4-6`). When concurrent section generation triggers an HTTP 429 (`TPM limit exceeded`), the role execution dispatcher immediately retries the request using the fallback model, preventing pipeline stalls and 60-second backoff waits.

---

## 2. Configuration Options

| Option Type | Identifier | Default / Example | Purpose |
| :--- | :--- | :--- | :--- |
| **CLI Flag** | `--fallback-model`, `--secondary-model` | `claude-sonnet-4-6` | Command-line specification of secondary model |
| **Environment Variable** | `AZURE_FALLBACK_MODEL` | `claude-sonnet-4-6` | Azure Foundry default fallback model |
| **Generic Env Variable** | `LLM_FALLBACK_MODEL` | `None` | Provider-agnostic fallback model |
| **Python API** | `set_fallback_model("claude-sonnet-4-6")` | N/A | Dynamic programmatic setting |

---

## 3. Modified Files

1. **`backend/.env`**:
   - Added `AZURE_FALLBACK_MODEL="claude-sonnet-4-6"`
2. **`backend/app/workflows/do_risk_report/roles.py`**:
   - Added `ACTIVE_FALLBACK_MODEL`, `set_fallback_model()`, and `get_fallback_model()`.
   - Updated `run_role()` to construct `models_sequence = [selected_model, active_fallback]`.
   - When an HTTP 429 (or token rate limit error) is encountered on the primary model, it logs `[RATE LIMIT 429]` and immediately falls over to the secondary model.
   - Upon successful generation by the secondary model, logs `[FALLBACK SUCCESS]` and returns the parsed result.
   - Updated `run_role_with_timings()` to accept and track `fallback_model`.
3. **`backend/app/workflows/do_risk_report/orchestrator.py`**:
   - Added `fallback_model: Optional[str] = None` to `DORiskReportOrchestrator.run()`.
   - Populated `fallback_model` in execution telemetry.
4. **`backend/app/workflows/do_risk_report/cli.py`**:
   - Added `--fallback-model` / `--secondary-model` arguments to `build_parser()`.
   - Added `Fallback Model: {fallback_model}` to CLI banner.
   - Passed `fallback_model` into `orchestrator.run()`.
5. **`backend/test_do_risk_report.py`**:
   - Added unit tests for fallback model getter/setter, CLI flag parsing, and simulated 429 failover.
