"use client";

import React, { useState } from "react";
import { getAuthHeaders } from "@/lib/supabase";
import { Workflow, WorkflowStep } from "../types";
import {
  X,
  Sparkles,
  Check,
  ArrowRight,
  Bot,
  FileText,
  GitBranch,
  Code2,
  Repeat,
  Layers,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface AIWorkflowGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (workflow: Workflow) => void;
}

const SAMPLE_IDEAS = [
  "Security & Vulnerability Audit Pipeline: Scans code, evaluates OWASP compliance, and outputs an executive remediation report",
  "Competitive Intelligence & Market Analysis DAG: Researches competitors, extracts market metrics, and writes briefing",
  "Automated Code Review & Refactor Pipeline: Static code analysis, quality gate evaluation, and pull request refactor",
  "Data Analytics & Quantitative Metrics Engine: Extracts numerical data, analyzes trends, and generates summary report",
  "Multi-Source Document Synthesis Pipeline: Gathers documentation, cross-verifies facts, and delivers executive briefing",
];

export default function AIWorkflowGeneratorModal({
  isOpen,
  onClose,
  onCreated,
}: AIWorkflowGeneratorModalProps) {
  const [prompt, setPrompt] = useState(SAMPLE_IDEAS[0]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Generated Workflow State
  const [generatedWorkflow, setGeneratedWorkflow] = useState<{
    title: string;
    description: string;
    goal: string;
    steps: WorkflowStep[];
    edges: Array<{ source: string; target: string }>;
  } | null>(null);

  const [expandedStepIdx, setExpandedStepIdx] = useState<number | null>(0);

  if (!isOpen) return null;

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    setIsGenerating(true);
    setErrorMessage(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const authHeaders = await getAuthHeaders();

      const res = await fetch(`${apiUrl}/api/ai/generate-workflow`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "AI workflow generation failed.");
      }

      const data = await res.json();
      const rawWf = data.workflow || data || {};

      const steps: WorkflowStep[] = (rawWf.steps || []).map((s: Partial<WorkflowStep>, idx: number) => ({
        id: s.id || `step_${idx + 1}`,
        name: s.name || `Step ${idx + 1}`,
        step_type: s.step_type || "agent",
        agent_id: s.agent_id || "researcher",
        instructions: s.instructions || "",
        code: s.code || "",
        condition_expr: s.condition_expr || "",
        true_target_step_id: s.true_target_step_id || "",
        false_target_step_id: s.false_target_step_id || "",
        loop_target_step_id: s.loop_target_step_id || "",
        max_loop_iterations: s.max_loop_iterations || 3,
        artifact_title: s.artifact_title || "",
        artifact_type: s.artifact_type || "markdown",
        tool_ids: s.tool_ids || [],
        knowledge_file_ids: s.knowledge_file_ids || [],
        depends_on: s.depends_on || (idx > 0 ? [`step_${idx}`] : []),
      }));

      const edges: Array<{ source: string; target: string }> =
        rawWf.edges && Array.isArray(rawWf.edges) && rawWf.edges.length > 0
          ? rawWf.edges
          : steps.slice(1).map((s, idx) => ({ source: steps[idx].id, target: s.id }));

      setGeneratedWorkflow({
        title: rawWf.title || "AI Generated Workflow Pipeline",
        description: rawWf.description || prompt.trim(),
        goal: rawWf.goal || prompt.trim(),
        steps,
        edges,
      });
      setExpandedStepIdx(0);
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "Failed to generate workflow.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveAndOpen = async () => {
    if (!generatedWorkflow) return;

    setIsSaving(true);
    setErrorMessage(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const authHeaders = await getAuthHeaders();

      const payload = {
        title: generatedWorkflow.title.trim() || "Autonomous Workflow",
        description: generatedWorkflow.description.trim(),
        goal: generatedWorkflow.goal.trim(),
        visibility: "private",
        steps: generatedWorkflow.steps,
        edges: generatedWorkflow.edges,
      };

      const res = await fetch(`${apiUrl}/api/workflows`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save workflow.");
      }

      const created: Workflow = await res.json();
      onCreated(created);
      onClose();
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "Save error.");
    } finally {
      setIsSaving(false);
    }
  };

  const getStepTypeBadge = (type?: string) => {
    switch (type) {
      case "condition":
        return (
          <span className="inline-flex items-center gap-1 text-[9px] font-mono px-1.5 py-0.5 rounded-xs bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <GitBranch size={9} /> Condition
          </span>
        );
      case "python_code":
        return (
          <span className="inline-flex items-center gap-1 text-[9px] font-mono px-1.5 py-0.5 rounded-xs bg-purple-500/10 border border-purple-500/30 text-purple-400">
            <Code2 size={9} /> Python Code
          </span>
        );
      case "loop":
        return (
          <span className="inline-flex items-center gap-1 text-[9px] font-mono px-1.5 py-0.5 rounded-xs bg-pink-500/10 border border-pink-500/30 text-pink-400">
            <Repeat size={9} /> Loop
          </span>
        );
      case "artifact":
        return (
          <span className="inline-flex items-center gap-1 text-[9px] font-mono px-1.5 py-0.5 rounded-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <FileText size={9} /> Artifact
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[9px] font-mono px-1.5 py-0.5 rounded-xs bg-blue-500/10 border border-blue-500/30 text-blue-400">
            <Bot size={9} /> Agent
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-canvas border border-hairline rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden select-none">
        {/* Header */}
        <div className="h-14 px-5 border-b border-hairline flex items-center justify-between shrink-0 bg-surface-1/50">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md bg-linear-primary/10 border border-linear-primary/30 text-linear-primary flex items-center justify-center">
              <Sparkles size={13} />
            </div>
            <div>
              <h3 className="text-xs font-semibold text-ink tracking-tight flex items-center gap-1.5">
                <span>AI Workflow Generator</span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-xs bg-surface-2 border border-hairline text-ink-subtle">
                  Gemini 3.8
                </span>
              </h3>
              <p className="text-[10px] text-ink-subtle">
                Generate multi-step DAG pipelines with agent nodes, conditions, and Python tools from a prompt
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors border border-hairline"
            title="Close generator"
          >
            <X size={14} />
          </button>
        </div>

        {/* Scroll Body */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1 text-xs">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono">
              {errorMessage}
            </div>
          )}

          {/* Prompt Input Section */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-medium text-ink flex items-center gap-1.5">
                Describe the Workflow Pipeline You Need
              </label>
            </div>

            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Create a security vulnerability audit pipeline that inspects code assets, evaluates OWASP compliance, and compiles an executive remediation plan..."
              className="w-full text-xs bg-surface-1 border border-hairline hover:border-hairline-strong focus:border-linear-focus rounded-md p-3 text-ink focus:outline-none leading-relaxed resize-y"
            />

            {/* Quick Inspiration Pills */}
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-[10px] text-ink-tertiary">Quick ideas:</span>
              {SAMPLE_IDEAS.map((idea, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setPrompt(idea)}
                  className="text-[9px] font-mono px-2 py-0.5 rounded-xs bg-surface-2 hover:bg-surface-3 text-ink-muted hover:text-ink border border-hairline transition-colors truncate max-w-[200px]"
                  title={idea}
                >
                  {idea.slice(0, 32)}...
                </button>
              ))}
            </div>
          </div>

          {/* Generate Action Button */}
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleGenerate}
              disabled={isGenerating || !prompt.trim()}
              className="px-4 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors shadow-card flex items-center gap-1.5 disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <span className="w-3 h-3 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  <span>Architecting Workflow DAG...</span>
                </>
              ) : (
                <>
                  <Sparkles size={11} />
                  <span>{generatedWorkflow ? "Regenerate Workflow" : "Generate Workflow"}</span>
                </>
              )}
            </button>
          </div>

          {/* Generated Workflow Review & Refine Deck */}
          {generatedWorkflow && (
            <div className="p-4 rounded-lg bg-surface-1 border border-hairline space-y-4 mt-3 animate-fade-in">
              {/* Review Header Banner */}
              <div className="flex items-center justify-between pb-2 border-b border-hairline">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold flex items-center gap-1">
                    <Check size={11} /> Generated Specification
                  </span>
                  <span className="text-xs font-semibold text-ink">Review & Refine DAG</span>
                </div>

                <div className="flex items-center gap-1.5 text-[10px] font-mono text-ink-subtle">
                  <span>{generatedWorkflow.steps.length} Steps</span>
                  <span>·</span>
                  <span>{generatedWorkflow.edges.length} Edges</span>
                </div>
              </div>

              {/* Editable Metadata Fields */}
              <div className="space-y-3">
                <div>
                  <label className="text-[10px] font-medium text-ink-subtle mb-1 block">
                    Workflow Title
                  </label>
                  <input
                    type="text"
                    value={generatedWorkflow.title}
                    onChange={(e) =>
                      setGeneratedWorkflow({ ...generatedWorkflow, title: e.target.value })
                    }
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none focus:border-linear-focus font-medium"
                  />
                </div>

                <div>
                  <label className="text-[10px] font-medium text-ink-subtle mb-1 block">
                    High-Level Goal
                  </label>
                  <input
                    type="text"
                    value={generatedWorkflow.goal}
                    onChange={(e) =>
                      setGeneratedWorkflow({ ...generatedWorkflow, goal: e.target.value })
                    }
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none focus:border-linear-focus"
                  />
                </div>

                <div>
                  <label className="text-[10px] font-medium text-ink-subtle mb-1 block">
                    Description
                  </label>
                  <input
                    type="text"
                    value={generatedWorkflow.description}
                    onChange={(e) =>
                      setGeneratedWorkflow({ ...generatedWorkflow, description: e.target.value })
                    }
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none focus:border-linear-focus"
                  />
                </div>
              </div>

              {/* Visual Sequence Flow Strip */}
              <div className="p-2.5 rounded-md bg-canvas border border-hairline space-y-1.5">
                <div className="flex items-center gap-1.5 text-[10px] font-medium text-ink-subtle">
                  <Layers size={11} className="text-linear-primary" />
                  <span>DAG Execution Sequence</span>
                </div>
                <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono">
                  {generatedWorkflow.steps.map((st, idx) => (
                    <React.Fragment key={st.id}>
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-xs bg-surface-2 border border-hairline text-ink">
                        <span className="text-ink-tertiary">{idx + 1}.</span>
                        <span className="font-sans font-medium text-ink-muted">{st.name}</span>
                        {getStepTypeBadge(st.step_type)}
                      </span>
                      {idx < generatedWorkflow.steps.length - 1 && (
                        <span className="text-ink-tertiary">──►</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {/* Step By Step Configuration Accordion */}
              <div className="space-y-2">
                <label className="text-[10px] font-medium text-ink-subtle block">
                  Pipeline Steps Specification ({generatedWorkflow.steps.length})
                </label>

                <div className="space-y-2">
                  {generatedWorkflow.steps.map((step, idx) => {
                    const isExpanded = expandedStepIdx === idx;
                    return (
                      <div
                        key={step.id}
                        className="rounded-md border border-hairline bg-canvas overflow-hidden transition-colors"
                      >
                        <button
                          type="button"
                          onClick={() => setExpandedStepIdx(isExpanded ? null : idx)}
                          className="w-full p-2.5 flex items-center justify-between text-left hover:bg-surface-2/40 transition-colors"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="w-5 h-5 rounded-xs bg-surface-2 text-[10px] font-mono text-ink-muted flex items-center justify-center shrink-0 border border-hairline">
                              {idx + 1}
                            </span>
                            <span className="text-xs font-medium text-ink truncate">
                              {step.name}
                            </span>
                            {getStepTypeBadge(step.step_type)}
                            {step.agent_id && (
                              <span className="text-[9px] font-mono text-ink-subtle px-1.5 py-0.2 rounded-xs bg-surface-2 border border-hairline hidden sm:inline">
                                @{step.agent_id}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            {step.depends_on.length > 0 && (
                              <span className="text-[9px] font-mono text-ink-tertiary hidden md:inline">
                                depends: {step.depends_on.join(", ")}
                              </span>
                            )}
                            {isExpanded ? (
                              <ChevronUp size={12} className="text-ink-subtle" />
                            ) : (
                              <ChevronDown size={12} className="text-ink-subtle" />
                            )}
                          </div>
                        </button>

                        {isExpanded && (
                          <div className="p-3 border-t border-hairline space-y-2.5 bg-surface-1/30">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                              <div>
                                <label className="text-[9px] font-medium text-ink-subtle mb-0.5 block">
                                  Step Name
                                </label>
                                <input
                                  type="text"
                                  value={step.name}
                                  onChange={(e) => {
                                    const updated = [...generatedWorkflow.steps];
                                    updated[idx] = { ...step, name: e.target.value };
                                    setGeneratedWorkflow({ ...generatedWorkflow, steps: updated });
                                  }}
                                  className="w-full text-xs bg-canvas border border-hairline rounded px-2 py-1 text-ink focus:outline-none"
                                />
                              </div>

                              <div>
                                <label className="text-[9px] font-medium text-ink-subtle mb-0.5 block">
                                  Assigned Agent ID
                                </label>
                                <input
                                  type="text"
                                  value={step.agent_id || "researcher"}
                                  onChange={(e) => {
                                    const updated = [...generatedWorkflow.steps];
                                    updated[idx] = { ...step, agent_id: e.target.value };
                                    setGeneratedWorkflow({ ...generatedWorkflow, steps: updated });
                                  }}
                                  className="w-full text-xs bg-canvas border border-hairline rounded px-2 py-1 text-ink focus:outline-none"
                                />
                              </div>
                            </div>

                            <div>
                              <label className="text-[9px] font-medium text-ink-subtle mb-0.5 block">
                                Prompt Instructions Template
                              </label>
                              <textarea
                                rows={3}
                                value={step.instructions || ""}
                                onChange={(e) => {
                                  const updated = [...generatedWorkflow.steps];
                                  updated[idx] = { ...step, instructions: e.target.value };
                                  setGeneratedWorkflow({ ...generatedWorkflow, steps: updated });
                                }}
                                className="w-full text-xs font-mono bg-canvas border border-hairline rounded p-2 text-ink focus:outline-none leading-relaxed resize-y"
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Save Footer */}
              <div className="pt-2 border-t border-hairline flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={handleSaveAndOpen}
                  disabled={isSaving}
                  className="px-4 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors shadow-card flex items-center gap-1.5 disabled:opacity-50"
                >
                  {isSaving ? (
                    <>
                      <span className="w-3 h-3 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                      <span>Creating & Launching Studio...</span>
                    </>
                  ) : (
                    <>
                      <span>Create & Open Studio</span>
                      <ArrowRight size={12} />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
