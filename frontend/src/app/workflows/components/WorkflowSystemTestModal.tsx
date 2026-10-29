"use client";

import React, { useState, useEffect, useMemo } from "react";
import { WorkflowStep, WorkflowRun } from "../types";
import { getAuthHeaders } from "@/lib/supabase";
import {
  Play,
  X,
  Bot,
  Zap,
  Clock,
  CheckCircle2,
  XCircle,
  SlidersHorizontal,
  Code,
  Copy,
  Check,
  ChevronRight,
  Layers,
  FileText,
  Activity,
  Sparkles,
} from "lucide-react";

interface WorkflowSystemTestModalProps {
  workflowId: string;
  workflowTitle: string;
  workflowGoal: string;
  steps: WorkflowStep[];
  isOpen: boolean;
  onClose: () => void;
  onRunComplete?: () => void;
  onNavigateToRuns?: () => void;
}

export default function WorkflowSystemTestModal({
  workflowId,
  workflowTitle,
  workflowGoal,
  steps,
  isOpen,
  onClose,
  onRunComplete,
  onNavigateToRuns,
}: WorkflowSystemTestModalProps) {
  const [activeInputMode, setActiveInputMode] = useState<"visual" | "json">("visual");
  const [activeResultTab, setActiveResultTab] = useState<"final" | "artifacts" | "steps" | "raw">("final");
  const [selectedStepIndex, setSelectedStepIndex] = useState<number>(0);

  // Form Inputs state
  const [formInputs, setFormInputs] = useState<Record<string, string>>({});
  const [jsonInputs, setJsonInputs] = useState<string>('{\n  "query": "Sample workflow execution query"\n}');

  // Custom key-value additions
  const [customKey, setCustomKey] = useState("");
  const [customVal, setCustomVal] = useState("");

  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState<WorkflowRun | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Discover all unique inputs.<varName> referenced in any step of the workflow
  const discoveredInputVars = useMemo(() => {
    const vars: string[] = [];
    const regex = /\{\{\s*inputs\.([\w\.\-]+)\s*\}\}/g;

    steps.forEach((step) => {
      if (!step.instructions) return;
      const matches = Array.from(step.instructions.matchAll(regex)).map((m) => m[1]);
      matches.forEach((v) => {
        if (!vars.includes(v)) vars.push(v);
      });
    });

    return vars;
  }, [steps]);

  // Initialize inputs on open
  useEffect(() => {
    if (!isOpen) return;

    const initial: Record<string, string> = {};
    if (discoveredInputVars.length > 0) {
      discoveredInputVars.forEach((v) => {
        initial[v] = `Test input for ${v}`;
      });
    } else {
      initial["query"] = workflowGoal || "Sample pipeline test task";
    }

    setFormInputs(initial);
    setJsonInputs(JSON.stringify(initial, null, 2));
    setRunResult(null);
    setErrorMessage(null);
  }, [isOpen, discoveredInputVars, workflowGoal]);

  const handleInputChange = (key: string, value: string) => {
    const updated = { ...formInputs, [key]: value };
    setFormInputs(updated);
    setJsonInputs(JSON.stringify(updated, null, 2));
  };

  const handleAddCustomInput = () => {
    const trimmedKey = customKey.trim();
    if (!trimmedKey) return;
    const updated = { ...formInputs, [trimmedKey]: customVal };
    setFormInputs(updated);
    setJsonInputs(JSON.stringify(updated, null, 2));
    setCustomKey("");
    setCustomVal("");
  };

  const handleRemoveInput = (key: string) => {
    const copy = { ...formInputs };
    delete copy[key];
    setFormInputs(copy);
    setJsonInputs(JSON.stringify(copy, null, 2));
  };

  if (!isOpen) return null;

  const handleExecuteSystemTest = async () => {
    setIsRunning(true);
    setRunResult(null);
    setErrorMessage(null);

    let parsedInputs: Record<string, unknown> = {};
    if (activeInputMode === "visual") {
      parsedInputs = { ...formInputs };
    } else {
      try {
        parsedInputs = JSON.parse(jsonInputs);
      } catch {
        setErrorMessage("Invalid JSON in Inputs. Please check syntax.");
        setIsRunning(false);
        return;
      }
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const authHeaders = await getAuthHeaders();
      const res = await fetch(`${apiUrl}/api/workflows/${workflowId}/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({ inputs: parsedInputs }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Workflow run failed.");
      }

      const runData: WorkflowRun = await res.json();
      setRunResult(runData);
      setActiveResultTab("final");
      if (onRunComplete) onRunComplete();
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "System execution test failed.");
    } finally {
      setIsRunning(false);
    }
  };

  const handleCopyOutput = () => {
    if (!runResult?.output_data) return;
    const text =
      typeof runResult.output_data.final_result === "string"
        ? runResult.output_data.final_result
        : JSON.stringify(runResult.output_data, null, 2);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const activeStepRun =
    runResult?.step_runs && runResult.step_runs[selectedStepIndex]
      ? runResult.step_runs[selectedStepIndex]
      : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-canvas border border-hairline rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="h-14 px-5 border-b border-hairline flex items-center justify-between shrink-0 bg-surface-1/40">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md bg-surface-1 border border-hairline text-linear-primary flex items-center justify-center">
              <Layers size={14} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-semibold text-ink tracking-tight">
                  System Test: {workflowTitle || "Workflow Execution"}
                </h3>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-xs bg-surface-2 text-ink-subtle border border-hairline">
                  {steps.length} Steps Pipeline
                </span>
              </div>
              <p className="text-[11px] text-ink-subtle truncate max-w-sm sm:max-w-md font-mono">
                Goal: {workflowGoal || "Execute multi-agent workflow"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Visual vs JSON toggle */}
            <div className="flex items-center p-0.5 rounded-pill bg-surface-1 border border-hairline text-[11px]">
              <button
                type="button"
                onClick={() => setActiveInputMode("visual")}
                className={`flex items-center gap-1 px-2.5 py-0.5 rounded-pill font-medium transition-colors ${
                  activeInputMode === "visual"
                    ? "bg-surface-2 text-ink border border-hairline-strong"
                    : "text-ink-subtle hover:text-ink"
                }`}
              >
                <SlidersHorizontal size={11} />
                <span>Visual Inputs</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveInputMode("json")}
                className={`flex items-center gap-1 px-2.5 py-0.5 rounded-pill font-medium transition-colors ${
                  activeInputMode === "json"
                    ? "bg-surface-2 text-ink border border-hairline-strong"
                    : "text-ink-subtle hover:text-ink"
                }`}
              >
                <Code size={11} />
                <span>JSON</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-1 transition-colors border border-hairline"
              title="Close modal"
            >
              <X size={14} />
            </button>
          </div>
        </div>

        {/* Scrollable Body */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1 text-xs">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono">
              {errorMessage}
            </div>
          )}

          {/* Inputs Section */}
          <div className="p-3.5 rounded-lg bg-surface-1 border border-hairline space-y-3">
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-semibold text-ink flex items-center gap-1.5">
                <SlidersHorizontal size={12} className="text-linear-primary" />
                Custom Workflow Test Inputs
              </span>
              <span className="text-[10px] text-ink-subtle font-mono">
                {Object.keys(formInputs).length} input variable(s) configured
              </span>
            </div>

            {activeInputMode === "visual" ? (
              <div className="space-y-2.5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {Object.entries(formInputs).map(([k, v]) => (
                    <div key={k} className="space-y-1">
                      <div className="flex items-center justify-between text-[10px] font-mono text-ink-subtle">
                        <span>
                          {"{{inputs."}<span className="text-ink font-semibold">{k}</span>{"}}"}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleRemoveInput(k)}
                          className="hover:text-red-400 transition"
                          title="Remove variable"
                        >
                          <X size={10} />
                        </button>
                      </div>
                      <input
                        type="text"
                        value={v}
                        onChange={(e) => handleInputChange(k, e.target.value)}
                        placeholder={`Input value for ${k}`}
                        className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus transition-colors"
                      />
                    </div>
                  ))}
                </div>

                {/* Add Custom Input Key/Value Row */}
                <div className="pt-2 border-t border-hairline flex flex-wrap items-center gap-2">
                  <input
                    type="text"
                    value={customKey}
                    onChange={(e) => setCustomKey(e.target.value)}
                    placeholder="New variable key (e.g. topic)"
                    className="text-xs font-mono bg-canvas border border-hairline rounded-md px-2.5 py-1 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus max-w-[180px]"
                  />
                  <input
                    type="text"
                    value={customVal}
                    onChange={(e) => setCustomVal(e.target.value)}
                    placeholder="Value"
                    className="text-xs font-mono bg-canvas border border-hairline rounded-md px-2.5 py-1 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus flex-1 min-w-[140px]"
                    onKeyDown={(e) => e.key === "Enter" && handleAddCustomInput()}
                  />
                  <button
                    type="button"
                    onClick={handleAddCustomInput}
                    disabled={!customKey.trim()}
                    className="px-2.5 py-1 text-xs font-medium bg-surface-2 hover:bg-surface-3 border border-hairline text-ink rounded-md transition-colors disabled:opacity-40"
                  >
                    + Add Field
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <textarea
                  rows={4}
                  value={jsonInputs}
                  onChange={(e) => setJsonInputs(e.target.value)}
                  className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md p-2.5 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus"
                />
              </div>
            )}
          </div>

          {/* Workflow Pipeline Sequence Overview */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-medium text-ink-subtle flex items-center gap-1.5">
              <Activity size={12} className="text-linear-primary" /> Execution Flow ({steps.length} Steps)
            </span>
            <div className="flex flex-wrap items-center gap-1.5">
              {steps.map((st, i) => (
                <div
                  key={st.id}
                  className="flex items-center gap-1 text-[11px] font-mono px-2 py-1 rounded-md bg-surface-1 border border-hairline text-ink"
                >
                  <Bot size={11} className="text-linear-primary" />
                  <span>{st.name || st.id}</span>
                  <span className="text-[9px] text-ink-subtle">({st.agent_id})</span>
                  {i < steps.length - 1 && (
                    <ChevronRight size={11} className="text-ink-subtle ml-1" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Execution Progress & Result Banner */}
          {runResult && (
            <div className="p-3.5 rounded-lg bg-surface-1 border border-hairline space-y-3 mt-2">
              <div className="flex items-center justify-between pb-2 border-b border-hairline">
                <div className="flex items-center gap-2">
                  {runResult.status === "completed" ? (
                    <CheckCircle2 size={15} className="text-semantic-success" />
                  ) : (
                    <XCircle size={15} className="text-red-400" />
                  )}
                  <span className="font-semibold text-ink text-xs">
                    Pipeline Status:{" "}
                    <span className="uppercase font-mono text-[11px] text-semantic-success">
                      {runResult.status}
                    </span>
                  </span>
                </div>

                <div className="flex items-center gap-3 text-ink-subtle text-[11px] font-mono">
                  <span className="flex items-center gap-1">
                    <Clock size={11} /> {runResult.duration_ms}ms
                  </span>
                  <span className="flex items-center gap-1">
                    <Zap size={11} className="text-linear-primary" /> {runResult.total_tokens} tokens
                  </span>
                </div>
              </div>

              {/* Result Tabs */}
              <div className="flex items-center gap-1 border-b border-hairline pb-1 text-[11px]">
                <button
                  type="button"
                  onClick={() => setActiveResultTab("final")}
                  className={`px-2.5 py-0.5 rounded-md font-medium transition-colors ${
                    activeResultTab === "final"
                      ? "bg-surface-2 text-ink border border-hairline"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  <span className="flex items-center gap-1">
                    <FileText size={11} /> Final Output
                  </span>
                </button>
                {Boolean(runResult.artifacts && runResult.artifacts.length > 0) && (
                  <button
                    type="button"
                    onClick={() => setActiveResultTab("artifacts")}
                    className={`px-2.5 py-0.5 rounded-md font-medium transition-colors ${
                      activeResultTab === "artifacts"
                        ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                        : "text-purple-400 hover:text-purple-300"
                    }`}
                  >
                    <span className="flex items-center gap-1">
                      <Sparkles size={11} /> Artifacts ({runResult.artifacts?.length || 0})
                    </span>
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setActiveResultTab("steps")}
                  className={`px-2.5 py-0.5 rounded-md font-medium transition-colors ${
                    activeResultTab === "steps"
                      ? "bg-surface-2 text-ink border border-hairline"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  <span className="flex items-center gap-1">
                    <Bot size={11} /> Step Traces ({runResult.step_runs?.length || 0})
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveResultTab("raw")}
                  className={`px-2.5 py-0.5 rounded-md font-medium transition-colors ${
                    activeResultTab === "raw"
                      ? "bg-surface-2 text-ink border border-hairline"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  <span className="flex items-center gap-1">
                    <Code size={11} /> Raw Run Payload
                  </span>
                </button>

                <div className="ml-auto flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={handleCopyOutput}
                    className="flex items-center gap-1 text-[10px] text-ink-subtle hover:text-ink bg-surface-2 px-1.5 py-0.5 rounded-md border border-hairline transition-colors"
                  >
                    {copied ? <Check size={11} className="text-semantic-success" /> : <Copy size={11} />}
                    <span>{copied ? "Copied" : "Copy Output"}</span>
                  </button>

                  {onNavigateToRuns && (
                    <button
                      type="button"
                      onClick={() => {
                        onClose();
                        onNavigateToRuns();
                      }}
                      className="text-[10px] text-linear-primary hover:underline font-mono"
                    >
                      View in Runs Tab →
                    </button>
                  )}
                </div>
              </div>

              {/* Final Output Content */}
              {activeResultTab === "final" && (
                <div className="space-y-2">
                  <pre className="font-mono text-[11px] text-ink leading-relaxed bg-canvas p-3 rounded-md border border-hairline whitespace-pre-wrap max-h-60 overflow-y-auto">
                    {typeof runResult.output_data?.final_result === "string"
                      ? runResult.output_data.final_result
                      : JSON.stringify(runResult.output_data, null, 2)}
                  </pre>
                </div>
              )}

              {/* Generated Artifacts Viewer */}
              {activeResultTab === "artifacts" && (
                <div className="space-y-3 max-h-72 overflow-y-auto">
                  {runResult.artifacts?.map((art, aIdx) => (
                    <div
                      key={aIdx}
                      className="p-3 rounded-md bg-canvas border border-purple-500/30 space-y-2 font-mono text-[11px]"
                    >
                      <div className="flex items-center justify-between pb-1.5 border-b border-hairline">
                        <div className="flex items-center gap-2">
                          <span className="text-purple-400 font-semibold">{art.title}</span>
                          <span className="text-[9px] uppercase px-1.5 py-0.2 rounded-xs bg-purple-500/20 text-purple-300 border border-purple-500/40">
                            {art.type}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            navigator.clipboard.writeText(art.content);
                            setCopied(true);
                            setTimeout(() => setCopied(false), 2000);
                          }}
                          className="text-[10px] text-ink-subtle hover:text-ink px-1.5 py-0.5 rounded bg-surface-2 border border-hairline transition-colors flex items-center gap-1"
                        >
                          <Copy size={10} /> Copy Content
                        </button>
                      </div>
                      <pre className="p-2.5 rounded bg-surface-1 border border-hairline text-ink leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
                        {art.content}
                      </pre>
                    </div>
                  ))}
                </div>
              )}

              {/* Step Traces Explorer */}
              {activeResultTab === "steps" && (
                <div className="space-y-2">
                  {/* Step Selector Pills */}
                  <div className="flex flex-wrap items-center gap-1">
                    {runResult.step_runs?.map((sr, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setSelectedStepIndex(idx)}
                        className={`px-2 py-0.5 rounded-md text-[10px] font-mono border transition-colors flex items-center gap-1 ${
                          selectedStepIndex === idx
                            ? "bg-surface-2 text-ink border-hairline-strong font-semibold"
                            : "bg-surface-1 text-ink-subtle border-hairline hover:text-ink"
                        }`}
                      >
                        <Bot size={10} className="text-linear-primary" />
                        <span>{sr.step_id || `Step ${idx + 1}`}</span>
                        <span className="text-[9px] opacity-70">({sr.duration_ms}ms)</span>
                      </button>
                    ))}
                  </div>

                  {/* Active Step Details */}
                  {activeStepRun ? (
                    <div className="p-3 rounded-md bg-canvas border border-hairline space-y-2 text-[11px] font-mono">
                      <div className="flex items-center justify-between pb-1.5 border-b border-hairline">
                        <span className="font-semibold text-ink">
                          {activeStepRun.step_id}: Agent {activeStepRun.agent_id}
                        </span>
                        <span className="text-ink-subtle text-[10px]">
                          {activeStepRun.duration_ms}ms · {activeStepRun.tokens_used} tokens
                        </span>
                      </div>

                      {activeStepRun.tool_calls && activeStepRun.tool_calls.length > 0 && (
                        <div>
                          <span className="text-[10px] text-ink-tertiary block mb-0.5">
                            Tools Invoked ({activeStepRun.tool_calls.length}):
                          </span>
                          <div className="space-y-1">
                            {activeStepRun.tool_calls.map((tc, tIdx) => (
                              <div
                                key={tIdx}
                                className="p-1.5 rounded-xs bg-surface-1 border border-hairline text-[10px]"
                              >
                                <div className="flex items-center justify-between">
                                  <span className="font-semibold text-ink">{tc.tool_name || tc.tool_id || "Tool"}</span>
                                  {Boolean(tc.status) && (
                                    <span className="text-[9px] text-ink-subtle font-mono">{tc.status}</span>
                                  )}
                                </div>
                                {tc.duration_ms !== undefined && (
                                  <div className="text-ink-subtle text-[9px]">
                                    {tc.duration_ms}ms
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div>
                        <span className="text-[10px] text-ink-tertiary block mb-0.5">
                          Output Produced:
                        </span>
                        <pre className="bg-surface-1 p-2 rounded-xs border border-hairline text-ink whitespace-pre-wrap max-h-36 overflow-y-auto">
                          {typeof activeStepRun.output_data?.text === "string"
                            ? activeStepRun.output_data.text
                            : JSON.stringify(activeStepRun.output_data, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <p className="text-[11px] text-ink-subtle py-2 font-mono">Select a step to inspect traces.</p>
                  )}
                </div>
              )}

              {/* Raw Run JSON */}
              {activeResultTab === "raw" && (
                <pre className="font-mono text-[10px] text-ink-muted bg-canvas p-3 rounded-md border border-hairline overflow-x-auto max-h-60">
                  {JSON.stringify(runResult, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="h-14 px-5 border-t border-hairline flex items-center justify-between bg-surface-1/40 shrink-0">
          <div className="text-[11px] text-ink-subtle font-mono">
            {isRunning ? (
              <span className="flex items-center gap-1.5 text-linear-primary animate-pulse">
                <Sparkles size={12} /> Pipeline executing in swarm backend...
              </span>
            ) : (
              <span>Ready to test workflow DAG</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-ink-subtle hover:text-ink transition-colors"
            >
              Close
            </button>
            <button
              type="button"
              disabled={isRunning}
              onClick={handleExecuteSystemTest}
              className="px-4 py-1.5 text-xs font-medium bg-linear-primary hover:bg-linear-hover text-white rounded-md transition-colors disabled:opacity-40 flex items-center gap-1.5 shadow-sm"
            >
              <Play size={12} className="fill-current" />
              <span>{isRunning ? "Executing Pipeline..." : "Execute System Test"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
