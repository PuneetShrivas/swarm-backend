# Feature: Persistent Studio Sidebar, File Agents, Background Customizer, Artifacts Studio & Interactive Components

- **Date/Time**: 2026-10-29T14:38:00+05:30
- **Feature Slug**: `persistent-sidebar-file-agents-favicon`

## Status

Completed (All steps 1-6 implemented and verified)

## Goal

Deliver a comprehensive upgrade to the Swarm platform across navigation, interactive UI/UX, file tooling, workspace theming, and artifact asset management:
1. **Persistent Collapsible Sidebar Across Studio Views**: A unified, responsive sidebar across `/chat`, `/workflows`, and `/agents`, with collapse state persisted in `localStorage` (`swarm_sidebar_collapsed`). Grouped sections for:
   - Conversations (chat history, search, inline rename/delete).
   - Workflows & Workflow Runs (workflow templates and grouped execution runs with status and duration).
   - Agents & Agent Runs (active specialist roster and grouped execution telemetry runs).
2. **Built-in File Creation & Ingestion Agents**:
   - `file_creator`: Generates code, tabular CSV, Markdown docs, JSON schemas, or configuration files with direct in-chat **Download File** buttons.
   - `file_parser`: Ingests, parses, and validates uploaded documents, logs, and tabular data, extracting schemas, summary statistics, and AST trees.
3. **Interactive & Responsive UI Components**:
   - Integrate creator-grade interactive components (Aceternity UI / Magic UI inspired spotlight hover borders, spring physics action buttons, tool chip hover popovers, and interactive badge chips) across Chat, Agents, and Workflows screens.
4. **Workspace Background Customizer in Theme Toggle**:
   - Allow user to toggle between `plain`, `dots` (radial dot matrix), and `grid` (engineering DAG canvas grid).
   - Persist in `localStorage` (`swarm-background-pattern`) and apply dynamically via data attributes and CSS pattern variables.
5. **Artifacts Studio in Top Navigation (`/artifacts`)**:
   - Add **Artifacts** to `AppNavigationRail` alongside Chat, Agents, and Workflows.
   - Dedicated dashboard showcasing all generated files from workflows and chat sessions.
   - One-click actions: File Preview modal with syntax highlighting, File Download, Copy Content, and Delete.
6. **Favicon Overhaul & Cache Busting**:
   - Multi-size brand `.ico` assets (`16x16`, `32x32`, `48x48`, `64x64`) generated directly from `swarm-logo.png`.
   - Explicit versioned icon tags (`?v=2`) preventing browser caching issues.

## Scope

- In scope:
  - **Persistent Collapsible Sidebar (`AppUnifiedSidebar.tsx`)**:
    - Usable across `/chat`, `/workflows`, and `/agents`.
    - Supports expanded (`w-64`) and collapsed (`w-14`) states with header toggle button.
    - Persists state in `localStorage` (`swarm_sidebar_collapsed`).
    - Grouped collapsible sections: Conversations, Workflows & Runs, Agents & Runs.
  - **Default File Creation & Ingestion Agents**:
    - `backend/app/agents/file_creator/` and `backend/app/agents/file_parser/`.
    - Keyword heuristics in `route_agent` in `backend/app/main.py`.
    - Interactive file download button in `MessageItem.tsx`.
  - **Interactive Components**:
    - `SpotlightCard`: Interactive card with mouse-tracking hover spotlight border for agents and workflows.
    - `InteractiveHoverButton`: Spring-animated button with smooth scale and arrow animation.
    - Interactive tool popovers and copy-with-feedback chips in chat.
  - **Workspace Background Customizer**:
    - Extended `ThemeProvider.tsx` and `ThemeSwitcher.tsx` with `backgroundPattern` (`plain`, `dots`, `grid`).
    - Global pattern variables in `globals.css` with responsive dot/grid rendering.
  - **Artifacts Studio (`/artifacts`)**:
    - New backend endpoints: `GET /api/artifacts`, `POST /api/artifacts`, `DELETE /api/artifacts/{id}` in `backend/app/main.py`.
    - Dedicated page: `frontend/src/app/artifacts/page.tsx` with filtering, preview modal, and direct downloads.
    - Added `Artifacts` tab in `AppNavigationRail.tsx`.
  - **Favicon & SEO**:
    - Replaced `src/app/favicon.ico` and `public/favicon.ico`.
    - Cache-busting icon definitions in `layout.tsx`.

## Current behavior

1. Sidebar only exists on `/chat` with a fixed 256px width, and cannot be collapsed.
2. `/workflows` and `/agents` have no sidebar and no grouped runs view.
3. No built-in agents specialized in generating downloadable files or parsing files with download buttons.
4. Workspace background is fixed to solid color without pattern customization.
5. No centralized Artifacts view in top navigation to manage generated files.
6. Favicon cached or loading old icon on some browsers.

