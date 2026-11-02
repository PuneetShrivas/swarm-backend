# QA Checklist: DAG Editor Block Toolbar & Diagram Controls

**Datetime**: 2026-11-02T13:14:30+05:30  
**Feature**: `dag-editor-block-toolbar`  
**Status**: Ready for Production / Completed

## Visual Inspection Checklist

- [x] **Toolbar Attachment & Framing**:
  - [x] Attached toolbar is docked at the top of the DAG editor container.
  - [x] Background has dark glass blur (`bg-surface-1/95 backdrop-blur-md`) with hairline bottom border.
  - [x] Layout is cleanly aligned and doesn't overlap the diagram canvas area.

- [x] **Block Thumbnail Cards**:
  - [x] **Agent Step**: Displays Bot icon, lavender accent (`#5e6ad2`), LLM badge, and micro-prompt schematic.
  - [x] **Condition**: Displays GitBranch icon, amber accent (`#f59e0b`), BRANCH badge, and IF/True/False micro-lines.
  - [x] **Python Code**: Displays Terminal icon, emerald accent (`#10b981`), CODE badge, and `def execute()` micro-lines.
  - [x] **Loop Block**: Displays RotateCcw icon, cyan accent (`#06b6d4`), ITER badge, and loopback micro-lines.
  - [x] **Artifact**: Displays FileOutput icon, purple accent (`#a855f7`), FILE badge, and document micro-lines.
  - [x] Hover states show subtle lift and accent glow per `DESIGN.md`.

## Functional Interaction Checklist

- [x] **Adding Blocks via Toolbar**:
  - [x] Clicking any block thumbnail creates and appends the block to the DAG with proper predecessor connection.
  - [x] Dragging a block thumbnail onto the canvas drops and instantiates the block at the cursor location.
  - [x] The newly added block automatically opens its inline configuration form.

- [x] **Canvas & Viewport Controls**:
  - [x] **Tidy Up**: Re-aligns all nodes into organized topological levels.
  - [x] **Fit View**: Centers the diagram and zooms to show all nodes in the viewport.
  - [x] **Zoom In / Zoom Out**: Adjusts canvas zoom scale smoothly.
  - [x] **Grid Switcher**: Toggles canvas pattern (`Dots` → `Lines` → `Cross` → `Off`).
  - [x] **MiniMap Toggle**: Toggles MiniMap radar navigation window on and off.
  - [x] **Expand / Collapse All**: Expands all blocks for mass editing or collapses all to compact summary cards.

- [x] **Selection & Block Operations**:
  - [x] Selecting a node highlights its name in the toolbar selection badge.
  - [x] **Duplicate Selected**: Clones the active node with all instructions, scripts, tools, and connections preserved.
  - [x] **Delete Selected**: Deletes the selected node and cleanly removes references from successor nodes.
  - [x] **Unit Test Selected**: Launches isolated unit test runner for the selected block.
  - [x] **Test DAG**: Opens end-to-end system test modal.

## Regression & System Health

- [x] Production build passes with 0 errors (`npm --prefix frontend run build`).
- [x] All 11 agents in backend registry remain functional (`get_all()`).
- [x] Workflows studio tab switcher (Editor, Tools, Knowledge, Runs) functions normally.
- [x] Light and dark theme rendering conforms to Linear Design tokens.
