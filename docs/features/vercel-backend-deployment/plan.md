# Feature: Vercel FastAPI Backend Deployment

- **Date/Time**: 2026-10-29T13:13:00+05:30
- **Feature Slug**: `vercel-backend-deployment`

## Status

Completed (2026-10-29T13:20:00+05:30)

## Goal

Deploy the FastAPI backend correctly to Vercel under project `swarm-backend` (`https://vercel.com/puneet-shrivas-projects/swarm-backend`), ensuring all API routes (`/`, `/api/health`, `/api/agents`, `/api/chat`, `/api/workflows`, etc.) and OpenAPI documentation (`/docs`, `/openapi.json`) return valid responses without `404 Not Found` routing errors.

## Scope

- In scope:
  - Diagnose and resolve the cause of `{"detail": "Not Found"}` on `https://swarm-backend-lyart.vercel.app/`.
  - Remove legacy `backend/api/index.py` and faulty rewrite in `backend/vercel.json` that was intercepting all paths and passing `/api/index.py` to FastAPI.
  - Implement native zero-config FastAPI deployment structure:
    - Add top-level `backend/main.py` proxying `app.main:app` with path resolution.
    - Clean up `backend/vercel.json` or configure function settings if needed.
  - Verify all required Python dependencies in `backend/requirements.txt`.
  - Trigger production deployment using Vercel CLI (`vercel --prod --cwd backend`).
  - Verify live HTTP endpoints (`/`, `/api/health`, `/api/agents`, `/docs`) on `https://swarm-backend-lyart.vercel.app`.
  - Verify local automated test suite (`backend/test_endpoints.py`) passes without regressions.
- Out of scope:
  - Database schema changes in Supabase (environment variables are already provisioned on Vercel).
  - Frontend feature changes (only backend deployment configuration).

## Current behavior

When visiting `https://swarm-backend-lyart.vercel.app/` or `https://swarm-backend-lyart.vercel.app/api/health`, the server responds with:
```json
{"detail": "Not Found"}
```
Vercel CLI build warning confirmed:
`WARNING! Internal rewrites in backend framework projects now route requests using the rewritten destination path.`
Because `backend/vercel.json` rewrote `/(.*)` to `/api/index.py`, Vercel forwarded `/api/index.py` as the ASGI request path, which matches none of FastAPI's registered routes.

## Proposed behavior

1. Modern Vercel zero-config FastAPI entrypoint:
   - Provide clean `backend/main.py` exporting `app`.
   - Remove legacy `backend/api/index.py` and remove URL-corrupting `rewrites` from `backend/vercel.json`.
2. Requests to `https://swarm-backend-lyart.vercel.app/`:
   - Returns `{ "message": "Welcome to Swarm Backend API", "version": "2.0.0", ... }`.
3. Requests to `https://swarm-backend-lyart.vercel.app/api/health`:
   - Returns `{ "status": "ok", "agents_online": 7, ... }`.
4. Requests to `https://swarm-backend-lyart.vercel.app/docs`:
   - Renders interactive Swagger UI documentation.

## Implementation steps

1. **Step 1: Configure Clean Zero-Config Entrypoint & Clean Up Legacy Rewrites**:
   - Create `backend/main.py` importing `app` from `app.main`.
   - Remove legacy `backend/api/index.py`.
   - Update `backend/vercel.json` to zero-config or clean function configuration.
2. **Step 2: Deploy to Vercel Production**:
   - Run `vercel --prod --cwd backend` to trigger deployment to project `swarm-backend`.
3. **Step 3: Live Verification & Testing**:
   - Test live endpoints (`GET /`, `GET /api/health`, `GET /api/agents`, `GET /docs`).
   - Run backend test suite `backend/venv/Scripts/python backend/test_endpoints.py`.
4. **Step 4: Documentation & Sign-off**:
   - Create `verification.md` and `qa-checklist.md`.
   - Update `CHANGELOG.md` and architecture decisions.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/main.py` | New file | Standard top-level entrypoint for Vercel zero-config FastAPI |
| `backend/api/index.py` | Delete | Legacy function entrypoint that corrupted URL routing |
| `backend/vercel.json` | Delete or update | Remove faulty `rewrites` mapping `/(.*)` to `/api/index.py` |
| `backend/requirements.txt` | Update if needed | Ensure complete production dependencies |

## Interfaces

- Base URL: `https://swarm-backend-lyart.vercel.app`
- Endpoints: `GET /`, `GET /api/health`, `GET /api/agents`, `POST /api/chat`, `GET /docs`

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Vercel Serverless Function 15s/60s timeout on complex queries | Long multi-turn agent chats could time out | Ensure streaming or fast routing; configure `maxDuration: 60` if supported on Pro |
| Python path import issues in serverless environment | ModuleNotFoundError for `app.main` | `backend/main.py` explicitly adds `backend` to `sys.path` |

## Verification

- `Invoke-WebRequest -Uri "https://swarm-backend-lyart.vercel.app/"` -> HTTP 200 with API welcome JSON
- `Invoke-WebRequest -Uri "https://swarm-backend-lyart.vercel.app/api/health"` -> HTTP 200 with health JSON
- `backend/venv/Scripts/python backend/test_endpoints.py` -> 34 passed