## Proposed behavior

1. Unified persistent sidebar on `/chat`, `/workflows`, and `/agents` with smooth collapse/expand and grouped runs history.
2. High-performance `file_creator` and `file_parser` agents producing downloadable file cards with one-click download.
3. Interactive spotlight cards and spring buttons across chat, workflows, and agents.
4. Theme switcher includes interactive Workspace Background picker (Plain, Dots, Grid).
5. Top navigation features an **Artifacts** tab leading to a rich file management and preview studio.
6. Multi-resolution brand favicon active with cache busting.

## Implementation steps

1. **Step 1: Favicon Refresh & Background Customizer in ThemeSwitcher**:
   - Update `ThemeProvider.tsx`, `ThemeSwitcher.tsx`, and `globals.css` with background pattern modes (`plain`, `dots`, `grid`).
   - Confirm versioned favicon references in `layout.tsx`.
2. **Step 2: File Creation & Ingestion Agents + Artifacts Backend Endpoints**:
   - Create `file_creator` and `file_parser` agent packages.
   - Add `/api/artifacts` endpoints and memory store persistence in `backend/app/main.py`.
   - Update `route_agent` intent routing.
3. **Step 3: Interactive UI Components (Spotlight & Spring Buttons)**:
   - Create `SpotlightCard.tsx` and `InteractiveHoverButton.tsx`.
   - Enhance agent cards, workflow cards, and chat message action chips with hover spotlight and spring physics.
   - Add in-chat Download File button in `MessageItem.tsx`.
4. **Step 4: Unified Persistent Collapsible Sidebar (`AppUnifiedSidebar.tsx`)**:
   - Create `AppUnifiedSidebar.tsx` with `localStorage` persistence and grouped sections.
   - Integrate into `/chat`, `/workflows`, and `/agents`.
5. **Step 5: Artifacts Studio Page (`/artifacts`) & Navigation**:
   - Create `frontend/src/app/artifacts/page.tsx` with file cards, preview modal, copy, and download actions.
   - Add `Artifacts` tab to `AppNavigationRail.tsx`.
6. **Step 6: Verification, Production Build & Vercel Push**:
   - Add tests to `backend/test_endpoints.py` covering new agents and artifacts API.
   - Validate `npm run build` and endpoint tests.
   - Commit, push to `origin/main`, deploy to Vercel, and verify production endpoints.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `frontend/src/components/ThemeProvider.tsx` | Add background pattern state & persistence | Background customizer |
| `frontend/src/components/ThemeSwitcher.tsx` | Add Plain / Dots / Grid background options | Background customizer |
| `frontend/src/app/globals.css` | Define CSS patterns for dots and grid | Background customizer |
| `backend/app/agents/file_creator/*` | Create file creation agent | File creation requirement |
| `backend/app/agents/file_parser/*` | Create file parser agent | File parser requirement |
| `backend/app/main.py` | Add `/api/artifacts` endpoints and routing | Artifacts & File agents |
| `frontend/src/components/ui/SpotlightCard.tsx` | Create creator-grade interactive spotlight card | Interactive elements |
| `frontend/src/components/ui/InteractiveHoverButton.tsx` | Create spring-animated interactive button | Interactive elements |
| `frontend/src/app/chat/components/MessageItem.tsx` | Add Download File button & interactive actions | File download requirement |
| `frontend/src/components/AppUnifiedSidebar.tsx` | Create persistent collapsible sidebar | Persistent sidebar requirement |
| `frontend/src/app/chat/page.tsx` | Integrate `AppUnifiedSidebar` | Persistent sidebar requirement |
| `frontend/src/app/workflows/page.tsx` | Integrate `AppUnifiedSidebar` and `SpotlightCard` | Persistent sidebar requirement |
| `frontend/src/app/agents/page.tsx` | Integrate `AppUnifiedSidebar` and `SpotlightCard` | Persistent sidebar requirement |
| `frontend/src/components/AppNavigationRail.tsx` | Add `Artifacts` tab | Artifacts section requirement |
| `frontend/src/app/artifacts/page.tsx` | Build Artifacts Studio dashboard | Artifacts section requirement |
| `backend/test_endpoints.py` | Add test cases for artifacts and file agents | Definition of Done |

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Dynamic background patterns causing performance lag | GPU/rendering strain | Pure CSS radial and linear gradient patterns without canvas re-renders |
| Sidebar collapse transition causing layout shift | Visual flicker | Synchronous `localStorage` read before hydration with fallback |
| In-browser large file downloads | Memory spike | Blob object URL release via `URL.revokeObjectURL` |

## Verification commands

- Backend Tests: `backend\venv\Scripts\python backend\test_endpoints.py`
- Frontend Build: `cd frontend; npm run build`
- Vercel Deploy: `npx vercel@latest --prod --yes`
