# Architecture Decisions: Vercel FastAPI Backend Deployment

- **Slug**: `vercel-backend-deployment`
- **Date/Time**: 2026-10-29T13:20:00+05:30
- **Status**: Accepted

---

## Context
The Swarm FastAPI backend deployed to Vercel under project `swarm-backend` (`https://swarm-backend-lyart.vercel.app`) was failing with `{"detail": "Not Found"}` across all API routes (`/`, `/api/health`, `/api/agents`, `/docs`).

The root cause was the legacy Vercel Python serverless pattern:
1. `backend/api/index.py` was used as a single serverless function wrapper.
2. `backend/vercel.json` configured a wildcard rewrite: `{"source": "/(.*)", "destination": "/api/index.py"}`.
3. In modern Vercel CLI versions (v47+ / v65+), internal rewrites forward the rewritten destination path directly to the ASGI application scope (`scope["path"] = "/api/index.py"`).
4. FastAPI does not have an endpoint registered for `/api/index.py`, triggering FastAPI's internal `HTTPException(404, "Not Found")` for all incoming traffic.

---

## Decisions

### 1. Zero-Config Native FastAPI Deployment
- **Decision**: Migrate from legacy `api/*.py` single-function rewrites to Vercel's native zero-configuration FastAPI architecture.
- **Implementation**:
  - Deleted `backend/api/index.py` and removed the `backend/api/` folder.
  - Deleted `backend/vercel.json` rewrite rule.
  - Created top-level entrypoint `backend/main.py` which dynamically resolves the backend directory path in `sys.path` and exposes the ASGI `app` from `app.main:app`.
- **Rationale**: Vercel natively detects `main.py` or `app/main.py` when framework is Python/FastAPI, routing incoming HTTP request paths verbatim without internal rewrites.

### 2. Workspace Root Vercel CLI Execution Context
- **Decision**: Place the project link configuration `.vercel/project.json` at the repository root and run `npx vercel@latest --prod --yes` from the workspace root.
- **Rationale**: The Vercel project configuration on vercel.com specifies `rootDirectory: "backend"`. If `vercel` is invoked inside `backend/` with `--cwd backend`, Vercel attempts to resolve `backend/backend`, failing the build. Running from workspace root aligns perfectly with Vercel's Git deployment semantics.

---

## Consequences

- **Positive**:
  - All routes (`/`, `/api/health`, `/api/agents`, `/api/chat`, `/api/workflows`, `/docs`, `/openapi.json`) work cleanly with zero path mutation.
  - Interactive Swagger UI (`/docs`) and ReDoc are fully functional on production.
  - Local tests and remote behavior are 100% aligned.
  - Zero ongoing maintenance overhead for URL rewrite configurations in `vercel.json`.
- **Negative / Considerations**:
  - Vercel Serverless Functions have execution limits (15s on Hobby, 60s/300s on Pro). Long-running iterative agent chains should stream responses or be broken into discrete pipeline steps.
