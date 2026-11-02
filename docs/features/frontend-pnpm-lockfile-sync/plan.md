# Feature: Frontend pnpm Lockfile Sync and Vercel Deployment

## Status

Completed

## Goal

Resolve the Vercel frontend build failure (`ERR_PNPM_OUTDATED_LOCKFILE Cannot install with "frozen-lockfile" because pnpm-lock.yaml is not up to date with <ROOT>/package.json`) caused by missing lockfile updates when `remark-gfm` was added to `frontend/package.json`. Regenerate and synchronize `pnpm-lock.yaml`, verify local installation, lint, and build cleanly, eliminate lockfile ambiguity, and redeploy or trigger deployment on Vercel.

## Scope

- In scope:
  - Identify root cause: `remark-gfm` was added to `frontend/package.json` in commit `f4d6ce6` with `package-lock.json` updated but `pnpm-lock.yaml` left out of sync.
  - Install and synchronize `frontend/pnpm-lock.yaml` using `pnpm@9` so that `pnpm install --frozen-lockfile` succeeds.
  - Verify `pnpm run lint` and `pnpm run build` pass cleanly in `frontend/`.
  - Remove redundant/conflicting `package-lock.json` to prevent package manager divergence.
  - Document the fix and redeployment steps according to repository development standards.
- Out of scope:
  - Modifying application runtime features or UI components.
  - Backend schema or API endpoint changes.

## Current behavior

- `frontend/package.json` specifies `"remark-gfm": "^4.0.1"`.
- `frontend/pnpm-lock.yaml` is missing `remark-gfm` resolution and importers mapping.
- Vercel build runs `pnpm install --frozen-lockfile` on commit push, failing with:
  `ERR_PNPM_OUTDATED_LOCKFILE Cannot install with "frozen-lockfile" because pnpm-lock.yaml is not up to date with <ROOT>/package.json`.

## Proposed behavior

- `frontend/pnpm-lock.yaml` is fully synchronized with `frontend/package.json` matching lockfile version 9.
- `pnpm install --frozen-lockfile` executes without errors.
- `pnpm run build` generates Next.js production build artifacts cleanly.
- Deployment is re-triggered on Vercel.

## Implementation steps

1. Install `pnpm@9` locally and execute `pnpm install` in `frontend/` to update `pnpm-lock.yaml`.
2. Clean up conflicting `frontend/package-lock.json` so pnpm is consistently used.
3. Validate that `pnpm install --frozen-lockfile` succeeds cleanly.
4. Execute `pnpm run lint` and `pnpm run build` in `frontend/` to guarantee build safety.
5. Create and update feature documentation and changelog.
6. Commit changes and redeploy to Vercel.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `frontend/pnpm-lock.yaml` | Update | Synchronize lockfile with `frontend/package.json` including `remark-gfm` |
| `frontend/package-lock.json` | Remove | Remove conflicting lockfile generated accidentally with npm |
| `docs/features/frontend-pnpm-lockfile-sync/*` | Create | Feature documentation (plan, implementation, verification, qa-checklist) |
| `docs/decisions/frontend-pnpm-lockfile-sync/decisions.md` | Create | Architecture decision record for lockfile management |
| `CHANGELOG.md` | Update | Add changelog entry for bug fix |

## Interfaces

No API or UI interface changes.

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Outdated lockfile in CI/Vercel | Build failure blocking deployment | Regenerate lockfile with exact pnpm v9 and verify with `--frozen-lockfile` |
| Transitive dependency breakage | Build failure | Run full Next.js production build (`pnpm run build`) before committing |

## Verification

- Command: `cd frontend && pnpm install --frozen-lockfile` -> Exit code 0
- Command: `cd frontend && pnpm run lint` -> Exit code 0
- Command: `cd frontend && pnpm run build` -> Exit code 0
