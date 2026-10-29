# QA Checklist: Persistent Studio Sidebar, File Agents, Background Customizer & Artifacts Studio

- **Feature Slug**: `persistent-sidebar-file-agents-favicon`
- **Datetime**: 2026-10-29T15:06:00+05:30
- **Status**: Passed

---

## Pre-Release QA Validation

- [x] **Persistent Collapsible Studio Sidebar**:
  - [x] Renders consistently across `/chat`, `/workflows`, `/agents`, and `/artifacts`.
  - [x] Collapse toggle (`PanelLeftClose` / `PanelLeftOpen`) smoothly collapses sidebar to slim `w-14` icon rail.
  - [x] State is remembered in `localStorage` under `swarm_sidebar_collapsed` when navigating between routes.
  - [x] **Conversations Section**: Lists sessions with search filtering, active session highlighting, inline rename, and delete actions.
  - [x] **Workflows & Runs Section**: Collapsible section grouping user workflows and recent workflow runs with real-time status dots, durations, and token counts.
  - [x] **Agents & Telemetry Section**: Collapsible section displaying active agent roster and recent execution telemetry.

- [x] **Default File Creation & Ingestion Agents**:
  - [x] `file_creator` agent registered in registry with code generation and markdown template tools.
  - [x] `file_parser` agent registered in registry with JSON schema extraction and document analysis tools.
  - [x] Prompt intent classifier routes phrases like "create a file", "write a python script file", "generate csv" to `file_creator`.
  - [x] Prompt intent classifier routes phrases like "parse this file", "analyze csv", "extract schema" to `file_parser`.
  - [x] `extract_file_artifact_from_turn` captures generated code/text blocks into downloadable artifacts with UUIDs and persists to Supabase/memory store.

- [x] **In-Chat & Direct File Downloads**:
  - [x] Assistant messages containing file artifacts render a high-visibility download card with filename, syntax badge, and one-click download button.
  - [x] Clicking download triggers an in-browser Blob download without page navigation or reload.

- [x] **Artifacts Studio Page (`/artifacts`)**:
  - [x] Top navigation bar includes `Artifacts` tab with icon.
  - [x] Grid view showcases all generated artifacts using interactive `SpotlightCard` elements.
  - [x] Search filter instantaneously filters by title, filename, and content.
  - [x] Category pills filter by Code (`.py`, `.ts`, `.json`), Documents (`.md`), Data (`.csv`), or All.
  - [x] Quick actions on cards: View Details modal, Copy to Clipboard with animated checkmark, Download Blob file, and Delete artifact.
  - [x] Preview modal displays formatted syntax code block, metadata chips, line count, and download button.

- [x] **Interactive Creator-Grade Hover Components**:
  - [x] `SpotlightCard` tracks mouse position with radial gradient border glow across agent studio cards, workflow cards, and artifact cards.
  - [x] `InteractiveHoverButton` provides spring animation physics and progressive icon animations.
  - [x] All action buttons in chat, agents, and workflows respond with smooth hover lifts, active states, and focus rings.

- [x] **Workspace Background Pattern Customizer**:
  - [x] Theme dropdown includes "Workspace Canvas" selector with `Plain`, `Dots`, and `Grid` options.
  - [x] Selecting a pattern dynamically updates `data-background` attribute on `document.documentElement`.
  - [x] Selection persists across page refreshes via `localStorage` (`swarm-background-pattern`).
  - [x] High-contrast dots and grid lines adapt with appropriate opacity in both dark and light modes.

- [x] **Favicon Refresh & Cache Busting**:
  - [x] True multi-resolution `.ico` (`16x16`, `32x32`, `48x48`, `64x64`) generated into `frontend/src/app/favicon.ico` and `frontend/public/favicon.ico`.
  - [x] Version query string `?v=3` added in `layout.tsx` metadata to bust browser cache immediately.

- [x] **Quality & Regression Checks**:
  - [x] All 40 backend endpoint tests pass with 100% success rate.
  - [x] Next.js production build (`npm run build`) compiles cleanly with 0 TypeScript and ESLint errors.
