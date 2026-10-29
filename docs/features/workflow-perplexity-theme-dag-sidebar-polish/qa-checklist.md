# QA Checklist: Workflow Perplexity Integration, Dark Glacier Frost Default, DAG Editor Soft Theme Glow & Full-Height Collapsed Sidebar

- **Feature Slug**: `workflow-perplexity-theme-dag-sidebar-polish`
- **Datetime**: 2026-10-29T15:39:00+05:30
- **Status**: Passed

---

## Pre-Release QA Validation

- [x] **Perplexity Sonar for Workflows & Live Information Tasks**:
  - [x] AI workflow generator system instructions explicitly mandate assigning `researcher` or `sonar` for web search, stock prices, news, and market data.
  - [x] Fallback deterministic generator creates `Live Market & Stock Intelligence Pipeline` with `step_1` set to `sonar` / `researcher`.
  - [x] Step normalization automatically detects live keywords ("stock", "price", "ticker", "market", "search", "web", "live", "quote") and assigns `model: "sonar"`.
  - [x] Workflow execution engine `_execute_agent_turn` routes sonar steps to Perplexity's live completions endpoint with full citations.

- [x] **Dedicated Research Agent Perplexity Enforcement**:
  - [x] Queries directed to `researcher` or auto-routed to `researcher` always execute with `model = "sonar"`.
  - [x] Direct live inquiries ("What is the current stock price and ticker quote for AAPL?") route automatically to `researcher` via `route_agent`.

- [x] **Full-Height Studio Sidebars**:
  - [x] `/agents` page container updated to `flex flex-col h-screen overflow-hidden`, ensuring sidebar stretches 100% of viewport height below the navigation rail.
  - [x] `/workflows` page container updated to `flex flex-col h-screen overflow-hidden`.
  - [x] `/artifacts` page container updated to `flex flex-col h-screen overflow-hidden`.
  - [x] `AppUnifiedSidebar` uses `shrink-0 h-full` on both expanded and collapsed icon rail states.

- [x] **Default Theme as Dark Glacier Frost**:
  - [x] Default palette initialized to `"frost"` (Glacier Frost - cyan ice glow over abyssal arctic navy).
  - [x] Next.js `NextThemesProvider` defaults to `defaultTheme="dark"` with `enableSystem={false}`.
  - [x] Root `<html>` element in `layout.tsx` pre-rendered with `data-palette="frost"` and `className="dark"`.

- [x] **DAG Editor Visual Upgrades**:
  - [x] White outline and box-shadow removed from selected/focused nodes in `globals.css`.
  - [x] `GoalNode` and `StepNode` display soft, theme-adaptive glow (`shadow-[0_0_20px_-3px_var(--glow-color)]`) and `border-linear-primary ring-1 ring-linear-primary/40` on selection/hover.
  - [x] DAG canvas `<Background>` renders high-contrast, clearly visible dots in dark mode (`rgba(255, 255, 255, 0.2)` with `size={1.5}` and `gap={20}`).

- [x] **Collapsed Sidebar Sections by Default**:
  - [x] Initial state for accordion groups (`conversations`, `workflows`, `agents`) set to `false`.
  - [x] Sections smoothly expand and collapse on header click.

- [x] **Quality Gates**:
  - [x] All 42 backend unit & integration tests pass with 100% success rate.
  - [x] Next.js production build completes cleanly with zero errors.
