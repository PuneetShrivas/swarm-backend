"use client";

import React, { useState } from "react";
import { WorkflowStep, StepUnitTestResponse } from "../types";
import { getAuthHeaders } from "@/lib/supabase";
import {
  Play,
  X,
  Bot,
  Zap,
  Clock,
  Coins,
  CheckCircle2,
  XCircle,
} from "lucide-react";

interface StepUnitTestModalProps {
  workflowId: string;
  step: WorkflowStep | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function StepUnitTestModal({
  workflowId,
  step,
  isOpen,
  onClose,
}: StepUnitTestModalProps) {
  const [mockInputsJson, setMockInputsJson] = useState('{\n  "query": "Sample test input parameter"\n}');
  const [mockPrevOutputsJson, setMockPrevOutputsJson] = useState('{\n  "step_1": {\n    "text": "Simulated previous step output"\n  }\n}');
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<StepUnitTestResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen || !step) return null;

  const handleExecuteUnitTest = async () => {
    setIsRunning(true);
    setResult(null);
    setErrorMessage(null);

    let parsedInputs = {};
    let parsedOutputs = {};
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
        throw new Error(data.detail || "Unit test failed.");
      }

      const testData: StepUnitTestResponse = await res.json();
      setResult(testData);
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "Unit test execution error.");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-card border border-border rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 flex items-center justify-center">
              <Play size={14} className="fill-current" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                Step Unit Test: {step.name}
              </h3>
              <p className="text-[11px] text-muted-foreground flex items-center gap-1">
                <Bot size={11} className="text-primary" /> Assigned Agent: <span className="font-mono text-foreground">{step.agent_id}</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted"
          >
            <X size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1 text-xs">
          {errorMessage && (
            <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs">
              {errorMessage}
            </div>
          )}

          {/* Raw Instructions Preview */}
          <div>
            <label className="text-[11px] font-medium text-muted-foreground block mb-1">
              Instructions Template
            </label>
            <div className="p-2.5 rounded-xl bg-background border border-border/80 font-mono text-[11px] text-foreground/90">
              {step.instructions}
            </div>
          </div>

          {/* Mock Inputs Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-medium text-muted-foreground block mb-1">
                Mock Inputs (JSON)
              </label>
              <textarea
                rows={4}
                value={mockInputsJson}
                onChange={(e) => setMockInputsJson(e.target.value)}
                className="w-full text-xs font-mono bg-background border border-border rounded-xl p-2.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div>
              <label className="text-[11px] font-medium text-muted-foreground block mb-1">
                Mock Previous Step Outputs (JSON)
              </label>
              <textarea
                rows={4}
                value={mockPrevOutputsJson}
                onChange={(e) => setMockPrevOutputsJson(e.target.value)}
                className="w-full text-xs font-mono bg-background border border-border rounded-xl p-2.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>

          {/* Execution Result Display */}
          {result && (
            <div className="p-3.5 rounded-xl bg-background border border-border space-y-2.5">
              <div className="flex items-center justify-between pb-2 border-b border-border/60">
                <span className="flex items-center gap-1.5 font-semibold text-foreground">
                  {result.status === "completed" ? (
                    <CheckCircle2 size={14} className="text-emerald-500" />
                  ) : (
                    <XCircle size={14} className="text-destructive" />
                  )}
                  Unit Test Outcome: <span className="uppercase text-[11px]">{result.status}</span>
                </span>
                <div className="flex items-center gap-2 text-muted-foreground text-[11px]">
                  <span className="flex items-center gap-1">
                    <Clock size={11} /> {result.duration_ms}ms
                  </span>
                  <span className="flex items-center gap-1">
                    <Coins size={11} className="text-primary" /> {result.tokens_used} tok
                  </span>
                </div>
              </div>

              {result.prompt_rendered && (
                <div>
                  <span className="text-[10px] font-semibold text-muted-foreground block mb-0.5">
                    Rendered Prompt:
                  </span>
                  <p className="font-mono text-[11px] text-muted-foreground bg-card p-2 rounded border border-border/50">
                    {result.prompt_rendered}
                  </p>
                </div>
              )}

              {result.tool_calls && result.tool_calls.length > 0 && (
                <div>
                  <span className="text-[10px] font-semibold text-muted-foreground block mb-0.5 flex items-center gap-1">
                    <Zap size={11} className="text-amber-500" /> Tool Calls:
                  </span>
                  <pre className="font-mono text-[10px] text-foreground bg-card p-2 rounded border border-border/50">
                    {JSON.stringify(result.tool_calls, null, 2)}
                  </pre>
                </div>
              )}

              <div>
                <span className="text-[10px] font-semibold text-muted-foreground block mb-0.5">
                  Step Output:
                </span>
                <pre className="font-mono text-[11px] text-foreground leading-relaxed bg-card p-2.5 rounded border border-border/50 whitespace-pre-wrap">
                  {typeof result.output_data?.text === "string"
                    ? result.output_data.text
                    : JSON.stringify(result.output_data, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-border flex items-center justify-end gap-2 bg-card/60">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            Close
          </button>
          <button
            disabled={isRunning}
            onClick={handleExecuteUnitTest}
            className="px-4 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-xl hover:opacity-90 disabled:opacity-50 transition flex items-center gap-1.5 shadow-subtle"
          >
            <Play size={13} className="fill-current" />
            {isRunning ? "Executing Step..." : "Run Step Unit Test"}
          </button>
        </div>
      </div>
    </div>
  );
}
