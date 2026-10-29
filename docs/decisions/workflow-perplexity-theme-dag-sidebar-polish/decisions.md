# Architectural Decision Record: Workflow Perplexity Integration, Dark Glacier Frost Default, DAG Editor Soft Theme Glow & Full-Height Collapsed Sidebar

- **Status**: Accepted
- **Datetime**: 2026-10-29T15:39:30+05:30
- **Scope**: Perplexity model routing for workflows and live tasks, research agent model enforcement, viewport layout locking for studio sidebars, default dark glacier frost theme configuration, DAG editor soft theme glow, and collapsed sidebar accordion default states.

---

## 1. Context & Problem Statement
Prior to this enhancement:
1. Workflows requiring real-time web discovery or stock prices did not reliably use Perplexity Sonar. The workflow execution engine in `backend/app/workflows/engine.py` only invoked Gemini, ignoring step-level requests for `sonar`.
2. Direct user queries for live stock prices or ticker data were not explicitly routed to the `researcher` agent.
3. On `/agents`, `/workflows`, and `/artifacts`, the outer page container used `min-h-screen`, causing the sidebar to not span full viewport height and allowing page-level window scrolling rather than independent inner pane scrolling.
4. The system defaulted to the monochrome `slate` palette rather than the branded `Glacier Frost` (`frost`) palette in Dark Mode.
5. In the visual DAG editor (`VisualGraphEditor.tsx`), selected cards rendered harsh pure white outlines and box shadows in dark mode, impairing text readability. Furthermore, canvas dots in dark mode used `#23252a`, which was virtually invisible on dark backgrounds.
6. The unified sidebar accordion opened with conversations and workflows expanded, which overwhelmed the navigation space on startup.

---

## 2. Decision & Architecture

### 2.1 Perplexity Integration in Workflow DAG Generation & Execution
- In `backend/app/ai_generator.py`, added a directive instructing LLM workflow generation to assign `model: "sonar"` and `agent_id: "researcher"` for any step involving web search, stock prices, ticker quotes, news, or live information. Added automatic step normalization to enforce this.
- Added a dedicated deterministic pipeline template (`Live Market & Stock Intelligence Pipeline`).
- In `backend/app/workflows/engine.py`, added Perplexity Sonar API execution directly to `_execute_agent_turn` with live citations and token tracking.

### 2.2 Research Agent & Live Query Model Enforcement
- In `backend/app/main.py`, expanded `research_keywords` to capture queries regarding stock prices, tickers, live market quotes, and web search.
- In `chat` endpoint, enforced that `chosen_model = "sonar"` whenever `selected_agent` is `researcher` or when the user's turn asks for live information or stock quotes.

### 2.3 Viewport Locking for Full-Height Studio Sidebars
- Changed the root container on `frontend/src/app/agents/page.tsx`, `workflows/page.tsx`, and `artifacts/page.tsx` from `min-h-screen` to `flex flex-col h-screen overflow-hidden`.
- Added `shrink-0` to both collapsed (`w-14`) and expanded (`w-64`) `<aside>` elements in `AppUnifiedSidebar.tsx`.
- The sidebar locks to 100% viewport height below the navigation rail, while the inner studio content panes scroll smoothly and independently with `overflow-y-auto h-full`.

### 2.4 Default Theme to Dark Glacier Frost
- Initialized `palette` state in `ThemeProvider.tsx` to `"frost"`.
- Set `defaultTheme="dark"` and `enableSystem={false}` in `NextThemesProvider`.
- Added `data-palette="frost"` and `className="dark"` to root `<html>` tag in `layout.tsx` to prevent FOUC.

### 2.5 Soft Theme Glow & Visible Dots in DAG Editor
- Overrode `.react-flow__node` in `globals.css` to disable harsh browser focus rings and default white outlines.
- Updated `GoalNode` and `StepNode` in `VisualGraphEditor.tsx` to accept React Flow's `selected` prop and apply `shadow-[0_0_20px_-3px_var(--glow-color)]` and `border-linear-primary ring-1 ring-linear-primary/40` on selection/hover.
- Updated `<Background>` in `VisualGraphEditor.tsx` to compute `canvasDotColor` via `useAppTheme()`: in dark mode, it renders `rgba(255, 255, 255, 0.2)` with `size={1.5}` and `gap={20}`, providing clean, crisp visibility.

### 2.6 Collapsed Sidebar Sections by Default
- In `AppUnifiedSidebar.tsx`, initialized `openSections` state to `{ conversations: false, workflows: false, agents: false }`.

---

## 3. Consequences & Verification
- All 42 modular backend unit/integration tests passed.
- Next.js production build succeeded with zero errors across all 14 routes.
