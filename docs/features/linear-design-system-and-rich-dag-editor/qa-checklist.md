# QA Checklist: Linear Design System Revamp, Chat `/workflows` Slash Command & Rich Visual DAG Studio

*Created: 2026-10-28T19:58:00+05:30*  
*Last Updated: 2026-10-28T20:14:00+05:30*  
*Status: Verified*

## Chat `/workflows` Slash Command
- [x] Typing `/` in chat input triggers the floating command palette menu.
- [x] Arrow keys and Enter select `/workflows`.
- [x] Selecting `/workflows` or typing `/workflow` / `/workflows` and pressing Enter opens `WorkflowPickerModal`.
- [x] Raw slash command is not dispatched as a chat prompt to backend.

## Linear Design System (`DESIGN.md`) Compliance
- [x] Page background uses `#010102` across all pages.
- [x] Cards and panels use `#0f1011` (`surface-1`) with 1px `#23252a` (`hairline`) borders.
- [x] Featured or elevated elements use `#141516` (`surface-2`).
- [x] Primary buttons and brand accents use `#5e6ad2` (`primary`) with `#828fff` hover and `#5e69d1` focus.
- [x] Typography uses Inter / SF Pro Display with measured negative letter-spacing on display headlines.
- [x] Button corners use 8px (`rounded.md`); cards use 12px (`rounded.lg`).
- [x] Status indicators use `#27a644` (`semantic-success`).
- [x] No saturated rainbow gradients or spotlight cards remain.

## Rich Visual DAG Studio
- [x] Canvas background renders `#010102` with `#23252a` dot matrix.
- [x] Nodes render with custom Linear charcoal styling.
- [x] `GoalNode` displays input parameters schema and output port.
- [x] `StepNode` displays agent avatar, step number pill, instructions snippet, and attached tool/doc chips.
- [x] Edges render as `DataFlowEdge` with animated lavender path and centered badges showing payload variables (`{{steps.<id>.output.text}}`, `{{inputs.query}}`).
- [x] "Tidy Up" button rearranges nodes hierarchically.
- [x] "+ Add Step" floating button adds a step directly into the canvas.
- [x] Play button on `StepNode` triggers isolated unit test and displays output.
- [x] MiniMap and Controls match charcoal panel styling.
