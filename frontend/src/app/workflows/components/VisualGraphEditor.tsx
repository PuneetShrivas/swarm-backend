"use client";

import React, { useMemo, useCallback } from "react";
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
import { WorkflowStep, ScriptTool, KnowledgeFile } from "../types";
import DataFlowEdge from "./DataFlowEdge";
import {
  Bot,
  Zap,
  FileText,
  Play,
  Flag,
  Plus,
  Trash2,
  Sparkles,
  Layers,
  Search,
  Code2,
  ShieldCheck,
  BarChart2,
  FolderOpen,
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

// ----------------- Custom Node Components -----------------

// 1. Goal Root Node (Linear Style)
function GoalNode({ data }: NodeProps) {
  return (
    <div className="p-4 rounded-lg bg-surface-1 border border-hairline hover:border-hairline-strong transition-colors shadow-card min-w-[260px] max-w-[300px] select-none font-sans">
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

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2.5 !h-2.5 !bg-linear-primary !border-2 !border-canvas hover:!scale-125 transition-transform"
      />
    </div>
  );
}

// 2. Step Agent Node (Linear Style)
function StepNode({ data }: NodeProps) {
  const step = data?.step as WorkflowStep;
  const onUnitTest = data?.onUnitTest as ((step: WorkflowStep) => void) | undefined;
  const onDeleteStep = data?.onDeleteStep as ((stepId: string) => void) | undefined;
  const agentName = (data?.agentName as string) || step?.agent_id || "Specialist Agent";
  const agentRole = (data?.agentRole as string) || "Agent executor";
  const stepIndex = (data?.stepIndex as number) ?? 1;

  const getAgentAvatar = (id?: string) => {
    switch (id) {
      case "orchestrator":
        return <Layers size={12} className="text-linear-primary" />;
      case "researcher":
        return <Search size={12} className="text-ink-muted" />;
      case "coder":
        return <Code2 size={12} className="text-semantic-success" />;
      case "reviewer":
        return <ShieldCheck size={12} className="text-ink-muted" />;
      case "data_analyst":
        return <BarChart2 size={12} className="text-ink-muted" />;
      case "synthesizer":
        return <FileText size={12} className="text-ink-muted" />;
      default:
        return <Bot size={12} className="text-linear-primary" />;
    }
  };

  return (
    <div className="p-4 rounded-lg bg-surface-1 border border-hairline hover:border-hairline-strong transition-colors shadow-card min-w-[280px] max-w-[320px] select-none font-sans group">
      <Handle
        type="target"
        position={Position.Top}
        className="!w-2.5 !h-2.5 !bg-linear-primary !border-2 !border-canvas hover:!scale-125 transition-transform"
      />

      {/* Step Header */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-hairline">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-6 h-6 rounded-md bg-surface-2 border border-hairline flex items-center justify-center shrink-0">
            {getAgentAvatar(step?.agent_id)}
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
            <span className="text-[10px] text-ink-subtle block truncate">
              {agentName} • {agentRole}
            </span>
          </div>
        </div>

        {/* Action Buttons: Unit Test + Delete */}
        <div className="flex items-center gap-1 shrink-0 ml-1">
          {onUnitTest && (
            <button
              onClick={() => onUnitTest(step)}
              className="p-1 rounded-md text-ink-subtle hover:text-semantic-success hover:bg-surface-2 transition-colors"
              title="Unit test this step"
            >
              <Play size={11} className="fill-current" />
            </button>
          )}
          {onDeleteStep && (
            <button
              onClick={() => onDeleteStep(step.id)}
              className="p-1 rounded-md text-ink-subtle hover:text-red-400 hover:bg-surface-2 transition-colors opacity-0 group-hover:opacity-100"
              title="Delete step"
            >
              <Trash2 size={11} />
            </button>
          )}
        </div>
      </div>

      {/* Instruction Preview with Highlighted Variables */}
      <div className="text-[11px] font-mono text-ink-subtle line-clamp-2 bg-canvas p-2 rounded-md border border-hairline mb-2.5 leading-relaxed">
        {renderInstructionTokens(step?.instructions)}
      </div>

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
              <span className="text-ink-tertiary font-mono text-[9px]">direct prompt</span>
            )}
        </div>

        <span className="font-mono text-[9px] text-ink-tertiary">
          output: text
        </span>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2.5 !h-2.5 !bg-linear-primary !border-2 !border-canvas hover:!scale-125 transition-transform"
      />
    </div>
  );
}

