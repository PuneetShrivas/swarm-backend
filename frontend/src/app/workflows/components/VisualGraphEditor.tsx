"use client";

import React, { useMemo, useCallback, useState } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Connection,
  Edge,
  Node,
  Handle,
  Position,
  NodeProps,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { WorkflowStep, ScriptTool, KnowledgeFile, WorkflowStepType } from "../types";
import DataFlowEdge from "./DataFlowEdge";
import {
  Bot,
  Zap,
  Play,
  Flag,
  Plus,
  Trash2,
  Sparkles,
  FolderOpen,
  GitBranch,
  Terminal,
  RotateCcw,
  FileOutput,
  ChevronDown,
  ChevronUp,
  Cpu,
  Check,
} from "lucide-react";

interface VisualGraphEditorProps {
  goal: string;
  steps: WorkflowStep[];
  edges: Array<{ id: string; source: string; target: string }>;
  onChangeSteps: (steps: WorkflowStep[]) => void;
  onChangeEdges: (edges: Array<{ id: string; source: string; target: string }>) => void;
  agents: Array<{ id: string; name: string; role?: string; icon?: string }>;
  tools: ScriptTool[];
  knowledgeFiles: KnowledgeFile[];
  onUnitTestStep?: (step: WorkflowStep) => void;
  onRunSystemTest?: () => void;
  readOnly?: boolean;
}

