# Feature: Workflow Perplexity Integration, Dark Glacier Frost Default, DAG Editor Soft Theme Glow & Full-Height Collapsed Sidebar

- **Feature Slug**: `workflow-perplexity-theme-dag-sidebar-polish`
- **Datetime**: 2026-10-29T15:28:00+05:30

## Status

Complete (Implemented and verified across backend, frontend, tests, and deployment)

## Goal

1. **Perplexity for Workflows & Live Information**: Ensure workflow generation, step execution, and agent routing automatically use the Perplexity model (`sonar` / `sonar-pro`) for web search, stock price lookups, market quotes, news, and live information queries.
2. **Dedicated Perplexity Research Agent**: Ensure the `researcher` agent always uses the Perplexity model (`sonar`), both in direct chat turns and within workflow DAG executions.
3. **Full-Height Studio Sidebars**: Fix sidebar container geometry on `/agents`, `/workflows`, and `/artifacts` pages so the sidebar spans the entire 100% viewport height without layout truncation or page scroll issues.
4. **Default Theme to Dark Glacier Frost**: Default the initial application theme to Dark Mode with the `Glacier Frost` palette (`frost`) out of the box, with zero flash of unstyled theme on initial load.
5. **DAG Editor Theme Contrast & Canvas Dots**:
   - a) Replace harsh white glow/outlines on DAG cards with soft, theme-adaptive glow (`var(--glow-color)`) matching the active theme palette.
   - b) Fix the DAG editor canvas dots background so dots are clearly visible, crisp, and high-tech in dark mode (`rgba(255, 255, 255, 0.18)` / `size={1.5}` / `gap={20}`).
6. **Collapsed Sidebar Sections by Default**: Set Conversations, Workflows, and Agents accordion sections to collapsed (`false`) by default in `AppUnifiedSidebar.tsx`.

## Scope

- In scope:
  - `backend/app/main.py`: Update `route_agent` intent keywords to route web searches, stock prices, ticker queries, and live information to `researcher` / Perplexity. Enforce `model="sonar"` whenever `researcher` is queried or when prompt requests live information.
  - `backend/app/ai_generator.py`: Update `generate_workflow_spec` system instruction and deterministic fallbacks to mandate `sonar` / `researcher` for all web search, stock prices, and live data tasks.
  - `backend/app/workflows/engine.py`: Update `_execute_agent_turn` to call the live Perplexity Sonar API when executing steps that use `sonar`, `researcher`, or live information queries (with synthetic fallback in test mode).
  - `backend/app/agents/researcher/config.json`: Affirm `sonar` model configuration.
  - `frontend/src/app/agents/page.tsx`, `frontend/src/app/workflows/page.tsx`, `frontend/src/app/artifacts/page.tsx`: Fix outer layout from `min-h-screen` to `h-screen overflow-hidden` so `AppUnifiedSidebar` spans 100% viewport height and main panes scroll independently.
  - `frontend/src/components/AppUnifiedSidebar.tsx`: Ensure `shrink-0 h-full` on aside containers and set default accordion states (`conversations: false, workflows: false, agents: false`).
  - `frontend/src/components/ThemeProvider.tsx` & `frontend/src/app/layout.tsx`: Set default palette to `frost` and default theme to `dark`.
  - `frontend/src/app/workflows/components/VisualGraphEditor.tsx` & `frontend/src/app/globals.css`:
    - Remove harsh white outline/box-shadow from `.react-flow__node.selected`.
    - Apply soft theme-adaptive glow (`var(--glow-color)`) and border (`border-linear-primary ring-1 ring-linear-primary/40`).
    - Update `<Background>` dot color to high-contrast `rgba(255, 255, 255, 0.18)` in dark mode with `size={1.5}` and `gap={20}`.
- Out of scope:
  - Replacing the underlying `@xyflow/react` library.
  - Changing authentication schemas or unrelated billing endpoints.

## Current Behavior

1. Workflows created via AI or templates often defaulted to `gemini-3.8-flash` or `orchestrator` even for web search and stock price lookups.
2. Workflow step execution in `engine.py` only queried the Gemini API; it did not route to Perplexity even when step models were `sonar`.
3. The sidebar on `/agents`, `/workflows`, and `/artifacts` did not extend to full viewport height because outer pages used `min-h-screen` instead of `h-screen overflow-hidden`.
4. Theme defaulted to `slate` instead of `dark` + `frost`.
5. In the DAG editor, cards displayed harsh white glow/outline upon focus or selection, and dots background in dark mode was `#23252a` (nearly invisible against `#08090a`).
6. Sidebar accordion sections opened expanded (`conversations: true`, `workflows: true`) by default.

