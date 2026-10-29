# Feature: Chat UX, Contextual Auto-Naming & Skeleton Polish

- **Date/Time**: 2026-10-29T14:00:00+05:30
- **Feature Slug**: `chat-ux-intelligence-polish`

## Status

Completed (2026-10-29T14:17:00+05:30)

## Goal

Deliver a refined, professional user experience across the chat interface and core studio modules by:
1. Automatically generating contextual conversation titles from user prompt intent.
2. Defaulting `/chat` to a clean new chat view without prematurely creating an empty sidebar session until the first message is sent.
3. Setting the default research agent model to Perplexity (`sonar`).
4. Using the authentic app brand logo (`BrandLogo`) for all AI chat messages instead of the generic bot icon.
5. Implementing polished skeleton loading states across the chat sidebar, message thread, workflows dashboard, and agents studio.
6. Updating the index/layout files: setting the brand favicon, comprehensive metadata, OpenGraph, Twitter cards, and SEO optimizations.
7. Deploying to Vercel production and verifying live health across both backend and frontend.

## Scope

- In scope:
  - **Contextual Conversation Auto-Naming**:
    - Backend: Add contextual title generator or auto-titling logic in `backend/app/main.py` that infers a clean 3-6 word title from the user prompt when creating or updating sessions.
    - Frontend: In `frontend/src/app/chat/page.tsx`, generate contextual title on first message dispatch and update session metadata.
  - **Lazy / On-Demand Session Creation**:
    - On loading `/chat`, default to an active new chat state (`activeSessionId = null`), without creating a blank "New Conversation" in the sidebar.
    - Clicking "New Chat" in `SessionSidebar` resets to the draft new chat state without calling `POST /api/sessions`.
    - Only when the user submits their first prompt does the session get created and added to the sidebar list.
  - **Perplexity as Default Research Model**:
    - Update `backend/app/agents/researcher/config.json` model to `"sonar"`.
    - Ensure Perplexity live web citation integration is active and has robust simulated fallbacks.
  - **AI Message Brand Logo**:
    - Update `frontend/src/app/chat/components/MessageItem.tsx` to render `<BrandLogo size={20} />` for agent messages.
    - Update `frontend/src/app/chat/page.tsx` in-flight loading bubble to render `<BrandLogo size={20} />`.
  - **Comprehensive Skeleton Loading States**:
    - `SessionSidebar.tsx`: Render 5 animated pulse skeleton items during `isLoadingSessions`.
    - `chat/page.tsx`: Render message thread skeletons when switching/loading sessions, and an animated skeleton stream in the in-flight processing bubble.
    - `workflows/page.tsx`: Render a responsive 6-card grid skeleton during `isLoading`.
    - `workflows/[id]/page.tsx`: Render a canvas studio skeleton during `isLoading`.
    - `agents/page.tsx`: Render a responsive 6-card agent roster skeleton during `isLoading`.
- Out of scope:
  - Modifying Supabase table schemas (existing columns `id`, `user_id`, `title`, `created_at`, `updated_at` are sufficient).

## Current behavior

1. When visiting `/chat`, if existing sessions exist, it automatically forces selection of `sessions[0]`, preventing a fresh chat view.
2. Clicking "New Chat" makes a network call `POST /api/sessions` creating a blank `"New Conversation"` item in the database and sidebar before any message is sent.
3. Conversation titles remain `"New Conversation"` unless manually edited.
4. The Research Agent default model in `backend/app/agents/researcher/config.json` is `"gemini-3.8-flash"`.
5. AI messages display a generic Lucide `<Bot />` icon.
6. Loading states show raw spinners (`<Loader2 className="animate-spin" />`) which cause layout shifts.

## Proposed behavior

