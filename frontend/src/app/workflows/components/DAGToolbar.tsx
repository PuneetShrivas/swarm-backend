"use client";

import React, { useState } from "react";
import { WorkflowStepType } from "../types";
import { BackgroundVariant } from "@xyflow/react";
import {
  Bot,
  GitBranch,
  Terminal,
  RotateCcw,
  FileOutput,
  Sparkles,
  Maximize2,
  ZoomIn,
  ZoomOut,
  Grid,
  Map,
  Copy,
  Trash2,
  Play,
  Layers,
  Lock,
  ChevronsUpDown,
  ChevronsDownUp,
  HelpCircle,
} from "lucide-react";

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
  selectedNodeName?: string | null;
  onDuplicateSelected?: () => void;
  onDeleteSelected?: () => void;
  onUnitTestSelected?: () => void;
  onRunSystemTest?: () => void;
  stepCount: number;
  edgeCount: number;
  readOnly?: boolean;
}

interface BlockDefinition {
  type: WorkflowStepType;
  title: string;
  badge: string;
  description: string;
  icon: React.ReactNode;
  accentBg: string;
  accentBorder: string;
  accentText: string;
  pillBorder: string;
  glowClass: string;
  renderThumbnailVisual: () => React.ReactNode;
}

const BLOCK_DEFINITIONS: BlockDefinition[] = [
  {
    type: "agent",
    title: "Agent Step",
    badge: "LLM",
    description: "Specialist LLM & prompt task",
    icon: <Bot size={13} className="text-linear-primary" />,
    accentBg: "bg-surface-2",
    accentBorder: "border-linear-primary/40",
    accentText: "text-linear-primary",
    pillBorder: "border-hairline",
    glowClass: "group-hover:border-linear-primary/60 group-hover:shadow-[0_0_12px_rgba(94,106,210,0.25)]",
    renderThumbnailVisual: () => (
      <div className="flex flex-col gap-1 w-full mt-1.5 opacity-80">
        <div className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-linear-primary" />
          <div className="h-1.5 w-16 bg-surface-3 rounded" />
          <span className="text-[8px] font-mono text-ink-tertiary ml-auto">qwen-3.8</span>
        </div>
        <div className="h-1 w-full bg-surface-3/80 rounded" />
        <div className="h-1 w-4/5 bg-surface-3/60 rounded" />
      </div>
    ),
  },
  {
    type: "condition",
    title: "Condition",
    badge: "BRANCH",
    description: "Python AST If / Else routing",
    icon: <GitBranch size={13} className="text-amber-400" />,
    accentBg: "bg-amber-500/10",
    accentBorder: "border-amber-500/40",
    accentText: "text-amber-400",
    pillBorder: "border-amber-500/30",
    glowClass: "group-hover:border-amber-400/60 group-hover:shadow-[0_0_12px_rgba(245,158,11,0.25)]",
    renderThumbnailVisual: () => (
      <div className="flex flex-col gap-1 w-full mt-1.5 opacity-80">
        <div className="flex items-center justify-between text-[8px] font-mono text-amber-300">
          <span>IF: expr &gt; 0</span>
        </div>
        <div className="flex items-center justify-between text-[7px] font-mono">
          <span className="text-emerald-400 flex items-center gap-0.5">✓ True</span>
          <span className="text-rose-400 flex items-center gap-0.5">✗ False</span>
        </div>
      </div>
    ),
  },
  {
    type: "python_code",
    title: "Python Code",
    badge: "CODE",
    description: "Sandboxed data computation",
    icon: <Terminal size={13} className="text-emerald-400" />,
    accentBg: "bg-emerald-500/10",
    accentBorder: "border-emerald-500/40",
    accentText: "text-emerald-400",
    pillBorder: "border-emerald-500/30",
    glowClass: "group-hover:border-emerald-400/60 group-hover:shadow-[0_0_12px_rgba(16,185,129,0.25)]",
    renderThumbnailVisual: () => (
      <div className="flex flex-col gap-1 w-full mt-1.5 opacity-80 font-mono text-[8px] text-emerald-300/90">
        <div className="flex items-center gap-1">
          <span className="text-ink-tertiary">def</span>
          <span className="text-emerald-400 font-medium">execute()</span>
        </div>
        <div className="flex items-center gap-1 pl-2">
          <span className="text-ink-tertiary">return</span>
          <span className="text-emerald-300">{"{res: ...}"}</span>
        </div>
      </div>
    ),
  },
  {
    type: "loop",
    title: "Loop Block",
    badge: "ITER",
    description: "Step iteration up to 10x",
    icon: <RotateCcw size={13} className="text-cyan-400" />,
    accentBg: "bg-cyan-500/10",
    accentBorder: "border-cyan-500/40",
    accentText: "text-cyan-400",
    pillBorder: "border-cyan-500/30",
    glowClass: "group-hover:border-cyan-400/60 group-hover:shadow-[0_0_12px_rgba(6,182,212,0.25)]",
    renderThumbnailVisual: () => (
      <div className="flex flex-col gap-1 w-full mt-1.5 opacity-80">
        <div className="flex items-center justify-between text-[8px] font-mono text-cyan-300">
          <span>Loop to Target</span>
          <span className="px-1 py-0.2 rounded-xs bg-cyan-950/50 border border-cyan-800 text-[7px]">max 3x</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-full h-1 bg-cyan-950 border-b border-cyan-500/50 rounded-full" />
        </div>
      </div>
    ),
  },
  {
    type: "artifact",
    title: "Artifact",
    badge: "FILE",
    description: "Reports, markdown & outputs",
    icon: <FileOutput size={13} className="text-purple-400" />,
    accentBg: "bg-purple-500/10",
    accentBorder: "border-purple-500/40",
    accentText: "text-purple-400",
    pillBorder: "border-purple-500/30",
    glowClass: "group-hover:border-purple-400/60 group-hover:shadow-[0_0_12px_rgba(168,85,247,0.25)]",
    renderThumbnailVisual: () => (
      <div className="flex flex-col gap-1 w-full mt-1.5 opacity-80">
        <div className="flex items-center justify-between text-[8px] font-mono text-purple-300">
          <span>Report Document</span>
          <span className="text-[7px] text-ink-tertiary">.md</span>
        </div>
        <div className="h-1 w-full bg-purple-950 border-b border-purple-500/40 rounded" />
        <div className="h-1 w-2/3 bg-purple-950/70 border-b border-purple-500/30 rounded" />
      </div>
    ),
  },
];

