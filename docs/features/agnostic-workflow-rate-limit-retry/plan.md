# Feature: Agnostic Workflow Azure Rate Limit (HTTP 429) Retry & Non-Skipping Recovery

## Datetime
`2026-11-05T13:30:15+05:30`

## Status
Completed

## Goal
Fix section skipping and premature failures in `backend/app/workflows/agnostic_research_report/` when Azure Foundry rate limits (HTTP 429 / TPM token limits) occur. Ensure that the workflow parses exact cooldown wait times from upstream error payloads (`Please wait X seconds before retrying.`), waits progressively with visible progress updates, retries across multiple outer rounds, and never skips drafting or synthesis sections with inline error messages.

## Scope
- In scope:
  - Modify **ONLY** files under `backend/app/workflows/agnostic_research_report/`:
    - `backend/app/workflows/agnostic_research_report/roles.py`:
      - Implement regex extraction of suggested wait seconds from HTTP 429 error messages (e.g. `Please wait 8 seconds before retrying`).
      - Implement multi-round outer retry loops (`max_outer_rounds = 5`) with exponential backoff and progress feedback.
      - Handle TPM rate limits gracefully across models in the sequence.
    - `backend/app/workflows/agnostic_research_report/orchestrator.py`:
      - Wrap section drafting (`draft`), planning (`plan`), extraction (`extract`), and synthesis (`synthesize`) in section-level retry loops with exponential backoff instead of catching exceptions and appending error text like `Section drafting unavailable due to upstream error`.
      - Only fail if all retry attempts and cooldown rounds are completely exhausted.
  - Verification:
    - Unit tests in `backend/test_agnostic_research_report.py`.
    - Documentation in `docs/features/agnostic-workflow-rate-limit-retry/` and `docs/decisions/agnostic-workflow-rate-limit-retry/`.
    - Changelog update in `CHANGELOG.md`.
- Out of scope:
  - Modifying files outside `backend/app/workflows/agnostic_research_report/` (strictly per user request: "Make the changes only in the backend\app\workflows\agnostic_research_report path and not in other paths").

## Current behavior
1. When Azure Foundry returns HTTP 429 (`Rate limit of 8000 per 60s exceeded for UserByModelByMinuteOutputTokens. Please wait 8 seconds before retrying.`), `roles.py` sleeps for only 2s or 4s and only tries 2-3 times before raising `RuntimeError`.
2. When `run_role("draft", ...)` raises `RuntimeError`, `orchestrator.py` catches `Exception` and writes:
   `- Section drafting unavailable due to upstream error: Role 'draft' execution failed across models ['claude-opus-4-8']: Azure Foundry HTTP 429...`
   directly into the report markdown, skipping the section.

## Proposed behavior
1. `roles.py` extracts the recommended wait time from Azure's response (e.g. `Please wait X seconds before retrying`), adding a safety buffer (e.g., `+ 2.0s`).
2. `roles.py` implements an outer retry loop (`max_outer_rounds = 5`, default wait 20s-30s + dynamic parsing) with live progress logging (`⏳ [AZURE COOLDOWN] Role 'draft': waiting Xs for token quota reset...`).
3. `orchestrator.py` wraps section drafting and cross-section synthesis in persistent retry loops instead of catching errors and skipping sections with inline error bullets.

## Implementation steps
1. Create feature plan and decision documentation.
2. Update `backend/app/workflows/agnostic_research_report/roles.py` with:
   - Dynamic 429 retry-after / "Please wait X seconds" extraction.
   - Multi-round retry loop (`max_outer_rounds = 5`) with cooldown progress logging.
3. Update `backend/app/workflows/agnostic_research_report/orchestrator.py` with:
   - Section-level drafting retry mechanism so sections are never skipped on transient rate limits.
   - Synthesis-level retry mechanism.
4. Update unit tests in `backend/test_agnostic_research_report.py` to verify dynamic wait extraction, 429 retry behavior, and non-skipping drafting recovery.
5. Verify all tests pass cleanly.
6. Update documentation (`implementation.md`, `verification.md`, `qa-checklist.md`, `decisions.md`, `CHANGELOG.md`).
7. Commit and push.

## Files to change / create
| File | Change | Reason |
|---|---|---|
| `backend/app/workflows/agnostic_research_report/roles.py` | Modify | Add dynamic 429 wait extraction and multi-round cooldown loop |
| `backend/app/workflows/agnostic_research_report/orchestrator.py` | Modify | Retry drafting and synthesis instead of skipping sections with error text |
| `backend/test_agnostic_research_report.py` | Modify | Add tests for 429 wait extraction and drafting retries |
| `docs/decisions/agnostic-workflow-rate-limit-retry/decisions.md` | Create | Architecture decisions on rate limit cooldowns |
| `docs/features/agnostic-workflow-rate-limit-retry/*` | Create | Feature lifecycle documentation |
| `CHANGELOG.md` | Modify | Record rate limit recovery enhancements |

## Verification
- Run `backend/test_agnostic_research_report.py`
