"use client";

import React from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  EdgeProps,
  getBezierPath,
} from "@xyflow/react";
import { X } from "lucide-react";

export interface DataFlowEdgeData {
  payloadLabel?: string;
  onDeleteEdge?: (edgeId: string) => void;
}

export default function DataFlowEdge({
  id,
  source,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
  selected,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const edgeData = data as DataFlowEdgeData | undefined;
  const payloadLabel =
    edgeData?.payloadLabel ||
    (source === "goal_root"
      ? "{{inputs.query}}"
      : `{{steps.${source}.output.text}}`);

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke: selected ? "#828fff" : "#5e6ad2",
          strokeWidth: selected ? 2.5 : 1.75,
          strokeDasharray: "4 3",
          ...style,
        }}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: "absolute",
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: "all",
          }}
          className="group cursor-pointer select-none"
        >
          <div
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded-pill text-[10px] font-mono border backdrop-blur-md shadow-card transition-colors ${
              selected
                ? "bg-surface-2 border-linear-hover text-ink"
                : "bg-surface-1 border-hairline hover:border-hairline-strong text-ink-muted hover:text-ink"
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-linear-primary animate-pulse shrink-0" />
            <span className="truncate max-w-[160px]">{payloadLabel}</span>
            {edgeData?.onDeleteEdge && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  edgeData.onDeleteEdge?.(id);
                }}
                className="opacity-0 group-hover:opacity-100 hover:text-red-400 p-0.5 rounded transition-opacity"
                title="Disconnect edge"
              >
                <X size={10} />
              </button>
            )}
          </div>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
