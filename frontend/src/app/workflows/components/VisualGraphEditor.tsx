"use client";

import React, { useMemo, useCallback } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
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
import {
  Bot,
  Zap,
  FileText,
  Play,
  Flag,
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
  readOnly?: boolean;
}

// ----------------- Custom Node Components -----------------

// 1. Goal Root Node
function GoalNode({ data }: NodeProps) {
  return (
    <div className="p-4 rounded-2xl bg-card border-2 border-primary/40 shadow-subtle min-w-[240px] max-w-[280px]">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-7 h-7 rounded-lg bg-primary/10 text-primary border border-primary/20 flex items-center justify-center shrink-0">
          <Flag size={14} />
        </div>
        <span className="text-xs font-bold text-foreground">Workflow Goal</span>
      </div>
      <p className="text-[11px] text-muted-foreground line-clamp-3 leading-relaxed">
        {(data?.goal as string) || "Define the high-level objective..."}
      </p>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-primary !border-2 !border-background"
      />
    </div>
  );
}

// 2. Step Agent Node
function StepNode({ data }: NodeProps) {
  const step = data?.step as WorkflowStep;
  const onUnitTest = data?.onUnitTest as ((step: WorkflowStep) => void) | undefined;
  const agentName = (data?.agentName as string) || step?.agent_id || "Agent";

  return (
    <div className="p-4 rounded-2xl bg-card border border-border shadow-subtle min-w-[260px] max-w-[300px] hover:border-primary/40 transition">
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-primary !border-2 !border-background"
      />

      <div className="flex items-center justify-between pb-2 mb-2 border-b border-border/70">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent/15 text-accent border border-accent/25 flex items-center justify-center shrink-0">
            <Bot size={14} />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-foreground truncate max-w-[140px]">
              {step?.name || "Step"}
            </h4>
            <span className="text-[10px] text-muted-foreground block truncate">
              {agentName}
            </span>
          </div>
        </div>

        {onUnitTest && (
          <button
            onClick={() => onUnitTest(step)}
            className="p-1 rounded-lg text-emerald-500 hover:bg-emerald-500/10 transition"
            title="Unit test step"
          >
            <Play size={13} className="fill-current" />
          </button>
        )}
      </div>

      <p className="text-[11px] font-mono text-muted-foreground line-clamp-2 bg-background/60 p-2 rounded-lg border border-border/40 mb-2.5">
        {step?.instructions || "No instructions"}
      </p>

      {/* Badges */}
      <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
        {step?.tool_ids?.length > 0 && (
          <span className="flex items-center gap-1 bg-amber-500/10 text-amber-500 border border-amber-500/20 px-1.5 py-0.5 rounded">
            <Zap size={10} /> {step.tool_ids.length} tools
          </span>
        )}
        {step?.knowledge_file_ids?.length > 0 && (
          <span className="flex items-center gap-1 bg-blue-500/10 text-blue-500 border border-blue-500/20 px-1.5 py-0.5 rounded">
            <FileText size={10} /> {step.knowledge_file_ids.length} docs
          </span>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-primary !border-2 !border-background"
      />
    </div>
  );
}

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
  // Define node types memoized
  const nodeTypes = useMemo(
    () => ({
      goalNode: GoalNode,
      stepNode: StepNode,
    }),
    []
  );

  // Generate initial React Flow nodes from steps & goal
  const initialNodes: Node[] = useMemo(() => {
    const list: Node[] = [
      {
        id: "goal_root",
        type: "goalNode",
        position: { x: 280, y: 30 },
        data: { goal },
      },
    ];

    steps.forEach((step, idx) => {
      const agentObj = agents.find((a) => a.id === step.agent_id);
      const posX = step.position?.x ?? 100 + (idx % 3) * 320;
      const posY = step.position?.y ?? 180 + Math.floor(idx / 3) * 220;

      list.push({
        id: step.id,
        type: "stepNode",
        position: { x: posX, y: posY },
        data: {
          step,
          agentName: agentObj?.name || step.agent_id,
          onUnitTest: onUnitTestStep,
        },
      });
    });

    return list;
  }, [goal, steps, agents, onUnitTestStep]);

  // Generate initial React Flow edges from step dependencies and edge records
  const initialEdges: Edge[] = useMemo(() => {
    const edgeMap = new Map<string, Edge>();

    // 1. Edges from explicit depends_on
    steps.forEach((step) => {
      if (step.depends_on.length === 0) {
        // Connect to goal root by default if no predecessors
        const edgeId = `goal_root->${step.id}`;
        edgeMap.set(edgeId, {
          id: edgeId,
          source: "goal_root",
          target: step.id,
          animated: true,
          style: { stroke: "hsl(var(--primary))", strokeWidth: 2 },
        });
      } else {
        step.depends_on.forEach((depId) => {
          const edgeId = `${depId}->${step.id}`;
          edgeMap.set(edgeId, {
            id: edgeId,
            source: depId,
            target: step.id,
            animated: true,
            style: { stroke: "hsl(var(--primary))", strokeWidth: 2 },
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
          source: e.source,
          target: e.target,
          animated: true,
          style: { stroke: "hsl(var(--primary))", strokeWidth: 2 },
        });
      }
    });

    return Array.from(edgeMap.values());
  }, [steps, edges]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [rfEdges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync state if props change externally
  React.useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  React.useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  // Handle new edge connection
  const onConnect = useCallback(
    (connection: Connection) => {
      if (readOnly || !connection.source || !connection.target) return;

      setEdges((eds) => addEdge({ ...connection, animated: true }, eds));

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
          id: `${connection.source}->${connection.target}`,
          source: connection.source,
          target: connection.target,
        },
      ]);
    },
    [readOnly, steps, edges, onChangeSteps, onChangeEdges, setEdges]
  );

  return (
    <div className="w-full h-[620px] rounded-2xl border border-border/80 bg-background/50 overflow-hidden relative shadow-subtle">
      <ReactFlow
        nodes={nodes}
        edges={rfEdges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodesDraggable={!readOnly}
        nodesConnectable={!readOnly}
        fitView
      >
        <Controls className="!bg-card !border !border-border !rounded-xl !shadow-subtle !text-foreground" />
        <MiniMap
          className="!bg-card !border !border-border !rounded-xl !shadow-subtle"
          nodeColor={() => "hsl(var(--primary))"}
          maskColor="rgba(0, 0, 0, 0.4)"
        />
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
      </ReactFlow>
    </div>
  );
}