1. Visiting `/chat` displays a clean new chat view (`activeSessionId = null`). The sidebar shows previously saved chats, but does not highlight or select one unless clicked.
2. Clicking "New Chat" clears the current dialogue to the initial prompt view with zero network requests and zero blank entries in the sidebar.
3. Submitting the first message triggers session creation with a smart title derived from the prompt (e.g. "PostgreSQL Execution Plan Analysis"), immediately inserting the session into the sidebar.
4. The Research Agent uses `"sonar"` (Perplexity) by default, providing live search sources and structured citations.
5. All AI message avatars render `BrandLogo` matching the app's brand mark.
6. Loading states across sidebar, message loading, workflow cards, and agent cards use modern skeleton pulses matching Linear and Vercel standards.

## Implementation steps

1. **Step 1: Contextual Title Generation & Perplexity Default Research Agent**
   - Update `backend/app/agents/researcher/config.json` model to `"sonar"`.
   - Implement title extraction in `backend/app/main.py` and frontend utility for auto-naming.
2. **Step 2: Lazy Session Creation on First Message**
   - Update `frontend/src/app/chat/page.tsx`:
     - Initialize with `activeSessionId = null` (draft new chat).
     - `handleCreateSession` clears chat without POSTing to `/api/sessions`.
     - In `handleSend`: Lazily create the session on the first message dispatch with contextual title.
3. **Step 3: AI Message Brand Logo Integration**
   - Replace `<Bot />` with `<BrandLogo size={20} />` in `MessageItem.tsx`.
   - Update in-flight thinking bubble in `chat/page.tsx` with `<BrandLogo size={20} />`.
4. **Step 4: Skeleton Loading UI Components**
   - Add session item skeletons in `SessionSidebar.tsx`.
   - Add conversation message skeletons in `chat/page.tsx`.
   - Add card grid skeletons in `workflows/page.tsx`.
   - Add card grid skeletons in `agents/page.tsx`.
   - Add canvas skeleton in `workflows/[id]/page.tsx`.
5. **Step 5: Layout Metadata, Favicon & SEO Enhancements**
   - Copy or generate brand `favicon.ico` / `icon.png` from `/swarm-logo.png`.
   - Update `frontend/src/app/layout.tsx` with full OpenGraph, Twitter card, robots, keywords, author, and themeColor metadata.
6. **Step 6: Testing, Build & Production Deployment Verification**
   - Build frontend (`npm run build`).
   - Run backend tests (`backend/test_endpoints.py` -> 34/34 passing).
   - Commit and push to `origin/main`.
   - Deploy backend/frontend to Vercel and verify live production health.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/agents/researcher/config.json` | Update | Set default model to `"sonar"` for Perplexity |
| `backend/app/main.py` | Update | Add contextual title generator for new conversations |
| `frontend/src/app/chat/page.tsx` | Update | Lazy session creation, contextual naming, brand logo in bubble, message skeletons |
| `frontend/src/app/chat/components/SessionSidebar.tsx` | Update | Skeleton loading list, zero-network new chat trigger |
| `frontend/src/app/chat/components/MessageItem.tsx` | Update | Replace `<Bot>` with `<BrandLogo>` for AI messages |
| `frontend/src/app/workflows/page.tsx` | Update | Skeleton grid for loading workflows |
| `frontend/src/app/workflows/[id]/page.tsx` | Update | Skeleton placeholder for studio canvas |
| `frontend/src/app/agents/page.tsx` | Update | Skeleton grid for loading agents |

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Title extraction latency | Delay in sending message | Synchronous fast title extraction on client/server (< 1ms); background refinement if needed |
| Race condition on fast double send in draft mode | Multiple sessions created | Lock in-flight session creation with a ref `isCreatingSessionRef` |
| Perplexity API key missing in local development | 500 error on researcher agent | Backend has built-in simulation fallback returning citations and sources |

## Verification

- `npm run build` succeeds with zero errors.
- `backend/test_endpoints.py` passes all 34 tests.
- Opening `/chat` presents fresh new chat; sidebar has no empty placeholder.
- Sending a message creates a session titled after the prompt in the sidebar.
- Researcher agent queries default to Perplexity Sonar.
- AI messages display `BrandLogo`.
- Skeleton loaders pulse smoothly during loading states.
