"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  Workflow,
  Cpu,
  Clock,
  Coins,
  ChevronDown,
  ChevronUp,
  Square,
  Sparkles,
  Bot,
  Terminal,
} from "lucide-react";

export interface LiveStepEvent {
  step_id: string;
  step_name?: string;
  step_index?: number;
  total_steps?: number;
  agent_id?: string;
  model?: string;
  duration_ms?: number;
  tokens_used?: number;
  output_preview?: string;
  tool_calls?: Array<{ tool: string; args?: Record<string, unknown> }>;
  status: "pending" | "running" | "completed" | "failed";
}

export interface LiveWorkflowPlan {
  id?: string;
  title: string;
  goal?: string;
  is_multi_step?: boolean;
  total_steps: number;
  steps?: Array<{
    id: string;
    name: string;
    agent_id?: string;
    model?: string;
  }>;
}

export interface LiveExecutionConsoleProps {
  phaseLabel?: string;
  workflowPlan?: LiveWorkflowPlan | null;
  activeStep?: LiveStepEvent | null;
  completedSteps?: LiveStepEvent[];
  startTime?: number;
  onStop?: () => void;
}

export function LiveExecutionConsole({
  phaseLabel,
  workflowPlan,
  activeStep,
  completedSteps = [],
  startTime,
  onStop,
}: LiveExecutionConsoleProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    if (!startTime) return;
    const interval = setInterval(() => {
      setElapsedMs(Date.now() - startTime);
    }, 100);
    return () => clearInterval(interval);
  }, [startTime]);

  const totalSteps = workflowPlan?.total_steps || Math.max(1, (completedSteps.length + (activeStep ? 1 : 0)));
  const completedCount = completedSteps.length;
  const progressPercent = Math.min(
    100,
    Math.round(((completedCount + (activeStep ? 0.5 : 0)) / totalSteps) * 100)
  );

  const formatElapsed = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const getAgentBadgeColor = (agentId?: string) => {
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
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 6 }}
      transition={{ duration: 0.2 }}
      className="w-full max-w-3xl rounded-xl border border-hairline bg-surface-1 shadow-lg shadow-black/20 overflow-hidden font-sans"
    >
      {/* Console Header Bar */}
      <div className="px-4 py-3 bg-surface-2/60 border-b border-hairline flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="relative flex items-center justify-center">
            <span className="w-2.5 h-2.5 rounded-full bg-linear-primary animate-ping opacity-75" />
            <span className="absolute w-2 h-2 rounded-full bg-linear-primary" />
          </div>

          <div className="flex items-center gap-2 min-w-0">
            <Workflow size={14} className="text-linear-primary shrink-0" />
            <span className="text-xs font-semibold text-ink truncate">
              {workflowPlan?.title || "Swarm Orchestrator Execution"}
            </span>
            {workflowPlan?.is_multi_step ? (
              <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-linear-primary/10 text-linear-primary font-mono border border-linear-primary/20 shrink-0">
                Multi-Agent DAG
              </span>
            ) : (
              <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-surface-3 text-ink-subtle font-mono border border-hairline shrink-0">
                Single Agent
              </span>
            )}
          </div>
        </div>

        {/* Status Metrics & Actions */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-1.5 text-ink-subtle text-[11px] font-mono">
            <Clock size={12} className="text-ink-subtle" />
            <span>{formatElapsed(elapsedMs)}</span>
          </div>

          <div className="hidden sm:flex items-center gap-1 text-[11px] font-mono text-ink-subtle">
            <Cpu size={12} className="text-linear-primary" />
            <span>
              {completedCount}/{totalSteps} steps
            </span>
          </div>

          {onStop && (
            <button
              type="button"
              onClick={onStop}
              title="Stop execution"
              className="p-1.5 rounded-md bg-surface-3 hover:bg-red-500/20 text-ink-subtle hover:text-red-400 border border-hairline hover:border-red-500/30 transition-colors"
            >
              <Square size={12} fill="currentColor" />
            </button>
          )}

          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? "Collapse console" : "Expand console"}
            className="p-1.5 rounded-md hover:bg-surface-3 text-ink-subtle hover:text-ink transition-colors"
          >
            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1 bg-surface-3 overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-linear-primary via-blue-500 to-indigo-500"
          initial={{ width: "5%" }}
          animate={{ width: `${Math.max(5, progressPercent)}%` }}
          transition={{ duration: 0.3, ease: "easeOut" }}
        />
      </div>

      {/* Expandable Console Body */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="p-4 space-y-3.5 bg-surface-1/90"
          >
            {/* Live Phase Banner */}
            {phaseLabel && (
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-2 border border-hairline text-xs text-ink-subtle">
                <Sparkles size={13} className="text-linear-primary shrink-0 animate-pulse" />
                <span className="font-mono text-[11px] truncate">{phaseLabel}</span>
              </div>
            )}

            {/* Currently Active Step (Pulsing Card) */}
            {activeStep ? (
              <div className="p-3.5 rounded-lg border border-linear-primary/30 bg-linear-primary/5 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Loader2 size={14} className="animate-spin text-linear-primary shrink-0" />
                    <span className="text-xs font-semibold text-ink font-mono">
                      {activeStep.step_name || `Executing Step ${activeStep.step_id}`}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {activeStep.agent_id && (
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${getAgentBadgeColor(
                          activeStep.agent_id
                        )}`}
                      >
                        @{activeStep.agent_id}
                      </span>
                    )}
                    {activeStep.model && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-3 text-ink-subtle border border-hairline">
                        {activeStep.model}
                      </span>
                    )}
                  </div>
                </div>

                <div className="text-[11px] text-ink-subtle flex items-center gap-1.5">
                  <Terminal size={12} className="text-linear-primary shrink-0" />
                  <span className="font-mono">
                    Step {(activeStep.step_index ?? 0) + 1} of {totalSteps} in flight...
                  </span>
                </div>
              </div>
            ) : null}

            {/* Completed Steps Trace List */}
            {completedSteps.length > 0 && (
              <div className="space-y-1.5 pt-1">
                <div className="text-[10px] uppercase tracking-wider font-mono text-ink-subtle flex items-center gap-1 px-1">
                  <Bot size={11} className="text-ink-subtle" />
                  <span>Execution Milestone Log ({completedSteps.length})</span>
                </div>

                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {completedSteps.map((step, idx) => (
                    <div
                      key={step.step_id || idx}
                      className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-surface-2/60 border border-hairline text-xs"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        {step.status === "failed" ? (
                          <AlertCircle size={13} className="text-red-400 shrink-0" />
                        ) : (
                          <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />
                        )}
                        <span className="font-mono text-xs text-ink truncate">
                          {step.step_name || step.step_id}
                        </span>
                        {step.agent_id && (
                          <span
                            className={`text-[9px] font-mono px-1.5 py-0.5 rounded border shrink-0 ${getAgentBadgeColor(
                              step.agent_id
                            )}`}
                          >
                            {step.agent_id}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-[10px] font-mono text-ink-subtle shrink-0">
                        {typeof step.tokens_used === "number" && step.tokens_used > 0 && (
                          <span className="flex items-center gap-0.5">
                            <Coins size={10} className="text-ink-subtle" />
                            {step.tokens_used}
                          </span>
                        )}
                        {typeof step.duration_ms === "number" && (
                          <span className="text-ink-subtle">
                            {formatElapsed(step.duration_ms)}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
