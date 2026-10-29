"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Clock,
  Coins,
  Wrench,
  BookmarkPlus,
  Workflow,
  Sparkles,
  Bot,
} from "lucide-react";

export interface StepRunItem {
  id?: string;
  step_id?: string;
  step_index?: number;
  agent_id?: string;
  status?: string;
  duration_ms?: number;
  tokens_used?: number;
  tool_calls?: Array<{ tool: string; args?: Record<string, unknown>; result?: Record<string, unknown> }>;
  prompt_rendered?: string;
  output_data?: { text?: string; artifacts?: unknown[] };
}

export interface GranularTraceItem {
  timestamp?: string;
  phase?: string;
  label?: string;
  event_type?: string;
  step_id?: string;
  step_name?: string;
  agent_id?: string;
  duration_ms?: number;
  tokens_used?: number;
  status?: string;
}

export interface WorkflowSpec {
  id?: string;
  title?: string;
  goal?: string;
  description?: string;
  is_multi_step?: boolean;
  steps?: Array<{
    id: string;
    name: string;
    agent_id?: string;
    model?: string;
    instructions?: string;
    step_type?: string;
  }>;
  edges?: Array<{ id?: string; source: string; target: string }>;
}

export interface GranularStepTraceProps {
  metadata?: Record<string, unknown>;
  onOpenSaveModal?: (spec: WorkflowSpec) => void;
}

