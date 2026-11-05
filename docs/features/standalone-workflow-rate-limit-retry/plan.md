# Feature: Replicate Azure Rate Limit (HTTP 429) Retry & Cooldown to Standalone Agnostic Workflow

## Datetime
`2026-11-05T14:26:00+05:30`

## Status
Completed

## Goal
Replicate the resilient Azure Foundry rate-limit (HTTP 429 / TPM token limits) backoff, dynamic wait parsing, and non-skipping section drafting recovery from `backend/app/workflows/agnostic_research_report/` into the root-level standalone package `agnostic_workflow/` (`C:\Users\punee\OneDrive\Documents\GitHub\swarm-backend\agnostic_workflow`). Ensure the standalone package never skips sections upon encountering token rate limits and can recover smoothly in external, isolated environments.

## Scope
- In scope:
  - `agnostic_workflow/roles.py`:
    - Add `parse_retry_delay()` for extracting exact wait times from Azure Foundry 429 error payloads with `+2.0s` safety buffer.
    - Implement multi-round outer retry loop (`max_outer_rounds = 5`, configurable via `AZURE_MAX_RETRY_ROUNDS`) with progressive cooldown calculations and live terminal progress countdown logging.
    - Add in-attempt dynamic backoff when rate-limited.
  - `agnostic_workflow/orchestrator.py`:
    - Implement persistent section drafting retry loop (`max_draft_retries = 4`, configurable via `DRAFT_MAX_RETRIES`) in `_process_section()` to eliminate section skipping and `- Section drafting unavailable due to upstream error` fallbacks.
    - Implement persistent synthesis retry loop (`max_synth_retries = 4`, configurable via `SYNTH_MAX_RETRIES`) in `run()` Stage 3.
  - `agnostic_workflow/test_standalone_workflow.py`:
    - Add unit tests validating `parse_retry_delay()`, 429 role recovery, and non-skipping section draft recovery.
    - Ensure zero imports from `app.*` remain strictly upheld.
  - Distribution update:
    - Re-pack `agnostic_workflow.zip` so external distributions include the latest resilient code.
- Out of scope:
  - Modifying other workflow paths.

## Current behavior
1. `agnostic_workflow/roles.py` has fixed short sleeps (2s, 4s) across 2-3 attempts without reading upstream wait recommendations or cycling through outer cooldown rounds.
2. `agnostic_workflow/orchestrator.py` catches `Exception` during section drafting and immediately inserts `- Section drafting unavailable due to upstream error: {e}` into the report markdown, skipping the section.

## Proposed behavior
1. `agnostic_workflow/roles.py` parses `Please wait X seconds before retrying` from 429 errors, pauses accordingly, and executes up to 5 outer cooldown rounds with real-time countdown progress.
2. `agnostic_workflow/orchestrator.py` retries drafting and synthesis up to 4 attempts before giving up, ensuring transient rate limits never result in skipped sections.
3. Zero app dependencies are preserved (`agnostic_workflow/` remains 100% standalone).

## Implementation steps
1. Create feature plan and decision documentation.
2. Update `agnostic_workflow/roles.py` with `parse_retry_delay()` and multi-round cooldown logic.
3. Update `agnostic_workflow/orchestrator.py` with drafting and synthesis retry loops.
4. Update `agnostic_workflow/test_standalone_workflow.py` with rate limit parsing and recovery tests.
5. Re-generate `agnostic_workflow.zip`.
6. Run test suite to verify all unit tests pass.
7. Update verification report, QA checklist, implementation log, and changelog.
8. Git commit and push to `origin/main`.

## Files to change
| File | Change | Reason |
|---|---|---|
| `agnostic_workflow/roles.py` | Modify | Replicate dynamic 429 wait extraction and multi-round outer cooldown loop |
| `agnostic_workflow/orchestrator.py` | Modify | Replicate section drafting and synthesis retries to prevent skipping |
| `agnostic_workflow/test_standalone_workflow.py` | Modify | Add unit tests for rate-limit recovery and delay parsing |
| `agnostic_workflow.zip` | Re-generate | Keep standalone zip archive in sync |
| `docs/decisions/standalone-workflow-rate-limit-retry/decisions.md` | Create | Architecture decisions |
| `docs/features/standalone-workflow-rate-limit-retry/*` | Create | Feature lifecycle documentation |
| `CHANGELOG.md` | Modify | Record replication to standalone workflow |

## Verification
- Run `backend\venv\Scripts\python.exe agnostic_workflow/test_standalone_workflow.py -v`
- Run `backend\venv\Scripts\python.exe -m unittest backend/test_agnostic_research_report.py -v` (regression test)
