# Feature: DAG Editor Block Toolbar & Diagram Controls

**Datetime**: 2026-11-02T13:14:45+05:30  
**Status**: Complete

## Goal

Design and implement an attached, comprehensive toolbar for the DAG editor (`VisualGraphEditor.tsx`) that:
1. Enables users to pick and use blocks (Agent, Condition, Python Code, Loop, Artifact) directly from the toolbar via both one-click addition and intuitive drag-and-drop onto the canvas.
2. Displays properly labelled block items equipped with stylized miniature visual thumbnails showing block type accents, iconography, and schematic structure.
3. Provides essential canvas and diagram controls to operate the DAG editor (Tidy Up auto-layout, Fit View, Zoom In/Out, Grid switcher, MiniMap toggle, Read-Only lock).
4. Provides block management operations (Expand All / Collapse All, Duplicate Selected Block, Delete Selected Step/Edge, Unit Test Selected Block, and System Test DAG trigger).

## Scope

- In scope:
  - Creation of a dedicated `DAGToolbar.tsx` component adhering strictly to `DESIGN.md` (Linear design tokens, `#010102` canvas, `#0f1011` surface-1, `#5e6ad2` primary accent, hairline borders).
  - 5 Rich Block Thumbnails with distinctive accents, labels, and schematic micro-previews:
    - **Agent Step** (Bot icon, `#5e6ad2` lavender accent, LLM prompt badge)
    - **Condition Branch** (GitBranch icon, `#f59e0b` amber accent, IF / True / False routes)
    - **Python Code** (Terminal icon, `#10b981` emerald accent, Sandboxed script preview)
    - **Loop Block** (RotateCcw icon, `#06b6d4` cyan accent, Iteration counter & loopback)
    - **Artifact Generator** (FileOutput icon, `#a855f7` purple accent, Markdown / report file)
  - Both Click-to-Add and Drag-and-Drop placement using ReactFlow's `screenToFlowPosition`.
  - Comprehensive DAG controls:
    - Auto-Layout ("Tidy Up")
    - Canvas Fit View & Smooth Zoom Controls
    - Grid background style switcher (`Dots`, `Lines`, `Cross`, `Off`)
    - MiniMap visibility toggle
    - Global Expand All / Collapse All node configuration views
    - Duplicate selected block with parameter preservation
    - Delete selected block or edge
    - System test trigger & Unit test trigger for selected block
- Out of scope:
  - Modifying backend workflow execution engine (already verified and working).
  - Backend database schema changes.

## Current behavior

1. Block addition is hidden inside a small dropdown menu (`showBlockPalette` boolean toggle) anchored at `top-3 left-3` inside the canvas.
2. The items in the dropdown are plain text rows with a small icon, lacking visual thumbnails and physical prominence.
3. Canvas controls are fragmented: ReactFlow default `Controls` and `MiniMap` sit in standard corners without higher-level layout commands (e.g., no Fit View button in the toolbar, no global Expand/Collapse all nodes, no Duplicate selected block button, no Grid switcher).
4. Users cannot drag and drop blocks into specific canvas positions; new blocks are always sequentially appended at the end of the step list.

## Proposed behavior

1. **Attached Toolbar Header**:
   - The DAG editor features an attached top control bar docked seamlessly to the top of the canvas card.
   - Designed with Linear design language: dark glass surface (`bg-surface-1/95 backdrop-blur-md`), hairline borders (`border-hairline`), refined typography (`font-mono`, `text-ink`, `text-ink-subtle`).
2. **Visual Thumbnail Block Picker Tray**:
   - Prominently positioned within the attached toolbar or expandable shelf.
   - Each of the 5 block types is presented as a high-fidelity miniature thumbnail card:
     - Distinct color accent badges (Lavender, Amber, Emerald, Cyan, Purple).
     - Miniature schematic diagram previewing the block's internal layout and handles.
     - Clear titles, subtitles, and badges.
   - Dual-interaction support:
     - **Click to Add**: Automatically appends the block to the workflow DAG and organizes layout.
     - **Drag-and-Drop**: Users drag a thumbnail card and drop it onto the canvas at the exact target location.
3. **Diagram & Canvas Controls**:
   - **Tidy Up**: Auto-organizes DAG nodes into topological hierarchy layers with smooth transition.
   - **Fit View**: Centers and scales the diagram to fit the current viewport.
   - **Zoom Controls**: Zoom in, Zoom out, and zoom level indicator.
   - **Grid Switcher**: Toggle canvas background between Dots, Lines, Cross, and Plain.
   - **MiniMap Toggle**: Instantly show or hide the radar minimap.
   - **Expand/Collapse All**: Toggle all block nodes between compact summary badges and full inline editor forms.
4. **Block Manipulation Controls**:
   - **Duplicate Selected**: Clones the active node with unique ID, offset position, and identical properties.
   - **Delete Selected**: Deletes currently highlighted node or edge with confirmation safety.
   - **Unit Test Selected**: Runs isolated execution on the selected block.
   - **Test DAG**: Opens end-to-end system test modal.

