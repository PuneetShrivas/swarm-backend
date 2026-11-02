# Architecture Decision Record: Single Lockfile Standard and pnpm Lockfile Sync

- **Status**: Accepted
- **Date**: 2026-11-02T09:41:00+05:30
- **Context**:
  In commit `f4d6ce6`, the package `remark-gfm` was added to `frontend/package.json` to enable GFM table and markdown features. During that change, `npm install` was run instead of `pnpm install`, producing an updated `frontend/package-lock.json` while leaving `frontend/pnpm-lock.yaml` unchanged.
  When deployed on Vercel, the Vercel build detected `pnpm-lock.yaml` and executed `pnpm install --frozen-lockfile`. This triggered `ERR_PNPM_OUTDATED_LOCKFILE`, failing the frontend deployment.
- **Decision**:
  1. Standardize frontend package management strictly on `pnpm` (lockfile version 9).
  2. Regenerate `frontend/pnpm-lock.yaml` using `pnpm install` so all declared dependencies in `package.json` are resolved.
  3. Remove `frontend/package-lock.json` to eliminate ambiguous multi-lockfile state and ensure all developers and CI pipelines use `pnpm`.
  4. Verify with `pnpm install --frozen-lockfile` and full Next.js production build (`pnpm run build`).
- **Consequences**:
  - Positive: Builds in CI/Vercel with `--frozen-lockfile` will reliably succeed.
  - Positive: Eliminates divergence between `npm` and `pnpm` lockfiles.
  - Neutral: Developers must use `pnpm` when adding or modifying dependencies in `frontend/`.
