# Feature: Sidebar Conversations Loading & Artifacts Tab Persistence

## Status

In progress

## Date

2026-10-29T18:18:00+05:30

## Goal

Ensure that:
1. Conversations load in the sidebar on all pages (`/workflows`, `/agents`, `/artifacts`), and selecting a conversation navigates to `/chat` with that session loaded and active.
2. File artifacts generated in chat are persistently stored and visible in the Artifacts tab (`/artifacts`).

## Scope

- In scope:
  - Backend `GET /api/artifacts` query extraction from Supabase `chat_messages` (scanning message `metadata->file_artifact` and `metadata->artifacts`), plus `user_artifacts` table and memory store.
  - Backend `POST /api/artifacts` upserting to Supabase `user_artifacts` and memory store.
  - Frontend `AppUnifiedSidebar.tsx` fetching `/api/sessions` when `initialSessions` is not provided.
  - Frontend `chat/page.tsx` reading `useSearchParams().get("session")` and auto-selecting the session.
  - Frontend `chat/page.tsx` caching generated artifacts in `localStorage` and syncing with `POST /api/artifacts`.
  - Frontend `artifacts/page.tsx` merging backend artifacts with local browser storage.
  - Automated tests covering artifact persistence and extraction from chat messages.
- Out of scope:
  - Modifying Supabase database schema migrations (handled dynamically with table checking / try-catch).

## Current behavior

1. When on `/workflows`, `/agents`, or `/artifacts`, `AppUnifiedSidebar` receives `sessions={undefined}`. It does not fetch `/api/sessions`, so the Conversations section remains empty (`"No saved chats"`).
2. Clicking a conversation from another page directs to `/chat?session=<id>`, but `chat/page.tsx` does not read the `session` query parameter.
3. In `POST /api/chat`, artifacts are attached to message metadata and saved to `chat_messages` table in Supabase, but `memory_store.save_artifact` is in-memory only. On serverless Vercel, `GET /api/artifacts` only checks in-memory `memory_store`, so it returns an empty list `[]` to `/artifacts`.

## Proposed behavior

1. `AppUnifiedSidebar` fetches `/api/sessions` on mount whenever `initialSessions` is not provided, making conversations visible across all screens.
2. `chat/page.tsx` reads `useSearchParams().get("session")` and auto-activates that conversation when navigating from other screens.
3. `GET /api/artifacts` scans `chat_messages` for the user and extracts all artifacts from `metadata.file_artifact` and `metadata.artifacts`, as well as `user_artifacts` table and memory store.
4. `chat/page.tsx` syncs any generated file artifact to both `localStorage` and `POST /api/artifacts`.
5. `artifacts/page.tsx` merges backend artifacts with local browser artifacts, ensuring instant visibility for both authenticated and guest users.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/main.py` | Update `GET /api/artifacts`, `POST /api/artifacts`, `delete_artifact` to query/persist with Supabase `chat_messages` & `user_artifacts` | Serverless persistence of chat artifacts |
| `frontend/src/components/AppUnifiedSidebar.tsx` | Fetch `/api/sessions` when `!initialSessions` | Load conversations on non-chat pages |
| `frontend/src/app/chat/page.tsx` | Read `useSearchParams().get("session")` to auto-select session; sync artifacts to `POST /api/artifacts` and `localStorage` | Deep linking from sidebar; artifact sync |
| `frontend/src/app/artifacts/page.tsx` | Merge artifacts from `/api/artifacts` with `localStorage` | Resilience and instant visibility |
| `backend/test_endpoints.py` | Add unit tests for artifact extraction from chat messages and listing | Prevent regressions |

## Verification

- Automated tests: 57+ tests in `backend/test_endpoints.py`.
- Frontend build: `npm --prefix frontend run build`.
- Production testing: Verify live against Vercel deployment.
