# Feature: Linear Design System Revamp, Chat `/workflows` Slash Command & Rich Visual DAG Studio

*Created: 2026-10-28T19:58:00+05:30*

## Status

Completed (All Phases Implemented & Verified)

## Goal

1. **Fix and enrich chat `/workflows` invocation**: Enable instant opening of available workflows when typing `/workflows` or `/workflow` in the chat input, backed by an interactive floating slash command menu.
2. **Apply Linear Design System (`DESIGN.md`) across the entire application**: Align the frontend to the 570-line [`DESIGN.md`](../../DESIGN.md) specification — featuring the `#010102` deep dark canvas, four-step surface ladder (`#0f1011` to `#191a1b`), 1px `#23252a` hairline borders, signature `#5e6ad2` Linear lavender-blue accent, and negative-tracked typography.
3. **Build a Rich, Interactive Visual DAG Editor**: Elevate `@xyflow/react` in the Workflow Studio with custom `DataFlowEdge` components that visually indicate what data flows from block to block (`{{inputs.query}}`, `{{steps.<id>.output.text}}`), rich `StepNode` cards with agent personas, status indicators, and on-node action buttons, DAG auto-layout ("Tidy Up"), and a quick step inserter.

---

## Scope

### In Scope
- **Chat Slash Commands**:
  - Floating slash command suggestion menu (`/workflows`, `/agents`, `/clear`) in `ChatInput.tsx`.
  - Triggering `WorkflowPickerModal` on typing or submitting `/workflows` or `/workflow`.
  - Keyboard navigation for command suggestions.
- **Linear Design System Compliance (`DESIGN.md`)**:
  - `globals.css` and `tailwind.config.ts` token definitions (`canvas`, `surface-1` through `surface-4`, `hairline`, `primary` lavender `#5e6ad2`, `ink` typography).
  - Reskinning: Landing page (`/`), Chat page (`/chat`), Session sidebar, Message bubbles, Headers, Workflows dashboard (`/workflows`), Studio (`/workflows/[id]`), Shared view (`/workflows/share/[slug]`), and Login page (`/login`).
  - Replacing saturated decorative gradients with high-craft surface lift and hairline borders.
- **Rich Visual DAG Studio**:
  - `DataFlowEdge`: Custom edge rendering animated lavender path with data dependency badges indicating source-to-target payload variables.
  - `StepNode`: Rich card with agent persona badge, step index, live execution status, variable chips, tool/knowledge pills, and on-node actions (Test, Configure, Delete).
  - `GoalNode`: Styled root objective node with input parameters display and output data handle.
  - One-click topological DAG auto-layout ("Tidy Up").
  - Canvas quick step inserter toolbar button.
  - Custom dark Controls and MiniMap in `#0f1011` surface-1.

### Out of Scope
- Modifying backend PostgreSQL database schema (all graph edge data and step variables map cleanly to existing schema).
- Third-party canvas rendering engines (remains purely on `@xyflow/react`).

---

## Current Behavior

1. In `ChatInput.tsx`, typing `/workflows` or `/workflow` does not open the available workflows picker modal; submitting it sends a plain text message `/workflows` to the AI.
2. The current UI uses generic Tailwind colors and multi-palette themes (`slate`, `nebula`, etc.) with saturated gradients and drop shadows that do not conform to the strict `#010102` / `#0f1011` / `#5e6ad2` specification in `DESIGN.md`.
3. In `VisualGraphEditor.tsx`, the DAG canvas uses default React Flow nodes and edges without showing data flow connections, node execution telemetry, auto-layout, or quick insertion.

---

## Proposed Behavior

1. Typing `/` or `/work...` in `ChatInput.tsx` displays an animated, keyboard-navigable Linear command popover. Selecting `/workflows` or submitting `/workflow` immediately opens the available workflows launcher.
2. The entire application reflects `DESIGN.md` — dark `#010102` canvas, hairline borders (`#23252a`), four-step surface ladder, lavender-blue accent (`#5e6ad2`), and clean typography.
3. The visual DAG editor displays animated data flow connections showing exact variable flow between steps, rich step cards with agent avatars, status pills, on-node unit test triggers, and an auto-layout organizer.

---

## Files to Change

| File | Change | Reason |
| ---- | ------ | ------ |
| `frontend/tailwind.config.ts` | Update colors & radius | Add Linear design system tokens (`canvas`, `surface-1` to `surface-4`, `hairline`, `ink`, `lavender`). |
| `frontend/src/app/globals.css` | Update CSS variables | Define Linear `#010102` canvas and surface hierarchy tokens. |
| `frontend/src/app/chat/components/ChatInput.tsx` | Add command palette | Intercept `/workflow` and `/workflows` and show floating slash menu. |
| `frontend/src/app/chat/page.tsx` | Wire slash handler | Prevent sending raw slash command strings to backend. |
| `frontend/src/app/chat/components/SessionSidebar.tsx` | Reskin | Linear `#0f1011` surface-1 with `#23252a` hairline border and `#5e6ad2` active item. |
| `frontend/src/app/chat/components/ChatHeader.tsx` | Reskin | 56px height, `#010102` canvas, `#23252a` bottom rule, Linear typography. |
| `frontend/src/app/chat/components/MessageItem.tsx` | Reskin | Linear charcoal bubbles, JetBrains Mono code blocks, `#27a644` status badge. |
| `frontend/src/app/workflows/page.tsx` | Reskin | 56px navbar, surface-1 cards, pill tabs, `#5e6ad2` primary button. |
| `frontend/src/app/workflows/[id]/page.tsx` | Reskin | Studio tabs, panels, header, and toolbar matching Linear tokens. |
| `frontend/src/app/workflows/components/DataFlowEdge.tsx` | **[NEW]** Component | Animated Bezier edge with interactive data flow badge showing payload variables. |
| `frontend/src/app/workflows/components/VisualGraphEditor.tsx` | Enrich DAG Studio | Rich `GoalNode`, rich `StepNode`, data flow edges, auto-layout, and step inserter. |
| `frontend/src/app/page.tsx` | Reskin landing page | Complete Linear marketing canvas compliance (#010102, no rainbow gradients). |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Edge variable interpolation complexity | Low | Default to `{{steps.<id>.output.text}}` for step-to-step and `{{inputs.query}}` for goal-to-step. |
| Theme variable overrides | Medium | Centralize CSS variables in `globals.css` so existing Tailwind classes (`bg-card`, `bg-background`, `border-border`) resolve directly to Linear colors. |

---

## Verification

- `& "backend\venv\Scripts\python.exe" -u backend/test_endpoints.py`: All 25 tests pass.
- `npm --prefix frontend run lint`: Zero warnings or errors.
- `npm --prefix frontend run build`: Successful Next.js compilation.
