"use client";

import React, { useState } from "react";
import { WorkflowRun, WorkflowStepRun } from "../types";
import {
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  Coins,
  ChevronRight,
  ChevronDown,
  Zap,
  Bot,
  AlertTriangle,
  Play,
} from "lucide-react";

interface WorkflowRunsDebuggerProps {
  runs: WorkflowRun[];
  onRefreshRuns: () => void;
  onTriggerRun?: () => void;
  isRunning?: boolean;
}

export default function WorkflowRunsDebugger({
  runs,
  onRefreshRuns,
  onTriggerRun,
  isRunning = false,
}: WorkflowRunsDebuggerProps) {
  const [selectedRun, setSelectedRun] = useState<WorkflowRun | null>(runs[0] || null);
  const [expandedStepId, setExpandedStepId] = useState<string | null>(null);

  // Sync selected run if runs update
  React.useEffect(() => {
    if (runs.length > 0 && (!selectedRun || !runs.find((r) => r.id === selectedRun.id))) {
      setSelectedRun(runs[0]);
    }
  }, [runs, selectedRun]);

  return (
    <div className="space-y-6">
      {/* Runs Header & Quick Action */}
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div>
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Activity size={16} className="text-primary" /> Execution Telemetry & Runs Debugger
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Audit logs, step latency metrics, token consumption, and tool execution traces.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRefreshRuns}
            className="px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground border border-border bg-card rounded-xl transition"
          >
            Refresh Logs
          </button>
          {onTriggerRun && (
            <button
              disabled={isRunning}
              onClick={onTriggerRun}
              className="px-3.5 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-xl hover:opacity-90 disabled:opacity-50 transition flex items-center gap-1.5 shadow-subtle"
            >
              <Play size={13} className="fill-current" />
              {isRunning ? "Executing..." : "Run System Test"}
            </button>
          )}
        </div>
      </div>

      {runs.length === 0 ? (
        <div className="p-12 text-center border-2 border-dashed border-border/80 rounded-2xl bg-card/40">
          <Activity className="w-10 h-10 text-muted-foreground opacity-40 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-foreground">No execution runs recorded</h4>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto mt-1 mb-4">
            Execute a system test run or invoke this workflow from the chat interface to view debugging logs.
          </p>
          {onTriggerRun && (
            <button
              onClick={onTriggerRun}
              className="px-4 py-2 bg-primary text-primary-foreground text-xs font-medium rounded-xl hover:opacity-90 transition shadow-subtle"
            >
              Run First Test Execution
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Runs List Table */}
          <div className="lg:col-span-5 space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {runs.map((run) => {
              const isSelected = selectedRun?.id === run.id;
              const isSuccess = run.status === "completed";
              const isFailed = run.status === "failed";

              return (
                <div
                  key={run.id}
                  onClick={() => setSelectedRun(run)}
                  className={`p-3.5 rounded-xl border text-left cursor-pointer transition ${
                    isSelected
                      ? "bg-primary/10 border-primary/40 shadow-subtle"
                      : "bg-card border-border/70 hover:border-border"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                      {isSuccess ? (
                        <CheckCircle2 size={14} className="text-emerald-500" />
                      ) : isFailed ? (
                        <XCircle size={14} className="text-destructive" />
                      ) : (
                        <Clock size={14} className="text-amber-500 animate-spin" />
                      )}
                      Run #{run.id.slice(0, 8)}
                    </span>
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 bg-muted text-muted-foreground rounded">
                      {run.trigger_type}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock size={11} /> {run.duration_ms}ms
                    </span>
                    <span className="flex items-center gap-1">
                      <Coins size={11} className="text-primary" /> {run.total_tokens} tokens
                    </span>
                    <span>
                      {new Date(run.created_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right: Selected Run Deep Inspector */}
          <div className="lg:col-span-7 p-5 rounded-2xl bg-card border border-border/80 shadow-subtle space-y-4">
            {selectedRun ? (
              <div className="space-y-4">
                {/* Header Summary */}
                <div className="flex items-center justify-between pb-3 border-b border-border">
                  <div>
                    <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
                      Run #{selectedRun.id}
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase ${
                          selectedRun.status === "completed"
                            ? "bg-emerald-500/15 text-emerald-500 border border-emerald-500/30"
                            : selectedRun.status === "failed"
                            ? "bg-destructive/15 text-destructive border border-destructive/30"
                            : "bg-amber-500/15 text-amber-500 border border-amber-500/30"
                        }`}
                      >
                        {selectedRun.status}
                      </span>
                    </h4>
                    <p className="text-[11px] text-muted-foreground mt-0.5 font-mono">
                      Started: {new Date(selectedRun.created_at).toLocaleString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-3 text-xs">
                    <div className="text-right">
                      <span className="text-[10px] text-muted-foreground block">Duration</span>
                      <span className="font-semibold text-foreground">{selectedRun.duration_ms} ms</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-muted-foreground block">Tokens</span>
                      <span className="font-semibold text-primary">{selectedRun.total_tokens}</span>
                    </div>
                  </div>
                </div>

                {selectedRun.error && (
                  <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
                    <AlertTriangle size={15} className="shrink-0" />
                    <span>{selectedRun.error}</span>
                  </div>
                )}

                {/* Final Result Card */}
                {selectedRun.output_data?.final_result && (
                  <div className="p-3.5 rounded-xl bg-background border border-border">
                    <span className="text-xs font-semibold text-foreground block mb-1">
                      Final Synthesized Outcome
                    </span>
                    <p className="text-xs text-foreground/90 leading-relaxed whitespace-pre-wrap">
                      {selectedRun.output_data.final_result}
                    </p>
                  </div>
                )}

                {/* Step-by-Step Breakdown Timeline */}
                <div>
                  <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                    Step Execution Breakdown ({selectedRun.step_runs?.length || 0} Steps)
                  </h5>

                  <div className="space-y-2">
                    {(!selectedRun.step_runs || selectedRun.step_runs.length === 0) ? (
                      <p className="text-xs text-muted-foreground italic">No step breakdown records.</p>
                    ) : (
                      selectedRun.step_runs.map((stepRun: WorkflowStepRun) => {
                        const isExpanded = expandedStepId === stepRun.id;
                        const isStepSuccess = stepRun.status === "completed";

                        return (
                          <div
                            key={stepRun.id}
                            className="rounded-xl border border-border/70 bg-background/50 overflow-hidden"
                          >
                            <div
                              onClick={() => setExpandedStepId(isExpanded ? null : stepRun.id)}
                              className="p-3 flex items-center justify-between cursor-pointer hover:bg-muted/40 transition"
                            >
                              <div className="flex items-center gap-2">
                                {isStepSuccess ? (
                                  <CheckCircle2 size={14} className="text-emerald-500 shrink-0" />
                                ) : (
                                  <XCircle size={14} className="text-destructive shrink-0" />
                                )}
                                <span className="text-xs font-semibold text-foreground">
                                  {stepRun.step_id}
                                </span>
                                <span className="text-[10px] text-primary bg-primary/10 px-1.5 py-0.2 rounded border border-primary/20 flex items-center gap-1">
                                  <Bot size={10} /> {stepRun.agent_id}
                                </span>
                              </div>

                              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                <span>{stepRun.duration_ms}ms</span>
                                <span>{stepRun.tokens_used} tok</span>
                                {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                              </div>
                            </div>

                            {/* Expanded Details */}
                            {isExpanded && (
                              <div className="p-3 pt-0 border-t border-border/50 text-xs space-y-2 bg-card/60">
                                {stepRun.prompt_rendered && (
                                  <div>
                                    <span className="text-[10px] font-semibold text-muted-foreground block mb-0.5">
                                      Rendered Prompt:
                                    </span>
                                    <p className="font-mono text-[11px] text-foreground/80 bg-background p-2 rounded border border-border/50">
                                      {stepRun.prompt_rendered}
                                    </p>
                                  </div>
                                )}

                                {stepRun.tool_calls && stepRun.tool_calls.length > 0 && (
                                  <div>
                                    <span className="text-[10px] font-semibold text-muted-foreground block mb-0.5 flex items-center gap-1">
                                      <Zap size={11} className="text-amber-500" /> Tool Calls:
                                    </span>
                                    <div className="space-y-1">
                                      {stepRun.tool_calls.map((tc, idx) => (
                                        <div key={idx} className="p-2 rounded bg-background border border-border/50 font-mono text-[10px]">
                                          <div className="flex justify-between text-muted-foreground mb-1">
                                            <span>Tool: {tc.tool_name}</span>
                                            <span>{tc.duration_ms}ms</span>
                                          </div>
                                          <pre className="text-foreground">{JSON.stringify(tc.result, null, 2)}</pre>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {stepRun.output_data && (
                                  <div>
                                    <span className="text-[10px] font-semibold text-muted-foreground block mb-0.5">
                                      Step Output:
                                    </span>
                                    <pre className="font-mono text-[11px] text-foreground/90 bg-background p-2 rounded border border-border/50 whitespace-pre-wrap">
                                      {typeof stepRun.output_data.text === "string"
                                        ? stepRun.output_data.text
                                        : JSON.stringify(stepRun.output_data, null, 2)}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
