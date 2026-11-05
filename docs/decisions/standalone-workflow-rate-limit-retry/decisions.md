# Decision Record: Replicating Rate Limit Cooldown & Non-Skipping Recovery to Standalone Package

## Datetime
`2026-11-05T14:26:15+05:30`

## Context
The standalone portable package located at root (`agnostic_workflow/`) was created to allow independent execution in remote environments without backend dependencies. During high-volume report generation across multiple sections, Azure Foundry imposes minute-based output token quotas (`UserByModelByMinuteOutputTokens`), triggering HTTP 429 errors.

The fixes implemented in `backend/app/workflows/agnostic_research_report/` must be faithfully replicated to `agnostic_workflow/` while preserving its strict zero-external-app-dependency guarantee.

## Decisions

1. **Parity of Retry Architecture**:
   - `agnostic_workflow/roles.py` receives the identical `parse_retry_delay()` helper and multi-round cooldown loop (`max_outer_rounds = 5`, countdown timer) using standard library `asyncio` and `re`.
   - `agnostic_workflow/orchestrator.py` receives the identical persistent section drafting and synthesis retry loops.

2. **Zero-App-Dependency Invariant**:
   - No imports from `backend/app/*` are introduced. All imports in `agnostic_workflow/` remain strictly self-contained or standard library / pip dependencies.
   - Verified via `test_01_zero_app_imports`.

3. **Archive Synchronization**:
   - `agnostic_workflow.zip` is updated to package the latest resilient files so zip distributions deployed elsewhere benefit from rate-limit handling out of the box.

## Consequences
- Standalone runs in external environments will not fail or emit incomplete reports with inline error bullets on Azure rate limits.
- The standalone package retains 100% architectural parity with the backend module.
