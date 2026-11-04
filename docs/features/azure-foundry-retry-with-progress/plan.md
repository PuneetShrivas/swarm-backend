# Feature: Azure Foundry Retry with Progress Cooldown

**Created Datetime**: 2026-11-04T14:48:55+05:30  
**Last Updated Datetime**: 2026-11-04T15:01:30+05:30  
**Feature Slug**: `azure-foundry-retry-with-progress`  
**Status**: Complete

---

## Goal

Instead of immediately terminating with a `RuntimeError` when models fail across an Azure Foundry sequence (e.g. hitting rolling 60-second Tokens-Per-Minute rate limits or temporary network timeouts), pause for a configured cooldown period, display real-time visual progress updates in the terminal, and retry across the model sequence.

---

## Scope

- **In scope**:
  - Multi-round retry loop (`AZURE_MAX_RETRY_ROUNDS`, default: 5) for Azure Foundry requests in `roles.py`.
  - Configurable base wait time (`AZURE_RETRY_WAIT_SECONDS`, default: 25) with incremental backoff.
  - Active visual progress indicators displayed in 5-second intervals during the cooldown period.
  - Transient vs non-transient error discrimination (retries on 429, TPM, 500, 502, 503, 504, timeout; aborts immediately on non-retryable 401/400).
  - Fast-path for testing mode (`is_testing`) to prevent unit test suites from sleeping unnecessarily.
- **Out of scope**:
  - Running live report generation (`run_do_risk_report.py`) before user approval.

---

## Current Behavior

When both the primary model and fallback model fail (e.g. due to rapid 429 TPM exhaustion during parallel section drafting), `roles.py` executes a single pass over `models_sequence` and immediately executes:
```python
raise RuntimeError(f"Role '{role}' Azure Foundry execution failed across models {models_sequence}: {last_azure_error}")
```
This aborts the entire report run even though waiting 20–30 seconds for the rolling 60-second TPM token bucket to reset would allow the run to continue and succeed.

---

## Proposed Behavior

1. Wrap the Azure Foundry execution in an outer multi-round retry loop (`max_outer_rounds = 5` by default, or 1 in test mode).
2. If all models in `models_sequence` fail with a retryable transient error (429, TPM limit, timeout, 5xx server error), enter a cooldown sleep before the next round.
3. During cooldown, print live progress updates every 5 seconds with a visual progress bar and countdown indicator.
4. Once the cooldown completes, resume the request with the primary model.
5. If non-retryable errors occur (401 invalid key, 400 bad request), abort immediately.
6. If all rounds are exhausted without success, raise the detailed `RuntimeError`.

---

## Implementation Steps

1. **Architecture Decision Record**: Document retry mechanics, backoff strategy, and progress display in `docs/decisions/azure-foundry-retry-with-progress/decisions.md`.
2. **Update `roles.py`**:
   - Implement `max_outer_rounds` loop over Azure execution.
   - Add transient error detection (`is_retryable`).
   - Implement progressive cooldown timer with 5-second console progress bar output.
3. **Log Implementation**: Record changes in `docs/features/azure-foundry-retry-with-progress/implementation.md`.
4. **Verification**: Verify code compilation and unit test compatibility without running live tests.
5. **Update Verification & QA Checklist**: Document test results in `verification.md` and `qa-checklist.md`.

---

## Files to Change

| File | Change | Reason |
| ---- | ------ | ------ |
| [`backend/app/workflows/do_risk_report/roles.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/roles.py) | Wrap Azure Foundry execution in outer retry loop with live progress output | Retry after transient rate limits instead of crashing |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Non-transient errors (e.g. invalid key) looping repeatedly | Long unhelpful wait | Check `is_retryable` keywords (429, rate limit, timeout, 503); abort immediately on auth/client errors |
| Unit tests hanging on retry sleeps | Slow test suite | Set `max_outer_rounds = 1` when `is_testing == True` |
