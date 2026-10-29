# QA Checklist: Vercel Deployment for Frontend & Backend

*Created: 2026-10-29T07:14:00+05:30*  
*Status: Pending Sign-Off*

## Quality Assurance Checklist

### 1. Backend Serverless Deployment
- [ ] `backend/api/index.py` correctly imports FastAPI `app` and resolves sys.path.
- [ ] `backend/vercel.json` rewrites all requests to `/api/index.py`.
- [ ] Backend deploys to Vercel without build failure.
- [ ] Live endpoint `GET /` returns status 200 with Swarm API version info.
- [ ] Live endpoint `GET /api/health` returns status 200 and lists active agents.
- [ ] Live endpoint `GET /api/agents` returns active agents roster.
- [ ] CORS middleware accepts requests from Vercel frontend domains.

### 2. Frontend Production Deployment
- [ ] `frontend/vercel.json` correctly identifies Next.js Framework.
- [ ] Frontend builds cleanly on Vercel (`npm run build`).
- [ ] Live frontend loads `/` with Linear theme styles intact.
- [ ] Live frontend loads `/agents` and displays active agent cards.
- [ ] Live frontend loads `/workflows` and allows workflow viewing.
- [ ] Live frontend successfully calls backend API endpoints over HTTPS without CORS errors.

### 3. Build & Regression
- [ ] Local backend test suite passes (`backend/test_endpoints.py`).
- [ ] Local frontend linting passes (`npm --prefix frontend run lint`).
- [ ] Local frontend build passes (`npm --prefix frontend run build`).
