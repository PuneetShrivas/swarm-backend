# QA Checklist: Vercel FastAPI Backend Deployment

- **Feature Slug**: `vercel-backend-deployment`
- **Datetime**: 2026-10-29T13:20:00+05:30
- **QA Status**: Passed

---

## Pre-deployment Checklist

- [x] Removed legacy `backend/api/index.py` that caused path hijacking under modern Vercel CLI.
- [x] Removed faulty `backend/vercel.json` rewrites (`/(.*)` -> `/api/index.py`).
- [x] Created `backend/main.py` entrypoint exposing ASGI `app` instance with serverless `sys.path` injection.
- [x] Verified local module loading: `$env:PYTHONPATH="backend"; python -c "from main import app"`.
- [x] Full local test suite executed: `backend/test_endpoints.py` (34/34 passing).

---

## Post-deployment Verification Checklist

- [x] Production build and deployment succeeded on Vercel CLI v65 (`npx vercel@latest --prod --yes`).
- [x] Deployment aliased to production domain `https://swarm-backend-lyart.vercel.app`.
- [x] Root route `GET /` returns HTTP 200 with `supabase_connected: true` and `agents_count: 7`.
- [x] Health route `GET /api/health` returns HTTP 200 with `status: ok` and all 7 agents online.
- [x] Agents roster `GET /api/agents` returns HTTP 200 with all 7 agents configured with tools and `gemini-3.8-flash`.
- [x] Interactive OpenAPI documentation `GET /docs` returns HTTP 200 with interactive Swagger UI.
- [x] Environment variables on Vercel (`GEMINI_API_KEY`, `GEMINI_MODEL`, `SUPABASE_URL`, `SUPABASE_KEY`, `PERPLEXITY_API_KEY`, `PERPLEXITY_MODEL`) are active.

---

## Definition of Done Validation

- [x] Code follows repository conventions.
- [x] Tests cover new behavior and relevant regressions.
- [x] Feature documentation is created or updated (`plan.md`, `implementation.md`, `verification.md`, `qa-checklist.md`).
- [x] Architecture documentation updated in `docs/decisions/vercel-backend-deployment/decisions.md`.
- [x] A concise changelog entry exists in `CHANGELOG.md`.
- [x] Final summary lists changed files, tests, docs, and residual risks.