## Implementation steps

1. **Step 1: Create `DAGToolbar.tsx` Component**:
   - Build modular toolbar component in `frontend/src/app/workflows/components/DAGToolbar.tsx`.
   - Render 5 labelled block thumbnail cards with micro-schematics, hover states, drag handles, and click handlers.
   - Implement canvas control button clusters (Tidy Up, Fit View, Zoom In/Out, Grid switcher, MiniMap toggle, Expand/Collapse All).
   - Implement block action cluster (Duplicate Selected, Delete Selected, Unit Test Selected, Test DAG).
2. **Step 2: Upgrade `VisualGraphEditor.tsx` with Attached Toolbar & Canvas Drop Handling**:
   - Integrate `DAGToolbar` as an attached top header bar.
   - Implement React Flow Drag-and-Drop handlers (`onDragOver`, `onDrop` using `reactFlowInstance.screenToFlowPosition`).
   - Upgrade node expansion state to `expandedNodeIds: Set<string>` for multi-node / Expand All / Collapse All support.
   - Wire selection tracking (`onSelectionChange`) to enable/disable block-specific actions (Duplicate, Delete, Unit Test).
   - Implement `handleDuplicateStep` and `handleDeleteSelected`.
3. **Step 3: Verification & Visual Polish**:
   - Test build: `npm --prefix frontend run build`.
   - Verify drag-and-drop onto canvas and click-to-add for all 5 block types.
   - Test all toolbar controls: Tidy Up, Fit View, Zoom In/Out, Grid modes, MiniMap toggle, Expand All/Collapse All, Duplicate, and Delete.
   - Verify light and dark theme styling against `DESIGN.md`.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `frontend/src/app/workflows/components/DAGToolbar.tsx` | New component | Dedicated attached toolbar with labelled block thumbnails, canvas controls, and block operations. |
| `frontend/src/app/workflows/components/VisualGraphEditor.tsx` | Component update | Dock `DAGToolbar`, wire drag-and-drop canvas drop handling, selection state, and batch operations. |
| `docs/features/dag-editor-block-toolbar/plan.md` | New documentation | Feature plan documentation following standard template. |
| `docs/features/dag-editor-block-toolbar/implementation.md` | New documentation | Step-by-step implementation log with dates and diffs. |
| `docs/features/dag-editor-block-toolbar/verification.md` | New documentation | Verification logs and test outputs. |
| `docs/features/dag-editor-block-toolbar/qa-checklist.md` | New documentation | Manual QA checklist for verification. |

## Interfaces

```typescript
export interface DAGToolbarProps {
  onAddBlock: (type: WorkflowStepType, dropPosition?: { x: number; y: number }) => void;
  onTidyUp: () => void;
  onFitView: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  isMiniMapOpen: boolean;
  onToggleMiniMap: () => void;
  backgroundVariant: BackgroundVariant | "none";
  onChangeBackgroundVariant: (variant: BackgroundVariant | "none") => void;
  isAllExpanded: boolean;
  onToggleExpandAll: () => void;
  selectedNodeId: string | null;
  onDuplicateSelected?: () => void;
  onDeleteSelected?: () => void;
  onUnitTestSelected?: () => void;
  onRunSystemTest?: () => void;
  stepCount: number;
  edgeCount: number;
  readOnly?: boolean;
}
```

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| ReactFlow canvas coordinate mismatch on drag-and-drop | Dropped node appears away from cursor position | Use `reactFlowInstance.screenToFlowPosition({ x: event.clientX, y: event.clientY })` to convert client screen pixels accurately to flow canvas space. |
| Canvas height / viewport compression by attached toolbar | Graph area shrinks | Keep toolbar height compact (44px bar + sleek collapsible or inline thumbnail shelf) and expand total editor container height slightly (`h-[720px]`). |
| Deleting connected nodes causing orphan edges | Broken references in workflow DAG | `handleDeleteStep` already cleans up `depends_on`, `true_target_step_id`, `false_target_step_id`, and `loop_target_step_id`. |

## Verification

- Unit tests / Compilation: `npm --prefix frontend run build` (0 TypeScript / Next.js errors).
- Manual checks:
  1. Verify attached toolbar renders docked at the top of the DAG editor.
  2. Verify all 5 block thumbnails display proper icons, accents, badges, and labels.
  3. Verify clicking a thumbnail adds the block to the DAG.
  4. Verify dragging a thumbnail drops the block at the cursor's exact coordinates.
  5. Verify Tidy Up, Fit View, Zoom In/Out, and Grid toggling.
  6. Verify Expand All and Collapse All toggles all nodes.
  7. Verify Duplicate Selected copies the selected block with all configurations preserved.
  8. Verify Delete Selected removes selected node or edge.
- Commands: `npm --prefix frontend run build`

## Rollout

Direct rollout to DAG editor frontend in Next.js app; backward compatible with existing workflow definitions.
