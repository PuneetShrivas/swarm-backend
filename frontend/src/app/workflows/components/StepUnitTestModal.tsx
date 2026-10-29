"use client";

import React, { useState, useEffect, useMemo } from "react";
import { WorkflowStep, StepUnitTestResponse } from "../types";
import { getAuthHeaders } from "@/lib/supabase";
import {
  Play,
  X,
  Bot,
  Zap,
  Clock,
  CheckCircle2,
  XCircle,
  Code,
  SlidersHorizontal,
  Eye,
  Copy,
  Check,
  ChevronRight,
  Terminal,
} from "lucide-react";

interface StepUnitTestModalProps {
  workflowId: string;
  step: WorkflowStep | null;
  workflowGoal?: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function StepUnitTestModal({
  workflowId,
  step,
  workflowGoal = "",
  isOpen,
  onClose,
}: StepUnitTestModalProps) {
  const [activeMode, setActiveMode] = useState<"visual" | "json">("visual");
  const [activeOutputTab, setActiveOutputTab] = useState<"output" | "artifacts" | "prompt" | "tools" | "raw">("output");

  // Dynamic variable state
  const [formInputs, setFormInputs] = useState<Record<string, string>>({});
  const [formPrevOutputs, setFormPrevOutputs] = useState<Record<string, Record<string, string>>>({});
  const [formGoal, setFormGoal] = useState<string>(workflowGoal || "");

  // Raw JSON state
  const [mockInputsJson, setMockInputsJson] = useState('{\n  "query": "Sample test input parameter"\n}');
  const [mockPrevOutputsJson, setMockPrevOutputsJson] = useState('{\n  "step_1": {\n    "text": "Simulated previous step output"\n  }\n}');

  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<StepUnitTestResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Discover variables from step.instructions: {{goal}}, {{inputs.<var>}}, {{steps.<id>.output.<field>}}
  const discoveredVariables = useMemo(() => {
    if (!step?.instructions) return { hasGoal: false, inputs: [], stepOutputs: [] };

    const regex = /\{\{\s*([\w\.\-]+)\s*\}\}/g;
    const matches = Array.from(step.instructions.matchAll(regex)).map((m) => m[1]);

    const hasGoal = matches.some((m) => m === "goal");
    const inputs: string[] = [];
    const stepOutputs: Array<{ stepId: string; field: string; raw: string }> = [];

    matches.forEach((m) => {
      if (m.startsWith("inputs.")) {
        const varName = m.replace("inputs.", "");
        if (!inputs.includes(varName)) inputs.push(varName);
      } else if (m.startsWith("steps.") && m.includes(".output.")) {
        const parts = m.split(".");
        // Format: steps.<stepId>.output.<field>
        if (parts.length >= 4) {
          const stepId = parts[1];
          const field = parts.slice(3).join(".");
          if (!stepOutputs.some((so) => so.stepId === stepId && so.field === field)) {
            stepOutputs.push({ stepId, field, raw: m });
          }
        }
      }
    });

    return { hasGoal, inputs, stepOutputs };
  }, [step?.instructions]);

  // Sync state when step opens
  useEffect(() => {
    if (!step) return;

    setFormGoal(workflowGoal || "");
    const initialInputs: Record<string, string> = {};
    if (discoveredVariables.inputs.length > 0) {
      discoveredVariables.inputs.forEach((varName) => {
        initialInputs[varName] = `Test value for ${varName}`;
      });
    } else {
      initialInputs["query"] = "Sample test query";
    }
    setFormInputs(initialInputs);

    const initialPrevOutputs: Record<string, Record<string, string>> = {};
    discoveredVariables.stepOutputs.forEach(({ stepId, field }) => {
      if (!initialPrevOutputs[stepId]) {
        initialPrevOutputs[stepId] = {};
      }
      initialPrevOutputs[stepId][field] = `Simulated output for ${stepId}.${field}`;
    });
    setFormPrevOutputs(initialPrevOutputs);

    setMockInputsJson(JSON.stringify(initialInputs, null, 2));
    setMockPrevOutputsJson(JSON.stringify(initialPrevOutputs, null, 2));
    setResult(null);
    setErrorMessage(null);
  }, [step, workflowGoal, discoveredVariables]);

  // Sync JSON text when visual form changes
  const handleVisualInputChange = (key: string, value: string) => {
    const updated = { ...formInputs, [key]: value };
    setFormInputs(updated);
    setMockInputsJson(JSON.stringify(updated, null, 2));
  };

  const handleVisualStepOutputChange = (stepId: string, field: string, value: string) => {
    const updated = {
      ...formPrevOutputs,
      [stepId]: {
        ...(formPrevOutputs[stepId] || {}),
        [field]: value,
      },
    };
    setFormPrevOutputs(updated);
    setMockPrevOutputsJson(JSON.stringify(updated, null, 2));
  };

  // Compute live interpolated prompt preview
  const liveResolvedPrompt = useMemo(() => {
    if (!step?.instructions) return "";
    let resolved = step.instructions;

    resolved = resolved.replace(/\{\{\s*goal\s*\}\}/g, formGoal || "[goal]");

    Object.entries(formInputs).forEach(([k, v]) => {
      const reg = new RegExp(`\\{\\{\\s*inputs\\.${k}\\s*\\}\\}`, "g");
      resolved = resolved.replace(reg, v || `[inputs.${k}]`);
    });

    Object.entries(formPrevOutputs).forEach(([stepId, fields]) => {
      Object.entries(fields).forEach(([fName, val]) => {
        const reg = new RegExp(`\\{\\{\\s*steps\\.${stepId}\\.output\\.${fName}\\s*\\}\\}`, "g");
        resolved = resolved.replace(reg, val || `[steps.${stepId}.output.${fName}]`);
      });
    });

    return resolved;
  }, [step?.instructions, formGoal, formInputs, formPrevOutputs]);

  if (!isOpen || !step) return null;

  const handleExecuteUnitTest = async () => {
    setIsRunning(true);
    setResult(null);
    setErrorMessage(null);

    let parsedInputs: Record<string, unknown> = {};
    let parsedOutputs: Record<string, unknown> = {};

    if (activeMode === "visual") {
      parsedInputs = { ...formInputs };
      parsedOutputs = { ...formPrevOutputs };
    } else {
      try {
        parsedInputs = JSON.parse(mockInputsJson);
      } catch {
        setErrorMessage("Invalid Mock Inputs JSON. Please check formatting.");
        setIsRunning(false);
        return;
      }
      try {
        parsedOutputs = JSON.parse(mockPrevOutputsJson);
      } catch {
        setErrorMessage("Invalid Mock Previous Outputs JSON. Please check formatting.");
        setIsRunning(false);
        return;
      }
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const authHeaders = await getAuthHeaders();
      const res = await fetch(`${apiUrl}/api/workflows/${workflowId}/steps/${step.id}/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({
          step_id: step.id,
          mock_inputs: parsedInputs,
          mock_previous_outputs: parsedOutputs,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Step unit test failed.");
      }

      const testData: StepUnitTestResponse = await res.json();
      setResult(testData);
      setActiveOutputTab("output");
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "Unit test execution error.");
    } finally {
      setIsRunning(false);
    }
  };

  const handleCopyOutput = () => {
    if (!result?.output_data) return;
    const text =
      typeof result.output_data.text === "string"
        ? result.output_data.text
        : JSON.stringify(result.output_data, null, 2);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-canvas border border-hairline rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="h-14 px-5 border-b border-hairline flex items-center justify-between shrink-0 bg-surface-1/40">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md bg-surface-1 border border-hairline text-linear-primary flex items-center justify-center">
              <Play size={13} className="fill-current" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-semibold text-ink tracking-tight">
                  Unit Test Step: {step.name}
                </h3>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-xs bg-surface-2 text-ink-subtle border border-hairline">
                  {step.id}
                </span>
              </div>
              <p className="text-[11px] text-ink-subtle flex items-center gap-1.5 font-mono">
                <Bot size={11} className="text-linear-primary" /> Agent:{" "}
                <span className="text-ink font-medium">{step.agent_id}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Visual vs JSON Mode Toggle */}
            <div className="flex items-center p-0.5 rounded-pill bg-surface-1 border border-hairline text-[11px]">
              <button
                type="button"
                onClick={() => setActiveMode("visual")}
                className={`flex items-center gap-1 px-2.5 py-0.5 rounded-pill font-medium transition-colors ${
                  activeMode === "visual"
                    ? "bg-surface-2 text-ink border border-hairline-strong"
                    : "text-ink-subtle hover:text-ink"
                }`}
              >
                <SlidersHorizontal size={11} />
                <span>Visual Form</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveMode("json")}
                className={`flex items-center gap-1 px-2.5 py-0.5 rounded-pill font-medium transition-colors ${
                  activeMode === "json"
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

        {/* Modal Scroll Body */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1 text-xs">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono">
              {errorMessage}
            </div>
          )}

          {/* Raw Instructions Preview */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px] text-ink-subtle">
              <span className="font-medium text-ink flex items-center gap-1">
                <Terminal size={12} className="text-linear-primary" /> Instructions Template
              </span>
              <span className="font-mono text-[10px]">
                {discoveredVariables.inputs.length} inputs · {discoveredVariables.stepOutputs.length} step refs
              </span>
            </div>
            <div className="p-3 rounded-lg bg-surface-1 border border-hairline font-mono text-[11px] text-ink/90 whitespace-pre-wrap leading-relaxed">
              {step.instructions}
            </div>
          </div>

          {/* Inputs Section: Visual Mode or JSON Mode */}
          {activeMode === "visual" ? (
            <div className="space-y-3.5 pt-1">
              {/* Global Goal */}
              {discoveredVariables.hasGoal && (
                <div className="space-y-1">
                  <label className="text-[11px] font-mono text-ink-subtle flex items-center gap-1">
                    <span>Variable:</span>
                    <code className="text-linear-primary font-bold">{"{{goal}}"}</code>
                  </label>
                  <input
                    type="text"
                    value={formGoal}
                    onChange={(e) => setFormGoal(e.target.value)}
                    placeholder="Workflow goal description"
                    className="w-full text-xs font-mono bg-surface-1 border border-hairline rounded-md px-3 py-2 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus transition-colors"
                  />
                </div>
              )}

              {/* Dynamic Discovered Workflow Inputs */}
              {discoveredVariables.inputs.length > 0 ? (
                <div className="space-y-2">
                  <div className="text-[11px] font-medium text-ink flex items-center gap-1">
                    <ChevronRight size={12} className="text-linear-primary" /> Step Input Variables
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {discoveredVariables.inputs.map((varName) => (
                      <div key={varName} className="space-y-1">
                        <label className="text-[10px] font-mono text-ink-subtle">
                          {"{{inputs."}<span className="text-ink font-semibold">{varName}</span>{"}}"}
                        </label>
                        <input
                          type="text"
                          value={formInputs[varName] || ""}
                          onChange={(e) => handleVisualInputChange(varName, e.target.value)}
                          placeholder={`Value for ${varName}`}
                          className="w-full text-xs font-mono bg-surface-1 border border-hairline rounded-md px-3 py-1.5 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus transition-colors"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-1">
                  <label className="text-[10px] font-mono text-ink-subtle">
                    Generic Input Query (No specific inputs required)
                  </label>
                  <input
                    type="text"
                    value={formInputs["query"] || ""}
                    onChange={(e) => handleVisualInputChange("query", e.target.value)}
                    placeholder="Test query"
                    className="w-full text-xs font-mono bg-surface-1 border border-hairline rounded-md px-3 py-1.5 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus transition-colors"
                  />
                </div>
              )}

              {/* Mock Step Outputs */}
              {discoveredVariables.stepOutputs.length > 0 && (
                <div className="space-y-2 pt-1 border-t border-hairline">
                  <div className="text-[11px] font-medium text-ink flex items-center gap-1">
                    <ChevronRight size={12} className="text-linear-primary" /> Mock Predecessor Step Outputs
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {discoveredVariables.stepOutputs.map(({ stepId, field, raw }) => (
                      <div key={raw} className="space-y-1">
                        <label className="text-[10px] font-mono text-ink-subtle truncate block">
                          {"{{"}<span className="text-linear-primary">{stepId}</span>.output.<span className="text-ink font-semibold">{field}</span>{"}}"}
                        </label>
                        <textarea
                          rows={2}
                          value={formPrevOutputs[stepId]?.[field] || ""}
                          onChange={(e) => handleVisualStepOutputChange(stepId, field, e.target.value)}
                          placeholder={`Output for ${raw}`}
                          className="w-full text-xs font-mono bg-surface-1 border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus transition-colors resize-none"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* JSON Mode */
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div>
                <label className="text-[11px] font-mono text-ink-subtle block mb-1">
                  Mock Inputs (JSON)
                </label>
                <textarea
                  rows={5}
                  value={mockInputsJson}
                  onChange={(e) => setMockInputsJson(e.target.value)}
                  className="w-full text-xs font-mono bg-surface-1 border border-hairline rounded-md p-2.5 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus"
                />
              </div>

              <div>
                <label className="text-[11px] font-mono text-ink-subtle block mb-1">
                  Mock Previous Outputs (JSON)
                </label>
                <textarea
                  rows={5}
                  value={mockPrevOutputsJson}
                  onChange={(e) => setMockPrevOutputsJson(e.target.value)}
                  className="w-full text-xs font-mono bg-surface-1 border border-hairline rounded-md p-2.5 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus"
                />
              </div>
            </div>
          )}

          {/* Live Resolved Prompt Preview */}
          <div className="p-3 rounded-lg bg-surface-1 border border-hairline space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-medium text-ink flex items-center gap-1.5">
                <Eye size={12} className="text-linear-primary" /> Live Resolved Prompt Preview
              </span>
              <span className="text-[10px] text-ink-subtle font-mono">
                Interpolated before execution
              </span>
            </div>
            <p className="font-mono text-[11px] text-ink-muted bg-canvas p-2.5 rounded-md border border-hairline whitespace-pre-wrap leading-relaxed max-h-28 overflow-y-auto">
              {liveResolvedPrompt}
            </p>
          </div>

          {/* Execution Result Display */}
          {result && (
            <div className="p-3.5 rounded-lg bg-surface-1 border border-hairline space-y-3 mt-3">
              <div className="flex items-center justify-between pb-2 border-b border-hairline">
                <div className="flex items-center gap-2">
                  {result.status === "completed" ? (
                    <CheckCircle2 size={15} className="text-semantic-success" />
                  ) : (
                    <XCircle size={15} className="text-red-400" />
                  )}
                  <span className="font-semibold text-ink text-xs">
                    Outcome: <span className="uppercase font-mono text-[11px] text-semantic-success">{result.status}</span>
                  </span>
                  {result.branch_taken !== undefined && (
                    <span
                      className={`text-[9px] font-mono uppercase px-1.5 py-0.2 rounded-xs border font-semibold ${
                        result.branch_taken
                          ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-400"
                          : "bg-rose-500/15 border-rose-500/40 text-rose-400"
                      }`}
                    >
                      Branch: {result.branch_taken ? "TRUE" : "FALSE"}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3 text-ink-subtle text-[11px] font-mono">
                  <span className="flex items-center gap-1">
                    <Clock size={11} /> {result.duration_ms}ms
                  </span>
                  <span className="flex items-center gap-1">
                    <Zap size={11} className="text-linear-primary" /> {result.tokens_used} tokens
                  </span>
                </div>
              </div>

              {/* Output Tabs */}
              <div className="flex items-center gap-1 border-b border-hairline pb-1 text-[11px]">
                <button
                  type="button"
                  onClick={() => setActiveOutputTab("output")}
                  className={`px-2 py-0.5 rounded-md font-medium transition-colors ${
                    activeOutputTab === "output"
                      ? "bg-surface-2 text-ink border border-hairline"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  Step Output
                </button>
                {Boolean(result.artifacts && result.artifacts.length > 0) && (
                  <button
                    type="button"
                    onClick={() => setActiveOutputTab("artifacts")}
                    className={`px-2 py-0.5 rounded-md font-medium transition-colors ${
                      activeOutputTab === "artifacts"
                        ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                        : "text-purple-400 hover:text-purple-300"
                    }`}
                  >
                    Artifacts ({result.artifacts?.length || 0})
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setActiveOutputTab("tools")}
                  className={`px-2 py-0.5 rounded-md font-medium transition-colors ${
                    activeOutputTab === "tools"
                      ? "bg-surface-2 text-ink border border-hairline"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  Tools ({result.tool_calls?.length || 0})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveOutputTab("prompt")}
                  className={`px-2 py-0.5 rounded-md font-medium transition-colors ${
                    activeOutputTab === "prompt"
                      ? "bg-surface-2 text-ink border border-hairline"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  Rendered Prompt
                </button>
                <button
                  type="button"
                  onClick={() => setActiveOutputTab("raw")}
                  className={`px-2 py-0.5 rounded-md font-medium transition-colors ${
                    activeOutputTab === "raw"
                      ? "bg-surface-2 text-ink border border-hairline"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  Raw JSON
                </button>

                <div className="ml-auto">
                  <button
                    type="button"
                    onClick={handleCopyOutput}
                    className="flex items-center gap-1 text-[10px] text-ink-subtle hover:text-ink bg-surface-2 px-1.5 py-0.5 rounded-md border border-hairline transition-colors"
                  >
                    {copied ? <Check size={11} className="text-semantic-success" /> : <Copy size={11} />}
                    <span>{copied ? "Copied" : "Copy"}</span>
                  </button>
                </div>
              </div>

              {/* Tab Contents */}
              {activeOutputTab === "output" && (
                <pre className="font-mono text-[11px] text-ink leading-relaxed bg-canvas p-3 rounded-md border border-hairline whitespace-pre-wrap max-h-56 overflow-y-auto">
                  {typeof result.output_data?.text === "string"
                    ? result.output_data.text
                    : JSON.stringify(result.output_data, null, 2)}
                </pre>
              )}

              {activeOutputTab === "artifacts" && (
                <div className="space-y-2 max-h-56 overflow-y-auto font-mono text-[11px]">
                  {result.artifacts?.map((art, aIdx) => (
                    <div key={aIdx} className="p-3 rounded-md bg-canvas border border-purple-500/30 space-y-1.5">
                      <div className="flex items-center justify-between pb-1 border-b border-hairline">
                        <span className="text-purple-400 font-semibold">{art.title}</span>
                        <span className="text-[9px] uppercase px-1 rounded-xs bg-purple-500/20 text-purple-300 border border-purple-500/40">
                          {art.type}
                        </span>
                      </div>
                      <pre className="p-2 rounded bg-surface-1 border border-hairline text-ink whitespace-pre-wrap max-h-36 overflow-y-auto">
                        {art.content}
                      </pre>
                    </div>
                  ))}
                </div>
              )}

              {activeOutputTab === "tools" && (
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {result.tool_calls && result.tool_calls.length > 0 ? (
                    result.tool_calls.map((tc, idx) => (
                      <div key={idx} className="p-2.5 rounded-md bg-canvas border border-hairline font-mono text-[11px]">
                        <div className="flex items-center justify-between text-ink font-semibold">
                          <span>{String(tc.tool || tc.tool_name || "Tool")}</span>
                          <span className="text-[10px] text-ink-subtle">Tool Call #{idx + 1}</span>
                        </div>
                        {Boolean(tc.args) && (
                          <div className="text-ink-subtle mt-1 text-[10px]">
                            <span className="text-ink-tertiary">args: </span>
                            {JSON.stringify(tc.args)}
                          </div>
                        )}
                        {Boolean(tc.result !== undefined) && (
                          <div className="text-semantic-success mt-1 pt-1 border-t border-hairline text-[10px]">
                            <span className="text-ink-tertiary">result: </span>
                            {JSON.stringify(tc.result)}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-[11px] text-ink-subtle py-2 font-mono">No tool calls executed in this step.</p>
                  )}
                </div>
              )}

              {activeOutputTab === "prompt" && (
                <pre className="font-mono text-[11px] text-ink-muted bg-canvas p-3 rounded-md border border-hairline whitespace-pre-wrap max-h-56 overflow-y-auto">
                  {result.prompt_rendered || liveResolvedPrompt}
                </pre>
              )}

              {activeOutputTab === "raw" && (
                <pre className="font-mono text-[10px] text-ink-muted bg-canvas p-3 rounded-md border border-hairline overflow-x-auto max-h-56">
                  {JSON.stringify(result, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="h-14 px-5 border-t border-hairline flex items-center justify-end gap-2 bg-surface-1/40 shrink-0">
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
            onClick={handleExecuteUnitTest}
            className="px-4 py-1.5 text-xs font-medium bg-linear-primary hover:bg-linear-hover text-white rounded-md transition-colors disabled:opacity-40 flex items-center gap-1.5 shadow-sm"
          >
            <Play size={12} className="fill-current" />
            <span>{isRunning ? "Executing Agent Step..." : "Run Step Unit Test"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
