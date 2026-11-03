# QA Checklist: Rate Limit Fallback Model (`--fallback-model`, `AZURE_FALLBACK_MODEL`)

**Datetime**: 2026-11-03T21:22:30+05:30  
**Feature Slug**: `rate-limit-fallback-model`

---

## Pre-Release Verification Checklist

- [x] **CLI Flag Parsing**:
  - [x] `python backend/run_do_risk_report.py --help` shows `--fallback-model`, `--secondary-model` arguments.
  - [x] Environment variable `AZURE_FALLBACK_MODEL` / `LLM_FALLBACK_MODEL` acts as the default fallback when no flag is supplied.

- [x] **Failover Logic**:
  - [x] Primary model is attempted first.
  - [x] Upon encountering HTTP 429 (`TPM rate limit`), the dispatcher catches the exception and attempts `claude-sonnet-4-6`.
  - [x] Succeeded fallback outputs are logged with `[FALLBACK SUCCESS]`.

- [x] **Safety & Constraints**:
  - [x] User instruction observed: overall report generation was NOT executed.
  - [x] Unit test suite passed with 50/50 tests OK.
