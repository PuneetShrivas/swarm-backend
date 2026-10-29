# Architectural Decision Record: Persistent Studio Sidebar, File Agents, Background Customizer & Artifacts Studio

- **Status**: Accepted
- **Datetime**: 2026-10-29T15:07:00+05:30
- **Scope**: Unified persistent collapsible sidebar, specialized file creation and ingestion agents, in-chat file artifact downloads, artifacts studio, interactive hover components, workspace canvas customization, and multi-resolution favicon generation.

---

## 1. Context & Problem Statement
Prior to this architectural enhancement:
1. The sidebar only existed inside `/chat` (`SessionSidebar.tsx`). The `/agents` and `/workflows` views lacked a sidebar, forcing users to navigate through the top header and obscuring recent execution runs or sessions.
2. Generating downloadable files required manual copy-pasting from chat code blocks. There were no specialized agents dedicated to code/file synthesis or document schema inspection and parsing.
3. The site's favicon was an old placeholder 25KB file cached aggressively by browsers.
4. Cards and interactive elements across chat, agents, and workflows were static with basic hover colors rather than modern creator-grade micro-interactions (e.g. spotlight tracking, spring hover physics).
5. The interface lacked background canvas customization (e.g., dotted or grid blueprints popular in modern AI workflow engines).
6. There was no centralized view to view, preview, copy, download, and manage persistent file artifacts created across sessions and workflows.

---

## 2. Decisions & Architecture

### 2.1 Unified Persistent Collapsible Sidebar (`AppUnifiedSidebar.tsx`)
- Created a single reusable sidebar component deployed across `/chat`, `/workflows`, `/agents`, and `/artifacts`.
- Built-in collapse toggle (`PanelLeftClose`/`PanelLeftOpen`) transitioning smoothly between `w-64` (full sidebar) and `w-14` (icon rail).
- Collapse state is saved to `localStorage` under `swarm_sidebar_collapsed`, ensuring the state is maintained consistently across page navigations.
- Segmented into collapsible groups:
  - **Conversations**: Search input, list of active chat sessions, inline titling, deletion, and quick "+ New Chat" button.
  - **Workflows & Runs**: User workflows list alongside a live feed of **Recent Workflow Runs** with real-time status dots (completed, running, failed), run duration, and token telemetry.
  - **Agents & Telemetry**: Active agent roster and telemetry turns.

### 2.2 Modular File Creation & Ingestion Agents
- Created `backend/app/agents/file_creator/`:
  - Specialized system prompt directing file artifact creation with structured metadata (filename, language/type, and content).
  - Tools for python, markdown, CSV, and shell script templates.
- Created `backend/app/agents/file_parser/`:
  - Specialized system prompt for document ingestion, schema validation, and data extraction.
  - Tools for JSON/YAML validation, table normalization, and text extraction.
- Natural language intent router routes file generation queries to `file_creator` and parsing queries to `file_parser`.
- Automatic turn analyzer (`extract_file_artifact_from_turn`) captures generated file blocks into persistent artifacts with UUIDs and stores them in memory/Supabase.

### 2.3 Artifacts Storage & API
- Added `artifacts` store in `backend/app/supabase.py` with methods `get_artifacts`, `save_artifact`, and `delete_artifact`.
- Exposed RESTful endpoints:
  - `GET /api/artifacts`: List all user-generated artifacts.
  - `POST /api/artifacts`: Create or register a file artifact.
  - `DELETE /api/artifacts/{id}`: Delete an artifact.
  - `GET /api/workflow-runs`: Retrieve recent workflow execution logs for sidebar telemetry.

### 2.4 Artifacts Studio (`/artifacts`) & In-Chat One-Click Downloads
- Created full-featured `/artifacts` page linked via `AppNavigationRail`.
- Features search, type filters (Code, Docs, Data, All), interactive spotlight cards, direct in-browser Blob download, code preview modal, and clipboard copy.
- Integrated download banner directly inside `MessageItem.tsx` for any chat message containing generated file artifacts.

### 2.5 Interactive Creator-Grade Hover Components
- Built `SpotlightCard.tsx`: Uses mouse coordinate tracking via radial gradients to render a subtle glowing border that follows the cursor.
- Built `InteractiveHoverButton.tsx`: Framer-motion powered button with spring hover physics and dynamic arrow expansion.
- Integrated into workflow cards, agent studio cards, and chat action chips.

### 2.6 Workspace Canvas Background Customizer
- Added `WorkspaceBackground` type (`plain`, `dots`, `grid`) to `ThemeProvider`.
- Added canvas selector in `ThemeSwitcher.tsx` with instant SVG pattern previews.
- Defined adaptive CSS patterns in `globals.css` that adjust opacity automatically based on whether dark or light mode is active.
- Persisted to `localStorage` (`swarm-background-pattern`).

### 2.7 True Multi-Resolution Favicon Generation
- Converted high-resolution `swarm-logo.png` into multi-resolution `.ico` (`16x16`, `32x32`, `48x48`, `64x64`) in both `src/app/favicon.ico` and `public/favicon.ico`.
- Added version query parameter (`?v=3`) to metadata icon tags in `layout.tsx` to bust browser cache immediately.

---

## 3. Consequences & Trade-offs
- **Pros**:
  - Seamless navigation and execution context across all workspace views.
  - Instant file downloads without copy-paste fatigue.
  - Professional, modern aesthetics with interactive micro-interactions and workspace personalization.
  - Immediate visual branding with crisp multi-resolution favicons.
- **Cons / Mitigations**:
  - Additional DOM elements for spotlight card gradient tracking; mitigated using pure CSS custom variables (`--mouse-x`, `--mouse-y`) without React state re-renders during mousemove.
