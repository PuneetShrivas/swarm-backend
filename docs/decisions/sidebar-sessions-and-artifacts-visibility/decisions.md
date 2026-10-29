# Architectural Decisions: Sidebar Sessions Across Pages and Artifacts Tab Visibility

**Datetime:** 2026-10-29T18:28:40+05:30  
**Slug:** `sidebar-sessions-and-artifacts-visibility`  

## Context
1. **Sidebar Conversations on Non-Chat Screens**:
   The unified persistent sidebar was introduced to provide uniform navigation and resource discovery across `/chat`, `/workflows`, `/agents`, and `/artifacts`. However, `initialSessions` was only passed from `chat/page.tsx`. On other pages, `sessions` was left as an empty array, rendering `"No saved chats"`. Additionally, when clicking a conversation item from another screen, the user was routed to `/chat?session=<id>`, but `chat/page.tsx` lacked URL search param observation to load the requested conversation.
2. **Artifact Visibility in Artifacts Studio**:
   Chat sessions generate files (e.g. CSVs, Python scripts, JSON schemas) stored in `chat_messages.metadata`. On Vercel serverless deploys, the backend in-memory cache resets across invocations. As a result, `/artifacts` returned empty `[]` when only checking memory store, causing generated artifacts to appear missing.

## Decision 1: Self-Fetching Sidebar with Auth State Subscription
- Rather than forcing every parent page (`workflows`, `agents`, `artifacts`) to fetch and duplicate session management logic, `AppUnifiedSidebar` automatically fetches `/api/sessions` when `initialSessions` is not provided.
- Added a `supabase.auth.onAuthStateChange` subscription so that asynchronous session establishment seamlessly re-triggers `fetchData()`, ensuring conversations are displayed without requiring a manual page refresh.

## Decision 2: Deep-Linking Via Next.js Search Parameters & Suspense Boundary
- In `chat/page.tsx`, `useSearchParams` is used to capture `?session=<id>`.
- Wrapped `ChatContent` in `<Suspense>` to maintain Next.js App Router static optimization rules and prevent hydration bailout errors.
- As soon as auth credentials become available, `loadSessionMessages(urlSessionId, token)` is invoked, restoring the entire tree structure for that session.
- Used `window.history.replaceState` during session switches to keep the browser address bar up to date without triggering route re-renders.

## Decision 3: Dual-Layer Artifact Persistence and Collation
- **Client Cache**: Generated file artifacts in chat are stored in `localStorage` under `"swarm_local_artifacts"` (capped at 50 items).
- **Backend API Dispatch**: On chat turn completion, artifacts are dispatched to `POST /api/artifacts`.
- **Backend Collation**: `GET /api/artifacts` aggregates artifacts from:
  1. `memory_store.artifacts`
  2. `memory_store.messages`
  3. `user_artifacts` table in Supabase
  4. User's recent `chat_messages` metadata (`metadata.file_artifact` and `metadata.artifacts`)
- This ensures generated artifacts are immediately visible, persistent across serverless restarts, and robust for both authenticated and guest users.
