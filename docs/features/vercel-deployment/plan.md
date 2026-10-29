# Feature: Vercel Deployment for Frontend & Backend

*Created: 2026-10-29T07:14:00+05:30*  
*Status: In progress*

## Goal

Configure, package, deploy, and verify both the Next.js frontend and FastAPI backend onto Vercel, providing production URLs with automated builds, proper environment variable handling, serverless routing, and cross-origin resource sharing (CORS).

---

## Scope

### In Scope
- **Backend Deployment Configuration**:
  - Create `backend/api/index.py` acting as the Vercel serverless ASGI entry point importing `app` from `app.main`.
  - Create `backend/vercel.json` configuring rewrites to `/api/index.py`, memory allocation, and function timeouts.
  - Update `backend/requirements.txt` to include explicit `httpx` and verified dependencies for serverless packaging.
  - Update CORS middleware in `backend/app/main.py` to allow `allow_origin_regex=r"https://.*\.vercel\.app"`.
- **Frontend Deployment Configuration**:
  - Configure `frontend/vercel.json` and build settings for Next.js 14 App Router.
  - Configure `NEXT_PUBLIC_API_URL` to route requests to the deployed backend Vercel URL.
  - Configure `frontend/next.config.mjs` with rewrites fallback if needed.
- **Vercel CLI Orchestration**:
  - Deploy `swarm-backend` project to Vercel via Vercel CLI (`vercel --prod`).
  - Capture production backend URL (e.g. `https://swarm-backend-xxx.vercel.app`).
  - Deploy `swarm-frontend` project to Vercel via Vercel CLI (`vercel --prod`) with `NEXT_PUBLIC_API_URL` set to the live backend URL.
  - Capture production frontend URL (e.g. `https://swarm-frontend-xxx.vercel.app`).
- **End-to-End Verification**:
  - Live probe of `GET /api/health` and `GET /api/agents` on the deployed backend URL.
  - Live probe of `/` and `/agents` on the deployed frontend URL.

### Out of Scope
- Custom domain DNS record acquisition (deployments will use Vercel's secure `*.vercel.app` domains).
- Database migration (Supabase is cloud-hosted and already accessible from Vercel).

---

## Current Behavior

- Neither the frontend nor backend have Vercel deployment manifests (`vercel.json` or `api/index.py` serverless wrappers).
- Frontend defaults `NEXT_PUBLIC_API_URL` to `http://localhost:8000`.
- Backend CORS configuration only specifies `allow_origins=["*"]` without explicit `allow_origin_regex` for secure Vercel preview/production domains.
- No project links exist in `.vercel`.

---

## Proposed Behavior

1. **Backend Serverless Package**:
   - `backend/api/index.py` exposes the FastAPI ASGI application to Vercel's Python runtime.
   - `backend/vercel.json` routes all incoming requests `/(.*)` to the serverless function.
   - Deployed as `swarm-backend` on Vercel.
2. **Frontend Production Deployment**:
   - `frontend/` builds Next.js with environment variables `NEXT_PUBLIC_API_URL` pointing to the live `swarm-backend` Vercel deployment.
   - Deployed as `swarm-frontend` on Vercel.
3. **Automated Verification**:
   - Test endpoints live over HTTPS to verify health, agents roster, and web application routing.

---

## Implementation Steps

1. **Phase 1: Backend Serverless Configuration & Dependencies**:
   - Create `backend/api/index.py` with `sys.path` resolution and ASGI import.
   - Create `backend/vercel.json` with serverless rewrite routing.
   - Update `backend/requirements.txt` with explicit `httpx`.
   - Update CORS in `backend/app/main.py` with `allow_origin_regex=r"https://.*\.vercel\.app"`.
   - Run backend test suite to ensure local regression-free status.
2. **Phase 2: Backend Vercel Deployment**:
   - Run `vercel deploy --prod` within `backend/` directory.
   - Extract live backend production URL.
   - Probe live backend endpoints (`/`, `/api/health`, `/api/agents`).
3. **Phase 3: Frontend Vercel Configuration & Deployment**:
   - Create `frontend/vercel.json`.
   - Run `vercel deploy --prod` within `frontend/` directory with `NEXT_PUBLIC_API_URL=<backend_url>`.
   - Extract live frontend production URL.
   - Probe live frontend pages.
4. **Phase 4: Full Validation & Documentation**:
   - Verify live cross-communication between deployed frontend and backend.
   - Update `verification.md`, `qa-checklist.md`, `implementation.md`, and `CHANGELOG.md`.
   - Commit and push to git.

---

## Files to Change

| File | Change | Reason |
| :--- | :--- | :--- |
| `backend/api/index.py` | New file | Vercel Serverless Function entry point for FastAPI ASGI app |
| `backend/vercel.json` | New file | Vercel deployment manifest and rewrite routing |
| `backend/requirements.txt` | Add `httpx` | Ensure serverless packaging bundles all network utilities |
| `backend/app/main.py` | Add `allow_origin_regex` | Ensure Vercel frontend domains can communicate via CORS |
| `frontend/vercel.json` | New file | Vercel deployment manifest for Next.js app |
| `CHANGELOG.md` | Add entry | Document Vercel deployment support |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| Cold starts on Vercel Python serverless function | Initial request delay (1-2s) | Lightweight `backend/api/index.py` entry point with lazy agent module loading |
| Missing environment variables on Vercel backend | Authentication or AI generation failure | Set environment variables (`GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, etc.) in Vercel project configuration or CLI |
| CORS rejection on frontend API calls | Blocked fetch in browser | Configured `allow_origin_regex=r"https://.*\.vercel\.app"` and credentials support in FastAPI |