export default function DAGToolbar({
  onAddBlock,
  onTidyUp,
  onFitView,
  onZoomIn,
  onZoomOut,
  isMiniMapOpen,
  onToggleMiniMap,
  backgroundVariant,
  onChangeBackgroundVariant,
  isAllExpanded,
  onToggleExpandAll,
  selectedNodeId,
  selectedNodeName,
  onDuplicateSelected,
  onDeleteSelected,
  onUnitTestSelected,
  onRunSystemTest,
  stepCount,
  edgeCount,
  readOnly = false,
}: DAGToolbarProps) {
  const [isPaletteOpen, setIsPaletteOpen] = useState(true);

  // Background grid variants cycle: dots -> lines -> cross -> none
  const handleCycleGrid = () => {
    if (backgroundVariant === BackgroundVariant.Dots) {
      onChangeBackgroundVariant(BackgroundVariant.Lines);
    } else if (backgroundVariant === BackgroundVariant.Lines) {
      onChangeBackgroundVariant(BackgroundVariant.Cross);
    } else if (backgroundVariant === BackgroundVariant.Cross) {
      onChangeBackgroundVariant("none");
    } else {
      onChangeBackgroundVariant(BackgroundVariant.Dots);
    }
  };

  const getGridVariantLabel = () => {
    switch (backgroundVariant) {
      case BackgroundVariant.Dots:
        return "Dots";
      case BackgroundVariant.Lines:
        return "Lines";
      case BackgroundVariant.Cross:
        return "Cross";
      default:
        return "Off";
    }
  };

  return (
    <div className="border-b border-hairline bg-surface-1/95 backdrop-blur-md select-none shrink-0 z-20">
      {/* Upper Control Bar */}
      <div className="h-11 px-3 flex items-center justify-between gap-2 overflow-x-auto no-scrollbar">
        {/* Left: Palette Toggle & Stats */}
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            type="button"
            onClick={() => setIsPaletteOpen((prev) => !prev)}
            className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md transition-colors border ${
              isPaletteOpen
                ? "bg-surface-2 text-ink border-hairline-strong shadow-xs"
                : "text-ink-subtle hover:text-ink hover:bg-surface-2 border-hairline"
            }`}
            title="Toggle block palette shelf"
          >
            <Layers size={13} className="text-linear-primary" />
            <span>Blocks</span>
            <span className="text-[10px] font-mono px-1 py-0.2 rounded-xs bg-surface-3 text-ink-subtle border border-hairline">
              5
            </span>
          </button>

          <div className="h-4 w-px bg-hairline mx-1" />

          {/* DAG Layout & Canvas Controls */}
          <button
            type="button"
            onClick={onTidyUp}
            className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-ink hover:bg-surface-2 rounded-md transition-colors border border-hairline"
            title="Auto-organize DAG into hierarchical layers"
          >
            <Sparkles size={12} className="text-linear-primary" />
            <span className="hidden sm:inline">Tidy Up</span>
          </button>

          <button
            type="button"
            onClick={onFitView}
            className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors border border-hairline"
            title="Fit diagram to viewport"
          >
            <Maximize2 size={12} />
          </button>

          <div className="flex items-center rounded-md border border-hairline bg-surface-2/60 p-0.5">
            <button
              type="button"
              onClick={onZoomOut}
              className="p-1 rounded text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors"
              title="Zoom out"
            >
              <ZoomOut size={12} />
            </button>
            <div className="h-3 w-px bg-hairline mx-0.5" />
            <button
              type="button"
              onClick={onZoomIn}
              className="p-1 rounded text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors"
              title="Zoom in"
            >
              <ZoomIn size={12} />
            </button>
          </div>

          <button
            type="button"
            onClick={handleCycleGrid}
            className="flex items-center gap-1 px-2 py-1 text-xs font-mono text-ink-subtle hover:text-ink hover:bg-surface-2 rounded-md transition-colors border border-hairline"
            title={`Toggle canvas grid (Current: ${getGridVariantLabel()})`}
          >
            <Grid size={12} />
            <span className="text-[10px]">{getGridVariantLabel()}</span>
          </button>

          <button
            type="button"
            onClick={onToggleMiniMap}
            className={`p-1.5 rounded-md transition-colors border ${
              isMiniMapOpen
                ? "bg-surface-2 text-ink border-hairline-strong"
                : "text-ink-subtle hover:text-ink hover:bg-surface-2 border-hairline"
            }`}
            title="Toggle MiniMap navigator"
          >
            <Map size={12} />
          </button>

          <button
            type="button"
            onClick={onToggleExpandAll}
            className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-ink-subtle hover:text-ink hover:bg-surface-2 rounded-md transition-colors border border-hairline"
            title={isAllExpanded ? "Collapse all blocks" : "Expand all blocks for inline editing"}
          >
            {isAllExpanded ? (
              <>
                <ChevronsDownUp size={12} />
                <span className="hidden md:inline">Collapse All</span>
              </>
            ) : (
              <>
                <ChevronsUpDown size={12} />
                <span className="hidden md:inline">Expand All</span>
              </>
            )}
          </button>
        </div>

        {/* Right: Selected Node Operations & System Test */}
        <div className="flex items-center gap-1.5 shrink-0">
          {/* Selected Node Status Pill */}
          {selectedNodeId ? (
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-surface-2 border border-hairline-strong text-[11px] font-mono text-ink">
              <span className="w-1.5 h-1.5 rounded-full bg-linear-primary animate-pulse" />
              <span className="truncate max-w-[120px] font-medium">
                {selectedNodeName || selectedNodeId}
              </span>
            </div>
          ) : (
            <span className="hidden lg:inline text-[10px] font-mono text-ink-tertiary px-1">
              {stepCount} steps • {edgeCount} edges
            </span>
          )}

          {/* Block-specific Action Buttons */}
          {!readOnly && (
            <>
              <button
                type="button"
                disabled={!selectedNodeId || selectedNodeId === "goal_root"}
                onClick={onDuplicateSelected}
                className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors border border-hairline disabled:opacity-30 disabled:pointer-events-none"
                title={selectedNodeId ? "Duplicate selected block" : "Select a block to duplicate"}
              >
                <Copy size={12} />
              </button>

              <button
                type="button"
                disabled={!selectedNodeId || selectedNodeId === "goal_root"}
                onClick={onDeleteSelected}
                className="p-1.5 rounded-md text-ink-subtle hover:text-rose-400 hover:bg-surface-2 transition-colors border border-hairline disabled:opacity-30 disabled:pointer-events-none"
                title={selectedNodeId ? "Delete selected block" : "Select a block to delete"}
              >
                <Trash2 size={12} />
              </button>
            </>
          )}

          {onUnitTestSelected && selectedNodeId && selectedNodeId !== "goal_root" && (
            <button
              type="button"
              onClick={onUnitTestSelected}
              className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-emerald-400 hover:bg-surface-2 rounded-md transition-colors border border-hairline"
              title="Unit test selected block"
            >
              <Play size={11} className="fill-current" />
              <span className="hidden sm:inline">Unit Test</span>
            </button>
          )}

          {onRunSystemTest && (
            <button
              type="button"
              onClick={onRunSystemTest}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors shadow-xs ml-1"
              title="Run entire workflow end-to-end with custom inputs"
            >
              <Play size={11} className="fill-current text-white" />
              <span>Test DAG</span>
            </button>
          )}

          {readOnly && (
            <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-surface-2 border border-hairline text-ink-subtle">
              <Lock size={10} /> Locked
            </span>
          )}
        </div>
      </div>

      {/* Lower Block Thumbnail Tray (Collapsible Shelf) */}
      {isPaletteOpen && !readOnly && (
        <div className="px-3 py-2 border-t border-hairline bg-surface-1/60 overflow-x-auto no-scrollbar">
          <div className="flex items-center gap-2.5 min-w-max">
            <div className="flex items-center gap-1 text-[10px] font-mono text-ink-tertiary mr-1 select-none">
              <HelpCircle size={11} />
              <span>Click or Drag to add:</span>
            </div>

            {BLOCK_DEFINITIONS.map((block) => (
              <div
                key={block.type}
                draggable={!readOnly}
                onDragStart={(e) => {
                  e.dataTransfer.setData("application/reactflow-type", block.type);
                  e.dataTransfer.effectAllowed = "move";
                }}
                onClick={() => onAddBlock(block.type)}
                className={`group relative flex flex-col justify-between w-[138px] h-[72px] p-2 rounded-md bg-surface-1 border border-hairline hover:bg-surface-2 transition-all cursor-pointer hover:-translate-y-0.5 ${block.glowClass}`}
                title={`Click or drag to add ${block.title}. ${block.description}`}
              >
                {/* Thumbnail Header */}
                <div className="flex items-center justify-between gap-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <div
                      className={`w-5 h-5 rounded flex items-center justify-center shrink-0 border ${block.accentBg} ${block.accentBorder}`}
                    >
                      {block.icon}
                    </div>
                    <span className="text-[11px] font-medium text-ink truncate tracking-tight">
                      {block.title}
                    </span>
                  </div>
                  <span
                    className={`text-[8px] font-mono px-1 py-0.2 rounded-xs border uppercase shrink-0 ${block.accentBg} ${block.pillBorder} ${block.accentText}`}
                  >
                    {block.badge}
                  </span>
                </div>

                {/* Miniature Schematic Body */}
                {block.renderThumbnailVisual()}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
