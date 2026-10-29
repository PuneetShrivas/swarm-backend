# Sidebar Sessions Across Pages and Artifacts Tab Visibility Implementation

**Datetime:** 2026-10-29T18:27:00+05:30  
**Feature Slug:** `sidebar-sessions-and-artifacts-visibility`  
**Status:** Complete  

## Overview
This feature resolves two related cross-page persistence and visibility issues:
1. **Sidebar Conversations on Non-Chat Pages**: On `/workflows`, `/agents`, and `/artifacts`, the unified persistent sidebar failed to display existing chat sessions, showing `"No saved chats. Start a new prompt."`. Furthermore, clicking a session link on those pages now navigates to `/chat?session=<id>` and automatically loads and restores that conversation's tree state.
2. **Artifact Visibility in Artifacts Studio**: File artifacts (such as generated CSVs, Python scripts, JSON schemas) created during chat sessions were not appearing in the `/artifacts` tab. This was due to serverless ephemeral memory restarts and lack of multi-source artifact collation. The fix persists artifacts to local client storage, dispatches them to `/api/artifacts`, and enables backend extraction from both `user_artifacts` and `chat_messages` metadata.

---

## Changes Implemented

### 1. Unified Persistent Sidebar (`frontend/src/components/AppUnifiedSidebar.tsx`)
- Added Step 0 in `fetchData`: when `!initialSessions || initialSessions.length === 0`, it fetches `/api/sessions` with the user's Supabase JWT authorization header.
- Added `supabase.auth.onAuthStateChange` subscription so that session restoration from cookies/local storage automatically triggers conversation and workflow fetching without page refresh.
- Preserved deep-linking behavior: clicking a conversation from `/workflows`, `/agents`, or `/artifacts` calls `router.push('/chat?session=' + s.id)`.

### 2. Chat Query Parameter Session Loader & Artifact Cache (`frontend/src/app/chat/page.tsx`)
- Imported `useSearchParams` and wrapped the main component in a Next.js App Router `<Suspense>` boundary.
- Added `useEffect` listening to `urlSessionId` (`searchParams?.get("session")`) and `session?.access_token`. When present, it automatically sets `activeSessionId` and calls `loadSessionMessages(urlSessionId, token)`.
- Updated `handleSelectSession` and `handleCreateSession` to use `window.history.replaceState` to maintain URL query cleanliness without reloading.
- In `requestSwarmResponse`, added dual artifact caching:
  1. Serializes `data.metadata.file_artifact` and `data.metadata.artifacts` to `localStorage.getItem("swarm_local_artifacts")`.
  2. Dispatches `POST /api/artifacts` so the artifact is indexed in memory and persisted in Supabase.

### 3. Artifacts Studio Aggregation & Sync (`frontend/src/app/artifacts/page.tsx`)
- Updated `fetchArtifacts` to read from `localStorage.getItem("swarm_local_artifacts")` and query backend `/api/artifacts`.
- Merges and deduplicates items by `id`, sorting newest first by `created_at`.
- Subscribes to `supabase.auth.onAuthStateChange` to re-fetch when session state transitions.
- In `handleDelete`, removes the artifact from local storage as well as issuing `DELETE /api/artifacts/{id}`.

### 4. Backend Multi-Source Artifact Collation (`backend/app/main.py`)
- Updated `list_artifacts`:
  1. Collects in-memory artifacts from `memory_store.get_artifacts(user_id)`.
  2. Collects file artifacts from in-memory chat messages in `memory_store.messages`.
  3. Queries Supabase `user_artifacts` table.
  4. Scans recent messages from Supabase `chat_messages` table and extracts any file artifacts stored in `metadata.file_artifact` and `metadata.artifacts`.
- Updated `create_artifact` and `delete_artifact` to handle both Supabase and memory stores.

### 5. Automated Regression Test Suite (`backend/test_endpoints.py`)
- Added Test 57: `Test Artifacts Persistence, Extraction & Studio Listing`.
- Verified `POST /api/artifacts`, `GET /api/artifacts`, and `DELETE /api/artifacts/{id}` lifecycle.
- All 57 tests passing cleanly.
