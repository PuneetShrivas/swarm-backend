# QA Checklist: Chat UX Intelligence, Lazy Sessions, Perplexity Default & Skeletons

- **Feature Slug**: `chat-ux-intelligence-polish`
- **Datetime**: 2026-10-29T14:16:30+05:30
- **Status**: Passed

---

## Pre-Release QA Validation

- [x] **Contextual Auto-Titling**:
  - [x] Initial user prompt strips conversational filler words and generates clean 3-6 word title.
  - [x] `POST /api/sessions` accepts `prompt` and resolves contextual title.
  - [x] `POST /api/chat` updates generic "New Conversation" session titles on the first turn.
  - [x] Updated title propagates into `session_title` metadata and synchronizes into sidebar list.

- [x] **Lazy Chat Session Creation**:
  - [x] Opening `/chat` defaults to clean new chat view (`activeSessionId = null`).
  - [x] Sidebar list does not display a blank or empty conversation item on load.
  - [x] Clicking "+ New Chat" resets conversation locally without creating an empty row in DB or sidebar.
  - [x] Sending first message automatically creates the session with contextual title and adds it to the sidebar.

- [x] **Research Agent Default to Perplexity**:
  - [x] `backend/app/agents/researcher/config.json` specifies `"model": "sonar"`.
  - [x] API queries to researcher route to Perplexity Sonar when API key is configured.
  - [x] Citations and web sources display in message metadata.

- [x] **Brand Logo on AI Messages**:
  - [x] All AI agent avatars in `MessageItem.tsx` render the Swarm brand mark (`BrandLogo`).
  - [x] In-flight reasoning bubble renders `BrandLogo`.
  - [x] Workflow execution step badges use `BrandLogo`.

- [x] **Skeleton Loading Feedback**:
  - [x] Sidebar displays 5 conversation skeleton bars while fetching sessions.
  - [x] Chat thread displays message skeleton cards while switching sessions.
  - [x] Workflows dashboard displays 6-card skeleton grid while fetching workflows.
  - [x] Agents dashboard displays 6-card agent roster skeleton grid while fetching agents.
  - [x] Workflow Studio displays 3-pane workspace skeleton while loading pipeline canvas.

- [x] **Favicon, Metadata & SEO**:
  - [x] `layout.tsx` metadata includes `metadataBase`, OpenGraph, Twitter card, robots, and keywords.
  - [x] Brand favicon is set to `/swarm-logo.png` via `icon.png` and `apple-icon.png`.
  - [x] `robots.ts` and `sitemap.ts` generate valid production SEO routes.

- [x] **Regression & Build Integrity**:
  - [x] All 37 backend endpoint and workflow tests pass cleanly.
  - [x] Next.js production build completes with zero errors.
