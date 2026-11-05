# QA Checklist: Standalone Agnostic Workflow Rate Limit Retry Replicate

## Datetime
`2026-11-05T14:30:45+05:30`

## Pre-Release QA Checks

- [x] **Rate Limit Delay Parsing**:
  - `parse_retry_delay` parses `"Please wait X seconds before retrying"`.
  - Floating seconds handling (`retry after 12.5 seconds`).
  - Exponential backoff fallback when no numeric wait is provided.
- [x] **Outer Cooldown Loop**:
  - Up to 5 outer rounds (`AZURE_MAX_RETRY_ROUNDS`) with progressive cooldown calculations and terminal progress countdowns.
- [x] **Non-Skipping Section Drafting**:
  - `_process_section` retries drafting up to 4 attempts (`DRAFT_MAX_RETRIES`) with backoff.
  - No premature `- Section drafting unavailable due to upstream error:` fallbacks on transient 429 errors.
  - Stage 3 synthesis retries up to 4 attempts (`SYNTH_MAX_RETRIES`).
- [x] **Zero App Dependencies Invariant**:
  - Strict verification that `agnostic_workflow/*.py` does not import `app.*`.
- [x] **Automated Test Coverage**:
  - 13/13 unit tests pass in `agnostic_workflow/test_standalone_workflow.py`.
  - 20/20 regression tests pass in `backend/test_agnostic_research_report.py`.
- [x] **Distribution Package Updated**:
  - `agnostic_workflow.zip` repacked with updated modules.
- [x] **Documentation Integrity**:
  - Feature plan, implementation log, verification report, and QA checklist completed with datetimes.
  - Architecture decisions recorded in `docs/decisions/standalone-workflow-rate-limit-retry/decisions.md`.
