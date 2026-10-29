# Feature: Default Workflow Template — Competitive Research & Report Pipeline

**Created**: 2026-10-29T16:13:00+05:30
**Updated**: 2026-10-29T16:13:00+05:30

## Status

Complete

## Goal

Provide all users with a production-quality default workflow template that demonstrates all block types (`agent`, `condition`, `python_code`, `loop`, `artifact`), uses multiple agents (`researcher`, `data_analyst`, `coder`, `reviewer`, `synthesizer`), and executes end-to-end. Seeded automatically at backend startup so every user can see, fork, and run it.

## Scope

- In scope:
  - Default workflow definition using 5+ agents and all 5 step types.
  - Seed at startup via `memory_store` (and optionally Supabase).
  - Dedicated `GET /api/workflows/defaults` endpoint for template discovery.
  - 4+ unit tests covering individual step types and E2E execution.
  - Feature documentation.
- Out of scope:
  - Frontend workflow template gallery (future enhancement).
  - Supabase migration schema changes (uses existing `workflows` table).

## Current behavior

No default or template workflows exist. Users must create workflows from scratch or use the AI generator.

## Proposed behavior

A "Competitive Product Research & Technical Report" pipeline with 8 steps is auto-seeded at startup with `visibility: "public"` and a known `share_slug: "default-research-pipeline"`. All users see it in their workflow list. A `GET /api/workflows/defaults` endpoint returns the default template(s).

## Implementation steps

1. Create `backend/app/workflows/default_workflows.py` with the workflow definition.
2. Add `seed_default_workflows()` function that inserts into `memory_store` if not already present.
3. Call `seed_default_workflows()` at FastAPI startup in `main.py`.
4. Add `GET /api/workflows/defaults` endpoint.
5. Add tests: default workflow exists, individual step unit tests, E2E run.
6. Documentation and changelog.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/default_workflows.py` | New file | Default workflow definition |
| `backend/app/main.py` | Add startup seed + defaults endpoint | Auto-seed and API discovery |
| `backend/test_endpoints.py` | Add 4+ tests | Verify correctness |
| `CHANGELOG.md` | Add entry | Track change |

## Interfaces

- `GET /api/workflows/defaults` → `List[Workflow]` — returns all default/template workflows.
- Default workflow uses `visibility: "public"`, `user_id: "system"`, `share_slug: "default-research-pipeline"`.

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Duplicate seeding on restart | Low — overwrites idempotently | Check existence before insert |
| Test environment conflicts | Low | Filter by known system user_id |

## Verification

- Unit tests: Step-level unit tests for python_code, condition, artifact blocks.
- Integration tests: E2E workflow execution with all steps.
- Manual checks: Workflow appears in GET /api/workflows list.
- Commands: `backend\venv\Scripts\python backend\test_endpoints.py`