## Proposed Behavior

1. AI workflow generation explicitly instructs the model and deterministic fallbacks to assign `researcher` and `sonar` for all steps handling web search, stock prices, news, and live information.
2. Workflow execution engine queries Perplexity Sonar for live steps, returning live citations and sources.
3. All studio views use `h-screen overflow-hidden` with `shrink-0 h-full` sidebar.
4. Default palette is `frost` (Glacier Frost) with dark mode active out of the box.
5. DAG cards use soft, theme-adaptive glow (`var(--glow-color)`) without harsh white artifacts, and canvas dots are clearly visible in dark mode.
6. Sidebar sections (conversations, workflows, agents) start collapsed by default.

## Implementation Steps

1. **Step 1**: Backend Perplexity Integration in Workflow Generator, Execution Engine & Routing.
   - Update `ai_generator.py` for web search & stock price Perplexity step assignment.
   - Update `workflows/engine.py` with Perplexity API execution in `_execute_agent_turn`.
   - Update `main.py` routing keywords for stock prices and live information.
   - Add unit tests in `test_endpoints.py` to verify workflow step execution with Perplexity and intent routing.
2. **Step 2**: Layout & Full-Height Sidebar Fixes across Studio Pages.
   - Update `agents/page.tsx`, `workflows/page.tsx`, and `artifacts/page.tsx` containers to `h-screen overflow-hidden`.
   - Update `AppUnifiedSidebar.tsx` aside classes with `shrink-0 h-full` and default accordion states to all `false`.
3. **Step 3**: Dark Glacier Frost Default Theme & Initial State.
   - Update `ThemeProvider.tsx` and `layout.tsx` to default to `frost` and `dark`.
4. **Step 4**: DAG Editor Visual Upgrades (Soft Theme Glow & High-Contrast Canvas Dots).
   - Update `globals.css` with `.react-flow__node` soft glow overrides.
   - Update `VisualGraphEditor.tsx` with theme-aware soft glow node selection and visible dark mode canvas dots.
5. **Step 5**: Verification & Tests.
   - Run backend test suite (`test_endpoints.py`).
   - Run Next.js production build (`npm run build`).
6. **Step 6**: Documentation, Git Push & Production Deployment.
   - Complete `implementation.md`, `verification.md`, `qa-checklist.md`, `decisions.md`, `CHANGELOG.md`.
   - Push to `origin/main` and deploy backend to Vercel.

## Files to Change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/main.py` | Add live info & stock keywords to routing; ensure `researcher` always uses `sonar` | Req 1 & 2 |
| `backend/app/ai_generator.py` | Prompt & deterministic updates to assign `sonar` / `researcher` for websearch/stocks | Req 1 |
| `backend/app/workflows/engine.py` | Add Perplexity Sonar execution in `_execute_agent_turn` | Req 1 & 2 |
| `backend/test_endpoints.py` | Add tests 41 & 42 for Perplexity workflow step execution and stock price routing | Verification |
| `frontend/src/app/agents/page.tsx` | Change container to `h-screen overflow-hidden` | Req 3 |
| `frontend/src/app/workflows/page.tsx` | Change container to `h-screen overflow-hidden` | Req 3 |
| `frontend/src/app/artifacts/page.tsx` | Change container to `h-screen overflow-hidden` | Req 3 |
| `frontend/src/components/AppUnifiedSidebar.tsx` | Default `openSections` to all `false`; add `shrink-0 h-full` | Req 3 & 6 |
| `frontend/src/components/ThemeProvider.tsx` | Default palette to `"frost"` and theme to `"dark"` | Req 4 |
| `frontend/src/app/layout.tsx` | Set `data-palette="frost"` default attribute on `<html>` | Req 4 |
| `frontend/src/app/globals.css` | React Flow node outline/box-shadow soft glow override | Req 5a |
| `frontend/src/app/workflows/components/VisualGraphEditor.tsx` | Theme-aware node glow; high-contrast canvas dots in dark mode | Req 5a & 5b |

## Verification

- Backend tests: `backend\venv\Scripts\python backend\test_endpoints.py` (all tests passing)
- Frontend build: `npm --prefix frontend run build` (all routes passing cleanly)
- Live deployment: Deploy backend to Vercel, verify live health and endpoints.
