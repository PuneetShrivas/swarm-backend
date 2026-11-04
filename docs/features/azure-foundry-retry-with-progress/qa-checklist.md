# QA Checklist: Azure Foundry Multi-Round Retry & Visual Cooldown Progress

**Created Datetime**: 2026-11-04T15:01:30+05:30  
**Last Updated Datetime**: 2026-11-04T15:01:30+05:30  
**Feature Slug**: `azure-foundry-retry-with-progress`  
**Status**: Complete

---

## Pre-Release Acceptance Criteria

- [x] **Multi-Round Outer Retry**: Azure Foundry execution loops up to `AZURE_MAX_RETRY_ROUNDS` (default: 5) across `models_sequence`.
- [x] **Configurable Cooldown**: `AZURE_RETRY_WAIT_SECONDS` (default: 25s) with incremental backoff (+10s per round).
- [x] **Live Visual Progress**: Progress bar, percentage, and second-by-second countdown emitted at 5-second intervals with `flush=True`.
- [x] **Transient Error Detection**: Automatic classification of 429, TPM, quota, timeout, and 5xx server errors as retryable.
- [x] **Immediate Non-Transient Abort**: Non-transient errors (401 Unauthorized, 400 Bad Request) terminate immediately without wasting time in sleep loops.
- [x] **Testing Mode Guard**: Unit tests with `TESTING=true` bypass multi-minute sleep loops and complete in seconds.
- [x] **Automated Tests**: Unit tests covering non-transient aborts and transient retry recovery passing.
- [x] **Documentation Integrity**: Feature plan, implementation log, verification report, and ADR updated with Datetime timestamps.
