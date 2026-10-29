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
  edgeType?: "normal" | "true_branch" | "false_branch" | "loop_back";
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
  const edgeType = edgeData?.edgeType || "normal";

  const getEdgeColor = () => {
    if (selected) return "#828fff";
    switch (edgeType) {
      case "true_branch":
        return "#10b981"; // emerald-500
      case "false_branch":
        return "#f43f5e"; // rose-500
      case "loop_back":
        return "#06b6d4"; // cyan-500
      default:
        return "#5e6ad2"; // linear primary
    }
  };

  const payloadLabel =
    edgeData?.payloadLabel ||
    (source === "goal_root"
      ? "{{inputs.query}}"
      : `{{steps.${source}.output.text}}`);

  const edgeColor = getEdgeColor();

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke: edgeColor,
          strokeWidth: selected ? 2.5 : 1.75,
          strokeDasharray: edgeType === "loop_back" ? "6 3" : "4 3",
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
            <span
              className="w-1.5 h-1.5 rounded-full shrink-0"
              style={{ backgroundColor: edgeColor }}
            />
            {edgeType === "true_branch" && (
              <span className="text-emerald-400 font-semibold text-[9px]">TRUE</span>
            )}
            {edgeType === "false_branch" && (
              <span className="text-rose-400 font-semibold text-[9px]">FALSE</span>
            )}
            {edgeType === "loop_back" && (
              <span className="text-cyan-400 font-semibold text-[9px]">LOOP</span>
            )}
            <span className="truncate max-w-[150px]">{payloadLabel}</span>
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