export function GranularStepTrace({
  metadata,
  onOpenSaveModal,
}: GranularStepTraceProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedStepId, setExpandedStepId] = useState<string | null>(null);

  if (!metadata) return null;

  const isEphemeral = Boolean(metadata.is_ephemeral_workflow);
  const isMultiStep = Boolean(metadata.is_multi_step);
  const workflowTitle = String(
    metadata.workflow_title || metadata.agent_name || "Autonomous Workflow Execution"
  );
  const workflowGoal = metadata.workflow_goal ? String(metadata.workflow_goal) : "";
  const stepRuns = Array.isArray(metadata.step_runs)
    ? (metadata.step_runs as StepRunItem[])
    : [];
  const granularTrace = Array.isArray(metadata.granular_trace)
    ? (metadata.granular_trace as GranularTraceItem[])
    : [];
  const workflowSpec = (metadata.workflow_spec as WorkflowSpec) || null;

  // Total metrics
  const totalTokens = Number(metadata.tokens_used) || 0;
  const totalDurationMs = Number(metadata.duration_ms) || Number(metadata.latency_ms) || 0;

  // Don't render if there's no step information
  if (stepRuns.length === 0 && granularTrace.length === 0 && !workflowSpec) {
    return null;
  }

  const formatElapsed = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const getAgentColor = (agentId?: string) => {
    switch (agentId) {
      case "researcher":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "coder":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "data_analyst":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "reviewer":
        return "bg-purple-500/10 text-purple-400 border-purple-500/20";
      case "file_creator":
        return "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";
      case "file_parser":
        return "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
      default:
        return "bg-linear-primary/10 text-linear-primary border-linear-primary/20";
    }
  };

  return (
    <div className="mt-3 rounded-lg border border-hairline bg-surface-2/40 overflow-hidden font-sans select-none">
      {/* Header bar */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="px-3.5 py-2.5 bg-surface-2/80 hover:bg-surface-2 flex items-center justify-between gap-3 cursor-pointer transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          <Workflow size={14} className="text-linear-primary shrink-0" />
          <span className="text-xs font-semibold text-ink truncate">
            {workflowTitle}
          </span>
          {isMultiStep ? (
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-linear-primary/10 text-linear-primary border border-linear-primary/20 shrink-0">
              {stepRuns.length || workflowSpec?.steps?.length || 2} Steps
            </span>
          ) : (
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-surface-3 text-ink-subtle border border-hairline shrink-0">
              1-Agent Step
            </span>
          )}
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          {totalDurationMs > 0 && (
            <span className="flex items-center gap-1 text-[11px] font-mono text-ink-subtle">
              <Clock size={11} className="text-ink-subtle" />
              {formatElapsed(totalDurationMs)}
            </span>
          )}

          {totalTokens > 0 && (
            <span className="hidden sm:flex items-center gap-1 text-[11px] font-mono text-ink-subtle">
              <Coins size={11} className="text-ink-subtle" />
              {totalTokens} tokens
            </span>
          )}

          <div className="p-1 rounded-md text-ink-subtle hover:text-ink">
            {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </div>
        </div>
      </div>

      {/* Ephemeral Workflow "Save as Workflow" Banner */}
      {isEphemeral && workflowSpec && (
        <div className="px-3.5 py-2 bg-linear-primary/5 border-t border-b border-linear-primary/20 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-[11px] text-ink-subtle">
            <Sparkles size={12} className="text-linear-primary shrink-0" />
            <span>
              On-the-fly workflow generated for this query. Not saved in your permanent workflows.
            </span>
          </div>

          {onOpenSaveModal && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onOpenSaveModal(workflowSpec);
              }}
              className="px-2.5 py-1 rounded-md bg-linear-primary hover:bg-linear-hover text-white text-[11px] font-medium inline-flex items-center gap-1.5 transition-all shrink-0 cursor-pointer shadow-xs active:scale-95"
            >
              <BookmarkPlus size={12} />
              <span>Save as Workflow</span>
            </button>
          )}
        </div>
      )}

      {/* Expandable Trace Details */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="p-3.5 space-y-3 bg-canvas/60"
          >
            {workflowGoal && (
              <p className="text-[11px] text-ink-subtle font-mono border-l-2 border-linear-primary/40 pl-2">
                <strong className="text-ink font-medium">Goal:</strong> {workflowGoal}
              </p>
            )}

            {/* Granular Execution Steps */}
            <div className="space-y-2">
              <div className="text-[10px] font-mono uppercase tracking-wider text-ink-subtle flex items-center gap-1">
                <Bot size={11} className="text-ink-subtle" />
                <span>Granular Step Traces ({stepRuns.length})</span>
              </div>

              {stepRuns.map((step, idx) => {
                const sId = step.step_id || `step_${idx + 1}`;
                const isStepExpanded = expandedStepId === sId;
                const toolCalls = step.tool_calls || [];
                const previewText = step.output_data?.text || "";

                return (
                  <div
                    key={sId}
                    className="rounded-lg border border-hairline bg-surface-1/90 overflow-hidden text-xs"
                  >
                    <div
                      onClick={() => setExpandedStepId(isStepExpanded ? null : sId)}
                      className="px-3 py-2 flex items-center justify-between gap-2 hover:bg-surface-2/60 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />
                        <span className="font-mono font-medium text-ink truncate">
                          {idx + 1}. {sId}
                        </span>
                        {step.agent_id && (
                          <span
                            className={`text-[10px] font-mono px-1.5 py-0.5 rounded border shrink-0 ${getAgentColor(
                              step.agent_id
                            )}`}
                          >
                            @{step.agent_id}
                          </span>
                        )}
                        {toolCalls.length > 0 && (
                          <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-mono text-ink-subtle px-1.5 py-0.2 rounded bg-surface-2 border border-hairline shrink-0">
                            <Wrench size={9} />
                            {toolCalls.length} tool{toolCalls.length > 1 ? "s" : ""}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-[10px] font-mono text-ink-subtle shrink-0">
                        {step.tokens_used ? (
                          <span className="flex items-center gap-0.5">
                            <Coins size={9} />
                            {step.tokens_used}
                          </span>
                        ) : null}
                        {step.duration_ms ? (
                          <span>{formatElapsed(step.duration_ms)}</span>
                        ) : null}
                        {isStepExpanded ? (
                          <ChevronUp size={12} />
                        ) : (
                          <ChevronDown size={12} />
                        )}
                      </div>
                    </div>

                    {/* Step Expanded Content */}
                    <AnimatePresence>
                      {isStepExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.15 }}
                          className="px-3 py-2.5 bg-surface-2/40 border-t border-hairline space-y-2 font-mono text-[11px]"
                        >
                          {/* Tool Calls */}
                          {toolCalls.length > 0 && (
                            <div className="space-y-1">
                              <span className="text-[10px] uppercase text-ink-subtle font-semibold">
                                Tool Invocations:
                              </span>
                              {toolCalls.map((tc, tIdx) => (
                                <div
                                  key={tIdx}
                                  className="p-1.5 rounded bg-surface-3 border border-hairline flex items-center justify-between gap-2"
                                >
                                  <span className="text-linear-primary font-semibold">
                                    {tc.tool}
                                  </span>
                                  <span className="text-ink-subtle text-[10px] truncate max-w-xs">
                                    {JSON.stringify(tc.args || {})}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Output Preview */}
                          {previewText && (
                            <div className="space-y-1">
                              <span className="text-[10px] uppercase text-ink-subtle font-semibold">
                                Step Output Preview:
                              </span>
                              <div className="p-2 rounded bg-surface-3 border border-hairline text-ink-subtle max-h-32 overflow-y-auto whitespace-pre-wrap font-sans text-xs">
                                {previewText.slice(0, 400)}
                                {previewText.length > 400 ? "..." : ""}
                              </div>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>

            {/* Granular Event Phase Timeline */}
            {granularTrace.length > 0 && (
              <div className="pt-2 border-t border-hairline space-y-1.5">
                <span className="text-[10px] font-mono uppercase tracking-wider text-ink-subtle">
                  Orchestrator Lifecycle Milestones
                </span>
                <div className="space-y-1">
                  {granularTrace.map((gt, gIdx) => (
                    <div
                      key={gIdx}
                      className="flex items-center justify-between text-[11px] font-mono text-ink-subtle py-0.5"
                    >
                      <span className="flex items-center gap-1.5 truncate">
                        <span className="w-1.5 h-1.5 rounded-full bg-linear-primary" />
                        <span className="text-ink">{gt.label || gt.phase}</span>
                      </span>
                      {gt.duration_ms ? (
                        <span className="shrink-0">{formatElapsed(gt.duration_ms)}</span>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
