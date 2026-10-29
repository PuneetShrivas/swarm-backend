# Architectural Decision Record: Chat UX Intelligence, Lazy Session Creation & Skeleton Loaders

- **Status**: Accepted
- **Datetime**: 2026-10-29T14:15:00+05:30
- **Scope**: Chat session lifecycle, contextual titling, research agent Perplexity default, AI message branding, and skeleton loading feedback.

---

## 1. Context & Problem Statement
Prior to this enhancement:
1. Chat sessions created generic `"New Conversation"` titles unless manually edited by the user.
2. Opening `/chat` immediately selected the first saved conversation (or created an empty item), preventing a clean "new chat" landing view without cluttering the sidebar.
3. The research agent defaulted to `gemini-3.8-flash` instead of leveraging live Perplexity Sonar web search capabilities.
4. AI turns displayed a generic Lucide `<Bot>` icon instead of the unified hexagonal Swarm brand mark.
5. Loading states across chat sessions, workflow cards, agent rosters, and studio canvases displayed minimal spinners without layout preservation, causing visual layout shifts (CLS).
6. Application metadata, favicon, and SEO were minimal.

---

## 2. Decision & Architecture

### 2.1 Contextual Prompt-Based Auto-Titling
- Added `extract_contextual_title(prompt: str) -> str` to `backend/app/main.py`.
- Strips filler patterns (`"can you please help me with"`, `"explain how"`, `"what is"`), limits length to 3-6 words (<= 42 chars), and formats as title-case.
- Supported both on `POST /api/sessions` with `{ prompt: "..." }` and automatically during the first turn of generic sessions on `POST /api/chat`, propagating `session_title` via turn metadata.

### 2.2 Lazy Chat Session Creation
- Initial chat page mount sets `activeSessionId = null`, displaying an empty message input and starter inspiration chips.
- Clicking "+ New Chat" resets state to `activeSessionId = null` without making any network requests or creating empty sidebar entries.
- The session is created lazily on the first message send, immediately assigning the contextually extracted title and adding it to the sidebar.

### 2.3 Perplexity Sonar Default for Researcher Agent
- Configured `backend/app/agents/researcher/config.json` with `"model": "sonar"` and `temperature: 0.2`.
- Backend routes queries through Perplexity's live search API (`https://api.perplexity.ai/chat/completions`) when `PERPLEXITY_API_KEY` is present, extracting live citations and sources.

### 2.4 Brand Hero Logo on AI Messages
- Replaced `<Bot>` icons in `MessageItem.tsx` and in-flight bubble with `BrandLogo` (`/swarm-logo.png` with vector fallback).

### 2.5 Skeleton Feedback Across All Studio Views
- Implemented `animate-pulse` skeleton loaders matching layout geometry in:
  - `SessionSidebar.tsx` (conversation list skeleton)
  - `chat/page.tsx` (message thread skeleton on session load)
  - `workflows/page.tsx` (6-card workflow grid skeleton)
  - `agents/page.tsx` (6-card agent roster grid skeleton)
  - `workflows/[id]/page.tsx` (3-pane studio workspace skeleton)

### 2.6 Favicon, Metadata & SEO Enhancements
- Enriched `layout.tsx` with `metadataBase`, OpenGraph, Twitter card, robots, and keywords.
- Copied `/swarm-logo.png` to `icon.png` and `apple-icon.png`.
- Added dynamic `robots.ts` and `sitemap.ts`.

---

## 3. Consequences & Verification
- Zero regression on existing 34 backend endpoint and workflow tests (now 37 tests passing).
- Clean Next.js production build with zero ESLint/TypeScript errors.
- Improved First Contentful Paint (FCP) and Cumulative Layout Shift (CLS) perceived performance.