// ----------------- Helper: Variable Token Highlighter -----------------
function renderInstructionTokens(text: string) {
  if (!text) return <span className="text-ink-tertiary">No instructions set.</span>;
  const parts = text.split(/(\{\{[^{}]+\}\})/g);
  return (
    <span>
      {parts.map((part, i) => {
        if (part.startsWith("{{") && part.endsWith("}}")) {
          return (
            <span
              key={i}
              className="inline-block px-1 py-0.2 mx-0.5 rounded-xs bg-surface-2 text-linear-primary font-mono text-[10px] border border-hairline"
            >
              {part}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
}

// ----------------- Helper: Compute Nearest Handles between Two Positions -----------------
function getOptimalEdgeHandles(
  sourcePos?: { x: number; y: number },
  targetPos?: { x: number; y: number }
): { sourceHandle: string; targetHandle: string } {
  if (!sourcePos || !targetPos) {
    return { sourceHandle: "source-bottom", targetHandle: "target-top" };
  }

  const dx = targetPos.x - sourcePos.x;
  const dy = targetPos.y - sourcePos.y;

  if (Math.abs(dy) >= Math.abs(dx)) {
    if (dy >= 0) {
      return { sourceHandle: "source-bottom", targetHandle: "target-top" };
    } else {
      // Loopback or reverse direction
      return { sourceHandle: "source-top", targetHandle: "target-bottom" };
    }
  } else {
    if (dx >= 0) {
      return { sourceHandle: "source-right", targetHandle: "target-left" };
    } else {
      return { sourceHandle: "source-left", targetHandle: "target-right" };
    }
  }
}

// ----------------- 4-Way Handle Set Component -----------------
function PerimeterHandles() {
  return (
    <>
      {/* Top handles */}
      <Handle
        type="target"
        position={Position.Top}
        id="target-top"
        className="!w-2.5 !h-2.5 !bg-linear-primary !border-2 !border-canvas hover:!scale-125 transition-transform"
      />
      <Handle
        type="source"
        position={Position.Top}
        id="source-top"
        className="!w-2.5 !h-2.5 !bg-linear-primary !border-2 !border-canvas hover:!scale-125 transition-transform opacity-0 hover:opacity-100"
      />

      {/* Right handles */}
      <Handle
        type="target"
        position={Position.Right}
        id="target-right"
        className="!w-2.5 !h-2.5 !bg-linear-primary !border-2 !border-canvas hover:!scale-125 transition-transform opacity-0 hover:opacity-100"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="source-right"
        className="!w-2.5 !h-2.5 !bg-linear-primary !border-2 !border-canvas hover:!scale-125 transition-transform"
      />

      {/* Bottom handles */}
      <Handle
        type="target"
        position={Position.Bottom}
        id="target-bottom"
        className="!w-2.5 !h-2.5 !bg-linear-primary !border-2 !border-canvas hover:!scale-125 transition-transform opacity-0 hover:opacity-100"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="source-bottom"
        className="!w-2.5 !h-2.5 !bg-linear-primary !border-2 !border-canvas hover:!scale-125 transition-transform"
      />

      {/* Left handles */}
      <Handle
        type="target"
        position={Position.Left}
        id="target-left"
        className="!w-2.5 !h-2.5 !bg-linear-primary !border-2 !border-canvas hover:!scale-125 transition-transform"
      />
      <Handle
        type="source"
        position={Position.Left}
        id="source-left"
        className="!w-2.5 !h-2.5 !bg-linear-primary !border-2 !border-canvas hover:!scale-125 transition-transform opacity-0 hover:opacity-100"
      />
    </>
  );
}

// ----------------- Custom Node Components -----------------

// 1. Goal Root Node (Linear Style with 4-way Snapping)
function GoalNode({ data }: NodeProps) {
  return (
    <div className="p-4 rounded-lg bg-surface-1 border border-hairline hover:border-hairline-strong transition-colors shadow-card min-w-[260px] max-w-[300px] select-none font-sans relative">
      <PerimeterHandles />

      <div className="flex items-center justify-between gap-2 mb-2 pb-2 border-b border-hairline">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-surface-2 text-linear-primary border border-hairline flex items-center justify-center shrink-0">
            <Flag size={12} />
          </div>
          <div>
            <span className="text-xs font-medium text-ink tracking-card-title block">
              Workflow Objective
            </span>
            <span className="text-[10px] font-mono text-ink-subtle">id: goal_root</span>
          </div>
        </div>
        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-xs bg-surface-2 text-linear-primary border border-hairline">
          ROOT
        </span>
      </div>

      <p className="text-xs text-ink-subtle line-clamp-2 leading-relaxed mb-3 tracking-body">
        {(data?.goal as string) || "Define the high-level objective..."}
      </p>

      {/* Emitted Payload Tokens */}
      <div className="pt-2 border-t border-hairline flex flex-wrap items-center gap-1">
        <span className="text-[10px] text-ink-tertiary font-mono mr-1">payload:</span>
        <span className="px-1.5 py-0.2 rounded-xs bg-surface-2 text-ink-muted text-[10px] font-mono border border-hairline">
          {"{{goal}}"}
        </span>
        <span className="px-1.5 py-0.2 rounded-xs bg-surface-2 text-linear-primary text-[10px] font-mono border border-hairline">
          {"{{inputs.query}}"}
        </span>
      </div>
    </div>
  );
}

// 2. Expandable Multi-Type Step Node (Linear Style with 4-way Snapping)
function StepNode({ data }: NodeProps) {
  const step = data?.step as WorkflowStep;
  const onUnitTest = data?.onUnitTest as ((step: WorkflowStep) => void) | undefined;
  const onDeleteStep = data?.onDeleteStep as ((stepId: string) => void) | undefined;
  const onUpdateStep = data?.onUpdateStep as ((updated: WorkflowStep) => void) | undefined;
  const onToggleExpand = data?.onToggleExpand as ((stepId: string) => void) | undefined;
  const isExpanded = Boolean(data?.isExpanded);
  const agentName = (data?.agentName as string) || step?.agent_id || "Specialist Agent";
  const stepIndex = (data?.stepIndex as number) ?? 1;
  const allSteps = (data?.allSteps as WorkflowStep[]) || [];
  const agentsList = (data?.agentsList as Array<{ id: string; name: string }>) || [];
  const toolsList = (data?.toolsList as ScriptTool[]) || [];

  const stepType: WorkflowStepType = step?.step_type || "agent";

  // Visual Identity per Block Type
  const getBlockConfig = () => {
    switch (stepType) {
      case "condition":
        return {
          label: "Condition",
          icon: <GitBranch size={12} className="text-amber-400" />,
          accentBg: "bg-amber-500/10",
          accentBorder: "border-amber-500/30",
          accentText: "text-amber-400",
        };
      case "python_code":
        return {
          label: "Python Code",
          icon: <Terminal size={12} className="text-emerald-400" />,
          accentBg: "bg-emerald-500/10",
          accentBorder: "border-emerald-500/30",
          accentText: "text-emerald-400",
        };
      case "loop":
        return {
          label: "Loop",
          icon: <RotateCcw size={12} className="text-cyan-400" />,
          accentBg: "bg-cyan-500/10",
          accentBorder: "border-cyan-500/30",
          accentText: "text-cyan-400",
        };
      case "artifact":
        return {
          label: "Artifact",
          icon: <FileOutput size={12} className="text-purple-400" />,
          accentBg: "bg-purple-500/10",
          accentBorder: "border-purple-500/30",
          accentText: "text-purple-400",
        };
      default:
        return {
          label: "Agent",
          icon: <Bot size={12} className="text-linear-primary" />,
          accentBg: "bg-surface-2",
          accentBorder: "border-hairline",
          accentText: "text-linear-primary",
        };
    }
  };

  const blockCfg = getBlockConfig();

  return (
    <div
      className={`rounded-lg bg-surface-1 border transition-all shadow-card select-none font-sans group relative ${
        isExpanded
          ? "w-[420px] border-linear-primary shadow-lg p-4"
          : "min-w-[280px] max-w-[320px] border-hairline hover:border-hairline-strong p-4"
      }`}
    >
      <PerimeterHandles />

      {/* Step Header */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-hairline">
        <div
          className="flex items-center gap-2 min-w-0 cursor-pointer"
          onClick={() => onToggleExpand?.(step.id)}
          title="Click to expand/collapse block controls"
        >
          <div
            className={`w-6 h-6 rounded-md ${blockCfg.accentBg} border ${blockCfg.accentBorder} flex items-center justify-center shrink-0`}
          >
            {blockCfg.icon}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-mono px-1 rounded-xs bg-surface-2 text-ink-subtle border border-hairline">
                #{stepIndex}
              </span>
              <h4 className="text-xs font-medium text-ink truncate tracking-card-title">
                {step?.name || `Step ${stepIndex}`}
              </h4>
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`text-[9px] font-mono uppercase px-1 rounded-xs border ${blockCfg.accentBg} ${blockCfg.accentBorder} ${blockCfg.accentText}`}>
                {blockCfg.label}
              </span>
              {stepType === "agent" && (
                <span className="text-[10px] text-ink-subtle truncate max-w-[140px]">
                  {agentName}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons: Expand Toggle, Unit Test, Delete */}
        <div className="flex items-center gap-1 shrink-0 ml-1">
          {onUnitTest && (
            <button
              onClick={() => onUnitTest(step)}
              className="p-1 rounded-md text-ink-subtle hover:text-semantic-success hover:bg-surface-2 transition-colors"
              title="Run isolated unit test on this block"
            >
              <Play size={11} className="fill-current" />
            </button>
          )}

          <button
            onClick={() => onToggleExpand?.(step.id)}
            className="p-1 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors"
            title={isExpanded ? "Collapse block" : "Expand block"}
          >
            {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>

          {onDeleteStep && (
            <button
              onClick={() => onDeleteStep(step.id)}
              className="p-1 rounded-md text-ink-subtle hover:text-red-400 hover:bg-surface-2 transition-colors opacity-0 group-hover:opacity-100"
              title="Delete block"
            >
              <Trash2 size={11} />
            </button>
          )}
        </div>
      </div>

      {/* COMPACT VIEW */}
      {!isExpanded && (
        <>
          {stepType === "condition" && (
            <div className="space-y-1.5 mb-2.5">
              <div className="text-[10px] font-mono bg-canvas p-2 rounded-md border border-hairline text-ink-subtle">
                <span className="text-amber-400 font-semibold">IF: </span>
                {step.condition_expr || "True"}
              </div>
              <div className="flex items-center justify-between text-[9px] font-mono text-ink-tertiary px-1">
                <span className="text-emerald-400 flex items-center gap-1">
                  ✓ True: {step.true_target_step_id || "Next Step"}
                </span>
                <span className="text-rose-400 flex items-center gap-1">
                  ✗ False: {step.false_target_step_id || "End"}
                </span>
              </div>
            </div>
          )}

          {stepType === "python_code" && (
            <div className="text-[11px] font-mono text-emerald-300 bg-canvas p-2 rounded-md border border-hairline mb-2.5 leading-relaxed line-clamp-2">
              <code>{step.code ? step.code.slice(0, 100) : "def execute(inputs, outputs, ctx): pass"}</code>
            </div>
          )}

          {stepType === "loop" && (
            <div className="space-y-1 mb-2.5">
              <div className="text-[10px] font-mono bg-canvas p-2 rounded-md border border-hairline text-cyan-300 flex items-center justify-between">
                <span>Loop to: {step.loop_target_step_id || "Start"}</span>
                <span className="px-1.5 py-0.2 rounded-xs bg-surface-2 border border-hairline text-[9px]">
                  max: {step.max_loop_iterations || 3}x
                </span>
              </div>
            </div>
          )}

          {stepType === "artifact" && (
            <div className="space-y-1 mb-2.5">
              <div className="text-[10px] font-mono bg-canvas p-2 rounded-md border border-hairline text-purple-300 flex items-center justify-between">
                <span className="truncate">{step.artifact_title || "Generated Artifact"}</span>
                <span className="uppercase text-[9px] px-1 rounded-xs bg-surface-2 border border-hairline">
                  {step.artifact_type || "markdown"}
                </span>
              </div>
            </div>
          )}

          {stepType === "agent" && (
            <div className="text-[11px] font-mono text-ink-subtle line-clamp-2 bg-canvas p-2 rounded-md border border-hairline mb-2.5 leading-relaxed">
              {renderInstructionTokens(step?.instructions)}
            </div>
          )}

          {/* Badges: Tools & Knowledge files */}
          <div className="flex items-center justify-between text-[10px] text-ink-subtle pt-1 border-t border-hairline">
            <div className="flex items-center gap-1.5">
              {step?.tool_ids?.length > 0 && (
                <span className="flex items-center gap-1 bg-surface-2 text-ink-muted border border-hairline px-1.5 py-0.2 rounded-xs font-mono">
                  <Zap size={9} className="text-linear-primary" /> {step.tool_ids.length} tools
                </span>
              )}
              {step?.knowledge_file_ids?.length > 0 && (
                <span className="flex items-center gap-1 bg-surface-2 text-ink-muted border border-hairline px-1.5 py-0.2 rounded-xs font-mono">
                  <FolderOpen size={9} /> {step.knowledge_file_ids.length} docs
                </span>
              )}
              {(!step?.tool_ids || step.tool_ids.length === 0) &&
                (!step?.knowledge_file_ids || step.knowledge_file_ids.length === 0) && (
                  <span className="text-ink-tertiary font-mono text-[9px] cursor-pointer" onClick={() => onToggleExpand?.(step.id)}>
                    click to edit
                  </span>
                )}
            </div>

            <span className="font-mono text-[9px] text-ink-tertiary">
              {stepType === "condition" ? "output: branch" : stepType === "artifact" ? "output: file" : "output: text"}
            </span>
          </div>
        </>
      )}

      {/* EXPANDED INTERACTIVE INLINE EDITOR */}
      {isExpanded && (
        <div className="space-y-3 pt-1" onClick={(e) => e.stopPropagation()}>
          {/* Step Name Edit */}
          <div>
            <label className="text-[10px] font-medium text-ink-tertiary mb-1 block">Step Name</label>
            <input
              type="text"
              value={step.name}
              onChange={(e) => onUpdateStep?.({ ...step, name: e.target.value })}
              className="w-full text-xs bg-canvas border border-hairline rounded-md px-2 py-1 text-ink focus:outline-none focus:border-linear-focus"
              placeholder="Step name"
            />
          </div>

          {/* Type-Specific Editors */}
          {stepType === "condition" && (
            <div className="space-y-2">
              <div>
                <label className="text-[10px] font-medium text-amber-400 mb-1 block flex items-center justify-between">
                  <span>Condition Expression (Python AST)</span>
                  <span className="text-[9px] text-ink-tertiary font-mono">e.g. len(inputs.query) &gt; 10</span>
                </label>
                <input
                  type="text"
                  value={step.condition_expr || ""}
                  onChange={(e) => onUpdateStep?.({ ...step, condition_expr: e.target.value })}
                  placeholder="inputs.get('status') == 'success' or len(inputs.query) > 10"
                  className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md px-2 py-1.5 text-amber-300 focus:outline-none focus:border-amber-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] font-medium text-emerald-400 mb-1 block">True Target Step</label>
                  <select
                    value={step.true_target_step_id || ""}
                    onChange={(e) => onUpdateStep?.({ ...step, true_target_step_id: e.target.value })}
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2 py-1 text-ink focus:outline-none"
                  >
                    <option value="">Default (Next Step)</option>
                    {allSteps.filter((s) => s.id !== step.id).map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-medium text-rose-400 mb-1 block">False Target Step</label>
                  <select
                    value={step.false_target_step_id || ""}
                    onChange={(e) => onUpdateStep?.({ ...step, false_target_step_id: e.target.value })}
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2 py-1 text-ink focus:outline-none"
                  >
                    <option value="">Default (End Workflow)</option>
                    {allSteps.filter((s) => s.id !== step.id).map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {stepType === "python_code" && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[10px] font-medium text-emerald-400 flex items-center gap-1">
                  <Terminal size={11} /> Inline Python Processor
                </label>
                <span className="text-[9px] text-ink-tertiary font-mono">execute(inputs, outputs, ctx)</span>
              </div>
              <textarea
                rows={5}
                value={step.code || "def execute(inputs, previous_outputs, context):\n    # Custom processing\n    query = inputs.get('query', '')\n    return {'result': query.upper(), 'status': 'ok'}"}
                onChange={(e) => onUpdateStep?.({ ...step, code: e.target.value })}
                className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md p-2 text-emerald-300 focus:outline-none focus:border-emerald-400 resize-y"
              />
            </div>
          )}

          {stepType === "loop" && (
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] font-medium text-cyan-400 mb-1 block">Loop Target Step</label>
                  <select
                    value={step.loop_target_step_id || ""}
                    onChange={(e) => onUpdateStep?.({ ...step, loop_target_step_id: e.target.value })}
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2 py-1 text-ink focus:outline-none"
                  >
                    <option value="">Select target to loop to...</option>
                    {allSteps.filter((s) => s.id !== step.id).map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-medium text-cyan-400 mb-1 block">Max Iterations (1-10)</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={step.max_loop_iterations ?? 3}
                    onChange={(e) => onUpdateStep?.({ ...step, max_loop_iterations: parseInt(e.target.value, 10) || 1 })}
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2 py-1 text-ink focus:outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="text-[10px] font-medium text-ink-tertiary mb-1 block">Termination Condition (Optional)</label>
                <input
                  type="text"
                  value={step.condition_expr || ""}
                  onChange={(e) => onUpdateStep?.({ ...step, condition_expr: e.target.value })}
                  placeholder="context.get('loop_count', 0) < 3"
                  className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md px-2 py-1 text-ink focus:outline-none"
                />
              </div>
            </div>
          )}

          {stepType === "artifact" && (
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] font-medium text-purple-400 mb-1 block">Artifact Title</label>
                  <input
                    type="text"
                    value={step.artifact_title || ""}
                    onChange={(e) => onUpdateStep?.({ ...step, artifact_title: e.target.value })}
                    placeholder="e.g. Security Audit Report"
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2 py-1 text-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-medium text-purple-400 mb-1 block">Artifact Type</label>
                  <select
                    value={step.artifact_type || "markdown"}
                    onChange={(e) => onUpdateStep?.({ ...step, artifact_type: e.target.value })}
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2 py-1 text-ink focus:outline-none"
                  >
                    <option value="markdown">Markdown Document (.md)</option>
                    <option value="code">Source Code (.py / .ts)</option>
                    <option value="json">Structured JSON (.json)</option>
                    <option value="report">Executive Report (.md)</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-[10px] font-medium text-ink-tertiary mb-1 block">Content / Template Instructions</label>
                <textarea
                  rows={3}
                  value={step.instructions || ""}
                  onChange={(e) => onUpdateStep?.({ ...step, instructions: e.target.value })}
                  placeholder="Provide markdown template or instructions for artifact formatting..."
                  className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md p-2 text-ink focus:outline-none resize-y"
                />
              </div>
            </div>
          )}

          {stepType === "agent" && (
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] font-medium text-ink-tertiary mb-1 block">Agent Specialist</label>
                  <select
                    value={step.agent_id}
                    onChange={(e) => onUpdateStep?.({ ...step, agent_id: e.target.value })}
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2 py-1 text-ink focus:outline-none"
                  >
                    {agentsList.map((ag) => (
                      <option key={ag.id} value={ag.id}>{ag.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-medium text-ink-tertiary mb-1 block flex items-center gap-1">
                    <Cpu size={10} className="text-linear-primary" /> Model Selection
                  </label>
                  <select
                    value={step.model || "gemini-3.8-flash"}
                    onChange={(e) => onUpdateStep?.({ ...step, model: e.target.value })}
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2 py-1 text-ink focus:outline-none"
                  >
                    <option value="gemini-3.8-flash">Gemini 3.8 Flash (Fast)</option>
                    <option value="gemini-4-argon">Gemini 4 Argon (Deep Reasoning)</option>
                    <option value="sonar">Perplexity Sonar (Live Web Search)</option>
                    <option value="sonar-pro">Perplexity Sonar Pro (Advanced Synthesis)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-medium text-ink-tertiary mb-1 block">Prompt Instructions</label>
                <textarea
                  rows={3}
                  value={step.instructions || ""}
                  onChange={(e) => onUpdateStep?.({ ...step, instructions: e.target.value })}
                  placeholder="Instructions for the agent..."
                  className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md p-2 text-ink focus:outline-none resize-y"
                />
              </div>

              {/* Tools toggles */}
              <div className="pt-1 border-t border-hairline flex flex-wrap gap-1">
                {toolsList.map((t) => {
                  const isChecked = step.tool_ids?.includes(t.id);
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => {
                        const newIds = isChecked
                          ? step.tool_ids.filter((id) => id !== t.id)
                          : [...(step.tool_ids || []), t.id];
                        onUpdateStep?.({ ...step, tool_ids: newIds });
                      }}
                      className={`text-[9px] px-1.5 py-0.5 rounded border transition-colors flex items-center gap-1 ${
                        isChecked
                          ? "bg-amber-500/15 border-amber-500/40 text-amber-400"
                          : "bg-surface-2 border-hairline text-ink-muted hover:border-hairline-strong"
                      }`}
                    >
                      <Zap size={9} /> {t.name}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Footer Controls */}
          <div className="flex items-center justify-between pt-2 border-t border-hairline">
            <button
              type="button"
              onClick={() => onToggleExpand?.(step.id)}
              className="text-[10px] font-medium text-ink hover:text-white px-2 py-1 rounded bg-surface-2 border border-hairline flex items-center gap-1"
            >
              <Check size={11} className="text-semantic-success" /> Done
            </button>

            {onUnitTest && (
              <button
                type="button"
                onClick={() => onUnitTest(step)}
                className="text-[10px] font-medium text-semantic-success hover:bg-surface-2 px-2 py-1 rounded flex items-center gap-1"
              >
                <Play size={10} className="fill-current" /> Run Test
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ----------------- Layout Calculation ("Tidy Up") -----------------
function calculateDAGLayout(
  goal: string,
  steps: WorkflowStep[],
  edges: Array<{ id: string; source: string; target: string }>,
  agents: Array<{ id: string; name: string; role?: string }>,
  tools: ScriptTool[],
  knowledgeFiles: KnowledgeFile[],
  expandedNodeId: string | null,
  onUnitTestStep?: (step: WorkflowStep) => void,
  onDeleteStep?: (stepId: string) => void,
  onUpdateStep?: (updated: WorkflowStep) => void,
  onToggleExpand?: (stepId: string) => void
): Node[] {
  const levels: Record<string, number> = { goal_root: 0 };

  const computeDepth = (id: string, visited = new Set<string>()): number => {
    if (visited.has(id)) return 1;
    visited.add(id);

    const step = steps.find((s) => s.id === id);
    if (!step || step.depends_on.length === 0) {
      return 1;
    }

    let maxParentDepth = 0;
    for (const dep of step.depends_on) {
      if (dep === "goal_root") {
        maxParentDepth = Math.max(maxParentDepth, 0);
      } else {
        maxParentDepth = Math.max(maxParentDepth, computeDepth(dep, new Set(visited)));
      }
    }
    return maxParentDepth + 1;
  };

  steps.forEach((s) => {
    levels[s.id] = computeDepth(s.id);
  });

  const byLevel: Record<number, WorkflowStep[]> = {};
  steps.forEach((s) => {
    const lvl = levels[s.id] || 1;
    if (!byLevel[lvl]) byLevel[lvl] = [];
    byLevel[lvl].push(s);
  });

  const nodeList: Node[] = [
    {
      id: "goal_root",
      type: "goalNode",
      position: { x: 380, y: 30 },
      data: { goal },
    },
  ];

  Object.entries(byLevel).forEach(([lvlStr, levelSteps]) => {
    const lvl = parseInt(lvlStr, 10);
    const count = levelSteps.length;
    const spacingX = 380;
    const startX = 380 - ((count - 1) * spacingX) / 2;
    const posY = 30 + lvl * 260;

    levelSteps.forEach((st, idx) => {
      const agentObj = agents.find((a) => a.id === st.agent_id);
      const originalIndex = steps.findIndex((x) => x.id === st.id) + 1;

      nodeList.push({
        id: st.id,
        type: "stepNode",
        position: { x: startX + idx * spacingX, y: posY },
        data: {
          step: st,
          stepIndex: originalIndex,
          agentName: agentObj?.name || st.agent_id,
          agentRole: agentObj?.role || "Agent executor",
          allSteps: steps,
          agentsList: agents,
          toolsList: tools,
          filesList: knowledgeFiles,
          isExpanded: expandedNodeId === st.id,
          onUnitTest: onUnitTestStep,
          onDeleteStep: onDeleteStep,
          onUpdateStep: onUpdateStep,
          onToggleExpand: onToggleExpand,
        },
      });
    });
  });

  return nodeList;
}

// ----------------- Main VisualGraphEditor Component -----------------
export default function VisualGraphEditor({
  goal,
  steps,
  edges,
  onChangeSteps,
  onChangeEdges,
  agents,
  tools,
  knowledgeFiles,
  onUnitTestStep,
  onRunSystemTest,
  readOnly = false,
}: VisualGraphEditorProps) {
  const [expandedNodeId, setExpandedNodeId] = useState<string | null>(null);
  const [showBlockPalette, setShowBlockPalette] = useState(false);

  // Toggle node expansion
  const handleToggleExpand = useCallback((stepId: string) => {
    setExpandedNodeId((prev) => (prev === stepId ? null : stepId));
  }, []);

  // Update a single step
  const handleUpdateStep = useCallback(
    (updatedStep: WorkflowStep) => {
      if (readOnly) return;
      const nextSteps = steps.map((s) => (s.id === updatedStep.id ? updatedStep : s));
      onChangeSteps(nextSteps);
    },
    [readOnly, steps, onChangeSteps]
  );

  // Delete edge handler
  const handleDeleteEdge = useCallback(
    (edgeId: string) => {
      if (readOnly) return;
      const [src, tgt] = edgeId.split("->");

      if (src && tgt && src !== "goal_root") {
        const nextSteps = steps.map((s) => {
          if (s.id === tgt) {
            return {
              ...s,
              depends_on: s.depends_on.filter((d) => d !== src),
            };
          }
          return s;
        });
        onChangeSteps(nextSteps);
      }

      onChangeEdges(edges.filter((e) => e.id !== edgeId && `${e.source}->${e.target}` !== edgeId));
    },
    [readOnly, steps, edges, onChangeSteps, onChangeEdges]
  );

  // Delete step handler
  const handleDeleteStep = useCallback(
    (stepId: string) => {
      if (readOnly) return;
      if (!confirm(`Delete step ${stepId}?`)) return;

      const nextSteps = steps
        .filter((s) => s.id !== stepId)
        .map((s) => ({
          ...s,
          depends_on: s.depends_on.filter((d) => d !== stepId),
          true_target_step_id: s.true_target_step_id === stepId ? undefined : s.true_target_step_id,
          false_target_step_id: s.false_target_step_id === stepId ? undefined : s.false_target_step_id,
          loop_target_step_id: s.loop_target_step_id === stepId ? undefined : s.loop_target_step_id,
        }));

      const nextEdges = edges.filter((e) => e.source !== stepId && e.target !== stepId);

      onChangeSteps(nextSteps);
      onChangeEdges(nextEdges);
    },
    [readOnly, steps, edges, onChangeSteps, onChangeEdges]
  );

  // Memoize custom node and edge types
  const nodeTypes = useMemo(
    () => ({
      goalNode: GoalNode,
      stepNode: StepNode,
    }),
    []
  );

  const edgeTypes = useMemo(
    () => ({
      dataFlowEdge: DataFlowEdge,
    }),
    []
  );

  // Generate initial React Flow nodes with layout
  const computedNodes: Node[] = useMemo(() => {
    return calculateDAGLayout(
      goal,
      steps,
      edges,
      agents,
      tools,
      knowledgeFiles,
      expandedNodeId,
      onUnitTestStep,
      handleDeleteStep,
      handleUpdateStep,
      handleToggleExpand
    );
  }, [
    goal,
    steps,
    edges,
    agents,
    tools,
    knowledgeFiles,
    expandedNodeId,
    onUnitTestStep,
    handleDeleteStep,
    handleUpdateStep,
    handleToggleExpand,
  ]);

  // Map of node positions for dynamic nearest-edge snapping
  const nodePositionMap = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>();
    computedNodes.forEach((n) => {
      map.set(n.id, n.position);
    });
    return map;
  }, [computedNodes]);

  // Generate React Flow edges with payload labels & dynamic nearest-edge snapping
  const computedEdges: Edge[] = useMemo(() => {
    const edgeMap = new Map<string, Edge>();

    // 1. Edges from explicit depends_on
    steps.forEach((step) => {
      if (step.depends_on.length === 0) {
        const edgeId = `goal_root->${step.id}`;
        const sourcePos = nodePositionMap.get("goal_root");
        const targetPos = nodePositionMap.get(step.id);
        const { sourceHandle, targetHandle } = getOptimalEdgeHandles(sourcePos, targetPos);

        edgeMap.set(edgeId, {
          id: edgeId,
          type: "dataFlowEdge",
          source: "goal_root",
          target: step.id,
          sourceHandle,
          targetHandle,
          animated: true,
          data: {
            payloadLabel: "{{inputs.query}}",
            edgeType: "normal",
            onDeleteEdge: handleDeleteEdge,
          },
        });
      } else {
        step.depends_on.forEach((depId) => {
          const edgeId = `${depId}->${step.id}`;
          const sourcePos = nodePositionMap.get(depId);
          const targetPos = nodePositionMap.get(step.id);
          const { sourceHandle, targetHandle } = getOptimalEdgeHandles(sourcePos, targetPos);

          const parentStep = steps.find((s) => s.id === depId);
          let edgeType: "normal" | "true_branch" | "false_branch" | "loop_back" = "normal";
          let payloadLabel = `{{steps.${depId}.output.text}}`;

          if (parentStep?.step_type === "condition") {
            if (parentStep.true_target_step_id === step.id) {
              edgeType = "true_branch";
              payloadLabel = "True Branch";
            } else if (parentStep.false_target_step_id === step.id) {
              edgeType = "false_branch";
              payloadLabel = "False Branch";
            }
          } else if (parentStep?.step_type === "loop" && parentStep.loop_target_step_id === step.id) {
            edgeType = "loop_back";
            payloadLabel = "Loop Iteration";
          }

          edgeMap.set(edgeId, {
            id: edgeId,
            type: "dataFlowEdge",
            source: depId,
            target: step.id,
            sourceHandle,
            targetHandle,
            animated: true,
            data: {
              payloadLabel,
              edgeType,
              onDeleteEdge: handleDeleteEdge,
            },
          });
        });
      }

      // If step has specific branch targets not yet in edgeMap
      if (step.step_type === "condition") {
        if (step.true_target_step_id) {
          const edgeId = `${step.id}->${step.true_target_step_id}`;
          if (!edgeMap.has(edgeId)) {
            const { sourceHandle, targetHandle } = getOptimalEdgeHandles(
              nodePositionMap.get(step.id),
              nodePositionMap.get(step.true_target_step_id)
            );
            edgeMap.set(edgeId, {
              id: edgeId,
              type: "dataFlowEdge",
              source: step.id,
              target: step.true_target_step_id,
              sourceHandle,
              targetHandle,
              animated: true,
              data: {
                payloadLabel: "True Branch",
                edgeType: "true_branch",
                onDeleteEdge: handleDeleteEdge,
              },
            });
          }
        }
        if (step.false_target_step_id) {
          const edgeId = `${step.id}->${step.false_target_step_id}`;
          if (!edgeMap.has(edgeId)) {
            const { sourceHandle, targetHandle } = getOptimalEdgeHandles(
              nodePositionMap.get(step.id),
              nodePositionMap.get(step.false_target_step_id)
            );
            edgeMap.set(edgeId, {
              id: edgeId,
              type: "dataFlowEdge",
              source: step.id,
              target: step.false_target_step_id,
              sourceHandle,
              targetHandle,
              animated: true,
              data: {
                payloadLabel: "False Branch",
                edgeType: "false_branch",
                onDeleteEdge: handleDeleteEdge,
              },
            });
          }
        }
      }

      // If loop block has target
      if (step.step_type === "loop" && step.loop_target_step_id) {
        const edgeId = `${step.id}->${step.loop_target_step_id}`;
        if (!edgeMap.has(edgeId)) {
          const { sourceHandle, targetHandle } = getOptimalEdgeHandles(
            nodePositionMap.get(step.id),
            nodePositionMap.get(step.loop_target_step_id)
          );
          edgeMap.set(edgeId, {
            id: edgeId,
            type: "dataFlowEdge",
            source: step.id,
            target: step.loop_target_step_id,
            sourceHandle,
            targetHandle,
            animated: true,
            data: {
              payloadLabel: "Loop Iteration",
              edgeType: "loop_back",
              onDeleteEdge: handleDeleteEdge,
            },
          });
        }
      }
    });

    // 2. Extra edges passed from props
    edges.forEach((e) => {
      const edgeId = `${e.source}->${e.target}`;
      if (!edgeMap.has(edgeId)) {
        const { sourceHandle, targetHandle } = getOptimalEdgeHandles(
          nodePositionMap.get(e.source),
          nodePositionMap.get(e.target)
        );
        edgeMap.set(edgeId, {
          id: edgeId,
          type: "dataFlowEdge",
          source: e.source,
          target: e.target,
          sourceHandle,
          targetHandle,
          animated: true,
          data: {
            payloadLabel:
              e.source === "goal_root"
                ? "{{inputs.query}}"
                : `{{steps.${e.source}.output.text}}`,
            edgeType: "normal",
            onDeleteEdge: handleDeleteEdge,
          },
        });
      }
    });

    return Array.from(edgeMap.values());
  }, [steps, edges, nodePositionMap, handleDeleteEdge]);

  const [nodes, setNodes, onNodesChange] = useNodesState(computedNodes);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState(computedEdges);

  React.useEffect(() => {
    setNodes(computedNodes);
  }, [computedNodes, setNodes]);

  React.useEffect(() => {
    setRfEdges(computedEdges);
  }, [computedEdges, setRfEdges]);

  // Handle new edge connection
  const onConnect = useCallback(
    (connection: Connection) => {
      if (readOnly || !connection.source || !connection.target) return;

      const newEdgeId = `${connection.source}->${connection.target}`;

      if (connection.source !== "goal_root") {
        const nextSteps = steps.map((s) => {
          if (s.id === connection.target && !s.depends_on.includes(connection.source!)) {
            return { ...s, depends_on: [...s.depends_on, connection.source!] };
          }
          return s;
        });
        onChangeSteps(nextSteps);
      }

      onChangeEdges([
        ...edges,
        {
          id: newEdgeId,
          source: connection.source,
          target: connection.target,
        },
      ]);
    },
    [readOnly, steps, edges, onChangeSteps, onChangeEdges]
  );

  // Add specific block type
  const handleAddBlock = (blockType: WorkflowStepType) => {
    if (readOnly) return;
    const nextIdx = steps.length + 1;
    const newStepId = `step_${nextIdx}_${Date.now().toString(36).slice(-3)}`;
    const previousStepId = steps.length > 0 ? steps[steps.length - 1].id : "goal_root";

    let newStep: WorkflowStep;

    switch (blockType) {
      case "condition":
        newStep = {
          id: newStepId,
          name: `Step ${nextIdx}: Condition Check`,
          step_type: "condition",
          agent_id: "orchestrator",
          condition_expr: "len(inputs.get('query', '')) > 0",
          instructions: "Evaluate condition expression",
          tool_ids: [],
          knowledge_file_ids: [],
          depends_on: previousStepId === "goal_root" ? [] : [previousStepId],
        };
        break;

      case "python_code":
        newStep = {
          id: newStepId,
          name: `Step ${nextIdx}: Python Processing`,
          step_type: "python_code",
          agent_id: "coder",
          code: "def execute(inputs, previous_outputs, context):\n    # Process data with Python\n    text = inputs.get('query', '')\n    return {'status': 'processed', 'length': len(text)}",
          instructions: "Execute sandboxed Python script",
          tool_ids: [],
          knowledge_file_ids: [],
          depends_on: previousStepId === "goal_root" ? [] : [previousStepId],
        };
        break;

      case "loop":
        newStep = {
          id: newStepId,
          name: `Step ${nextIdx}: Iteration Loop`,
          step_type: "loop",
          agent_id: "orchestrator",
          loop_target_step_id: previousStepId !== "goal_root" ? previousStepId : undefined,
          max_loop_iterations: 3,
          condition_expr: "context.get('loop_count', 0) < 3",
          instructions: "Loop back to target step until iteration limit",
          tool_ids: [],
          knowledge_file_ids: [],
          depends_on: previousStepId === "goal_root" ? [] : [previousStepId],
        };
        break;

      case "artifact":
        newStep = {
          id: newStepId,
          name: `Step ${nextIdx}: Generate Artifact`,
          step_type: "artifact",
          agent_id: "synthesizer",
          artifact_title: `Generated Report ${nextIdx}`,
          artifact_type: "markdown",
          instructions: "# Final Report\n\nGenerated automatically by Swarm Backend Pipeline.",
          tool_ids: [],
          knowledge_file_ids: [],
          depends_on: previousStepId === "goal_root" ? [] : [previousStepId],
        };
        break;

      default: // agent
        newStep = {
          id: newStepId,
          name: `Step ${nextIdx}: Specialist Action`,
          step_type: "agent",
          agent_id: agents.length > 1 ? agents[1].id : "researcher",
          model: "gemini-3.8-flash",
          instructions:
            previousStepId === "goal_root"
              ? "Process input objective: {{inputs.query}}"
              : `Synthesize input from predecessor: {{steps.${previousStepId}.output.text}}`,
          tool_ids: [],
          knowledge_file_ids: [],
          depends_on: previousStepId === "goal_root" ? [] : [previousStepId],
        };
        break;
    }

    const nextSteps = [...steps, newStep];
    const nextEdges = [
      ...edges,
      {
        id: `${previousStepId}->${newStepId}`,
        source: previousStepId,
        target: newStepId,
      },
    ];

    onChangeSteps(nextSteps);
    onChangeEdges(nextEdges);
    setShowBlockPalette(false);
    setExpandedNodeId(newStepId);
  };

  // Quick Action: Tidy Up (Recalculate auto-layout)
  const handleTidyUp = () => {
    const laidOut = calculateDAGLayout(
      goal,
      steps,
      edges,
      agents,
      tools,
      knowledgeFiles,
      expandedNodeId,
      onUnitTestStep,
      handleDeleteStep,
      handleUpdateStep,
      handleToggleExpand
    );
    setNodes(laidOut);
  };

  return (
    <div className="w-full h-[680px] rounded-lg border border-hairline bg-canvas overflow-hidden relative shadow-card select-none font-sans">
      {/* Floating Canvas Action Toolbar */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-1.5 p-1 rounded-md bg-surface-1/90 backdrop-blur-md border border-hairline shadow-card">
        <button
          type="button"
          onClick={handleTidyUp}
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-ink hover:bg-surface-2 rounded-md transition-colors"
          title="Auto-organize DAG into clean hierarchical layers"
        >
          <Sparkles size={12} className="text-linear-primary" />
          <span>Tidy Up</span>
        </button>

        {/* Add Block Palette Dropdown */}
        {!readOnly && (
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowBlockPalette(!showBlockPalette)}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors"
              title="Add a block to the workflow DAG"
            >
              <Plus size={12} />
              <span>Add Block</span>
              <ChevronDown size={11} className={`transition-transform ${showBlockPalette ? "rotate-180" : ""}`} />
            </button>

            {showBlockPalette && (
              <div className="absolute left-0 top-full mt-1.5 w-52 p-1 rounded-md bg-surface-1 border border-hairline shadow-card z-50 space-y-0.5">
                <button
                  type="button"
                  onClick={() => handleAddBlock("agent")}
                  className="w-full text-left px-2 py-1.5 rounded text-xs text-ink hover:bg-surface-2 flex items-center gap-2"
                >
                  <Bot size={13} className="text-linear-primary" />
                  <div>
                    <div className="font-medium">Agent Step</div>
                    <div className="text-[10px] text-ink-subtle">Specialist LLM agent</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleAddBlock("condition")}
                  className="w-full text-left px-2 py-1.5 rounded text-xs text-ink hover:bg-surface-2 flex items-center gap-2"
                >
                  <GitBranch size={13} className="text-amber-400" />
                  <div>
                    <div className="font-medium">Condition Branch</div>
                    <div className="text-[10px] text-ink-subtle">If / Else routing</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleAddBlock("python_code")}
                  className="w-full text-left px-2 py-1.5 rounded text-xs text-ink hover:bg-surface-2 flex items-center gap-2"
                >
                  <Terminal size={13} className="text-emerald-400" />
                  <div>
                    <div className="font-medium">Python Processor</div>
                    <div className="text-[10px] text-ink-subtle">Sandboxed data compute</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleAddBlock("loop")}
                  className="w-full text-left px-2 py-1.5 rounded text-xs text-ink hover:bg-surface-2 flex items-center gap-2"
                >
                  <RotateCcw size={13} className="text-cyan-400" />
                  <div>
                    <div className="font-medium">Loop Block</div>
                    <div className="text-[10px] text-ink-subtle">Iterate to step (max 10x)</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleAddBlock("artifact")}
                  className="w-full text-left px-2 py-1.5 rounded text-xs text-ink hover:bg-surface-2 flex items-center gap-2"
                >
                  <FileOutput size={13} className="text-purple-400" />
                  <div>
                    <div className="font-medium">Artifact Generator</div>
                    <div className="text-[10px] text-ink-subtle">Reports & structured files</div>
                  </div>
                </button>
              </div>
            )}
          </div>
        )}

        {onRunSystemTest && (
          <button
            type="button"
            onClick={onRunSystemTest}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-ink hover:bg-surface-2 rounded-md transition-colors border-l border-hairline pl-2"
            title="Run end-to-end system test with custom inputs"
          >
            <Play size={11} className="fill-current text-semantic-success" />
            <span>Test DAG</span>
          </button>
        )}
      </div>

      {/* Floating Canvas Legend */}
      <div className="absolute bottom-3 right-3 z-10 hidden sm:flex items-center gap-3 px-3 py-1.5 rounded-md bg-surface-1/90 backdrop-blur-md border border-hairline text-[10px] font-mono text-ink-subtle shadow-card">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-0.5 bg-linear-primary" />
          <span>Linear Flow</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-0.5 bg-emerald-500" />
          <span>True Branch</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-0.5 bg-rose-500" />
          <span>False Branch</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-0.5 bg-cyan-400" />
          <span>Loop Back</span>
        </div>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={rfEdges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodesDraggable={!readOnly}
        nodesConnectable={!readOnly}
        fitView
      >
        <Controls className="!bg-surface-1 !border !border-hairline !rounded-md !shadow-card !text-ink" />
        <MiniMap
          className="!bg-surface-1 !border !border-hairline !rounded-md !shadow-card"
          nodeColor={() => "#5e6ad2"}
          maskColor="rgba(1, 1, 2, 0.7)"
        />
        <Background
          variant={BackgroundVariant.Dots}
          gap={18}
          size={1}
          color="#23252a"
        />
      </ReactFlow>
    </div>
  );
}