// ----------------- Layout Calculation ("Tidy Up") -----------------
function calculateDAGLayout(
  goal: string,
  steps: WorkflowStep[],
  edges: Array<{ id: string; source: string; target: string }>,
  agents: Array<{ id: string; name: string; role?: string }>,
  onUnitTestStep?: (step: WorkflowStep) => void,
  onDeleteStep?: (stepId: string) => void
): Node[] {
  // Determine topological depth/level for each step
  const levels: Record<string, number> = { goal_root: 0 };

  // Calculate dependency depth
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

  // Group steps by level
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
      position: { x: 340, y: 30 },
      data: { goal },
    },
  ];

  Object.entries(byLevel).forEach(([lvlStr, levelSteps]) => {
    const lvl = parseInt(lvlStr, 10);
    const count = levelSteps.length;
    const spacingX = 340;
    const startX = 340 - ((count - 1) * spacingX) / 2;
    const posY = 30 + lvl * 220;

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
          onUnitTest: onUnitTestStep,
          onDeleteStep: onDeleteStep,
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
  onUnitTestStep,
  readOnly = false,
}: VisualGraphEditorProps) {
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

  // Delete edge handler
  const handleDeleteEdge = useCallback(
    (edgeId: string) => {
      if (readOnly) return;
      const [src, tgt] = edgeId.split("->");

      // Sever dependency on target step
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
        }));

      const nextEdges = edges.filter((e) => e.source !== stepId && e.target !== stepId);

      onChangeSteps(nextSteps);
      onChangeEdges(nextEdges);
    },
    [readOnly, steps, edges, onChangeSteps, onChangeEdges]
  );

  // Generate initial React Flow nodes with layout
  const computedNodes: Node[] = useMemo(() => {
    return calculateDAGLayout(
      goal,
      steps,
      edges,
      agents,
      onUnitTestStep,
      handleDeleteStep
    );
  }, [goal, steps, edges, agents, onUnitTestStep, handleDeleteStep]);

  // Generate React Flow edges with payload labels & custom DataFlowEdge
  const computedEdges: Edge[] = useMemo(() => {
    const edgeMap = new Map<string, Edge>();

    // 1. Edges from explicit depends_on
    steps.forEach((step) => {
      if (step.depends_on.length === 0) {
        const edgeId = `goal_root->${step.id}`;
        edgeMap.set(edgeId, {
          id: edgeId,
          type: "dataFlowEdge",
          source: "goal_root",
          target: step.id,
          animated: true,
          data: {
            payloadLabel: "{{inputs.query}}",
            onDeleteEdge: handleDeleteEdge,
          },
        });
      } else {
        step.depends_on.forEach((depId) => {
          const edgeId = `${depId}->${step.id}`;
          edgeMap.set(edgeId, {
            id: edgeId,
            type: "dataFlowEdge",
            source: depId,
            target: step.id,
            animated: true,
            data: {
              payloadLabel: `{{steps.${depId}.output.text}}`,
              onDeleteEdge: handleDeleteEdge,
            },
          });
        });
      }
    });

    // 2. Extra edges passed from props
    edges.forEach((e) => {
      const edgeId = `${e.source}->${e.target}`;
      if (!edgeMap.has(edgeId)) {
        edgeMap.set(edgeId, {
          id: edgeId,
          type: "dataFlowEdge",
          source: e.source,
          target: e.target,
          animated: true,
          data: {
            payloadLabel:
              e.source === "goal_root"
                ? "{{inputs.query}}"
                : `{{steps.${e.source}.output.text}}`,
            onDeleteEdge: handleDeleteEdge,
          },
        });
      }
    });

    return Array.from(edgeMap.values());
  }, [steps, edges, handleDeleteEdge]);

  const [nodes, setNodes, onNodesChange] = useNodesState(computedNodes);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState(computedEdges);

  // Sync state if computed nodes or edges change
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

      // Update underlying step depends_on
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

  // Quick Action: Add new step directly in the DAG
  const handleQuickAddStep = () => {
    if (readOnly) return;
    const nextIdx = steps.length + 1;
    const newStepId = `step_${nextIdx}`;
    const previousStepId = steps.length > 0 ? steps[steps.length - 1].id : "goal_root";

    const newStep: WorkflowStep = {
      id: newStepId,
      name: `Step ${nextIdx}: Analysis & Execution`,
      agent_id: agents.length > 1 ? agents[1].id : "researcher",
      instructions:
        previousStepId === "goal_root"
          ? "Process input objective: {{inputs.query}}"
          : `Synthesize input from predecessor: {{steps.${previousStepId}.output.text}}`,
      tool_ids: [],
      knowledge_file_ids: [],
      depends_on: previousStepId === "goal_root" ? [] : [previousStepId],
    };

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
  };

  // Quick Action: Tidy Up (Recalculate auto-layout)
  const handleTidyUp = () => {
    const laidOut = calculateDAGLayout(
      goal,
      steps,
      edges,
      agents,
      onUnitTestStep,
      handleDeleteStep
    );
    setNodes(laidOut);
  };

  return (
    <div className="w-full h-[650px] rounded-lg border border-hairline bg-canvas overflow-hidden relative shadow-card select-none font-sans">
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

        {!readOnly && (
          <button
            type="button"
            onClick={handleQuickAddStep}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors"
            title="Append a new step to the workflow DAG"
          >
            <Plus size={12} />
            <span>Add Step</span>
          </button>
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
          <span>Data Flow Edge</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-semantic-success" />
          <span>Output Ready</span>
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
