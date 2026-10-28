"use client";

import React from "react";
import {
  WorkflowStep,
  ScriptTool,
  KnowledgeFile,
} from "../types";
import {
  Plus,
  Trash2,
  ChevronUp,
  ChevronDown,
  Bot,
  Zap,
  FileText,
  Play,
  Layers,
  ArrowRight,
} from "lucide-react";

interface StepCardEditorProps {
  steps: WorkflowStep[];
  onChangeSteps: (steps: WorkflowStep[]) => void;
  agents: Array<{ id: string; name: string; role?: string; icon?: string }>;
  tools: ScriptTool[];
  knowledgeFiles: KnowledgeFile[];
  onUnitTestStep?: (step: WorkflowStep) => void;
  readOnly?: boolean;
}

export default function StepCardEditor({
  steps,
  onChangeSteps,
  agents,
  tools,
  knowledgeFiles,
  onUnitTestStep,
  readOnly = false,
}: StepCardEditorProps) {
  const handleAddStep = () => {
    if (readOnly) return;
    const newIdx = steps.length + 1;
    const newStep: WorkflowStep = {
      id: `step_${newIdx}_${Date.now().toString(36).slice(-4)}`,
      name: `Step ${newIdx}: New Action`,
      agent_id: agents[0]?.id || "orchestrator",
      instructions: `Analyze inputs: {{inputs.query}} and execute action based on goal: {{goal}}`,
      tool_ids: [],
      knowledge_file_ids: [],
      depends_on: steps.length > 0 ? [steps[steps.length - 1].id] : [],
    };
    onChangeSteps([...steps, newStep]);
  };

  const handleUpdateStep = (index: number, updates: Partial<WorkflowStep>) => {
    if (readOnly) return;
    const nextSteps = [...steps];
    nextSteps[index] = { ...nextSteps[index], ...updates };
    onChangeSteps(nextSteps);
  };

  const handleDeleteStep = (index: number) => {
    if (readOnly) return;
    const targetId = steps[index].id;
    const nextSteps = steps
      .filter((_, i) => i !== index)
      .map((s) => ({
        ...s,
        depends_on: s.depends_on.filter((dep) => dep !== targetId),
      }));
    onChangeSteps(nextSteps);
  };

  const handleMove = (index: number, direction: "up" | "down") => {
    if (readOnly) return;
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= steps.length) return;
    const nextSteps = [...steps];
    const [moved] = nextSteps.splice(index, 1);
    nextSteps.splice(targetIndex, 0, moved);
    onChangeSteps(nextSteps);
  };

  const handleInsertTag = (index: number, tag: string) => {
    if (readOnly) return;
    const current = steps[index].instructions || "";
    handleUpdateStep(index, { instructions: `${current} ${tag}`.trim() });
  };

  return (
    <div className="space-y-4">
      {steps.length === 0 ? (
        <div className="p-8 text-center border-2 border-dashed border-border/80 rounded-2xl bg-card/40">
          <Layers className="w-10 h-10 text-muted-foreground mx-auto mb-3 opacity-60" />
          <h4 className="text-base font-semibold text-foreground">No steps in this workflow yet</h4>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto mt-1 mb-4">
            Add steps to instruct agents, run sandboxed Python tools, and process knowledge files.
          </p>
          {!readOnly && (
            <button
              onClick={handleAddStep}
              className="px-4 py-2 bg-primary text-primary-foreground text-xs font-medium rounded-xl hover:opacity-90 transition inline-flex items-center gap-1.5 shadow-subtle"
            >
              <Plus size={14} /> Add First Step
            </button>
          )}
        </div>
      ) : (
        steps.map((step, idx) => {
          const priorSteps = steps.slice(0, idx);

          return (
            <div
              key={step.id}
              className="p-5 rounded-2xl bg-card border border-border/80 shadow-subtle space-y-4 transition hover:border-primary/30"
            >
              {/* Step Card Header */}
              <div className="flex items-center justify-between gap-3 border-b border-border/60 pb-3">
                <div className="flex items-center gap-2.5 flex-1">
                  <span className="w-6 h-6 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs font-semibold flex items-center justify-center shrink-0">
                    {idx + 1}
                  </span>
                  <input
                    type="text"
                    disabled={readOnly}
                    value={step.name}
                    onChange={(e) => handleUpdateStep(idx, { name: e.target.value })}
                    className="font-medium text-sm text-foreground bg-transparent border-b border-transparent hover:border-border focus:border-primary focus:outline-none px-1 py-0.5 w-full transition"
                    placeholder="Step Name"
                  />
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  {onUnitTestStep && (
                    <button
                      onClick={() => onUnitTestStep(step)}
                      className="px-2.5 py-1 text-xs font-medium text-emerald-500 hover:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg hover:bg-emerald-500/20 transition flex items-center gap-1"
                      title="Run isolated unit test on this step"
                    >
                      <Play size={11} className="fill-current" /> Unit Test
                    </button>
                  )}

                  {!readOnly && (
                    <>
                      <button
                        onClick={() => handleMove(idx, "up")}
                        disabled={idx === 0}
                        className="p-1 rounded text-muted-foreground hover:text-foreground disabled:opacity-30 transition"
                        title="Move Up"
                      >
                        <ChevronUp size={16} />
                      </button>
                      <button
                        onClick={() => handleMove(idx, "down")}
                        disabled={idx === steps.length - 1}
                        className="p-1 rounded text-muted-foreground hover:text-foreground disabled:opacity-30 transition"
                        title="Move Down"
                      >
                        <ChevronDown size={16} />
                      </button>
                      <button
                        onClick={() => handleDeleteStep(idx)}
                        className="p-1 rounded text-destructive/80 hover:text-destructive hover:bg-destructive/10 transition"
                        title="Delete Step"
                      >
                        <Trash2 size={16} />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Step Controls Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Agent Selection */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block flex items-center gap-1">
                    <Bot size={13} className="text-primary" /> Assigned Agent
                  </label>
                  <select
                    disabled={readOnly}
                    value={step.agent_id}
                    onChange={(e) => handleUpdateStep(idx, { agent_id: e.target.value })}
                    className="w-full text-xs bg-background/80 border border-border rounded-xl px-3 py-2 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    {agents.map((ag) => (
                      <option key={ag.id} value={ag.id}>
                        {ag.name} ({ag.role || ag.id})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Predecessor Dependencies */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block flex items-center gap-1">
                    <ArrowRight size={13} className="text-accent" /> Depends On
                  </label>
                  <div className="flex flex-wrap gap-1.5 min-h-[34px] items-center p-1.5 rounded-xl border border-border bg-background/50">
                    {priorSteps.length === 0 ? (
                      <span className="text-[11px] text-muted-foreground/70 px-1">Initial entry step (no dependencies)</span>
                    ) : (
                      priorSteps.map((p) => {
                        const isDep = step.depends_on.includes(p.id);
                        return (
                          <button
                            key={p.id}
                            type="button"
                            disabled={readOnly}
                            onClick={() => {
                              const newDeps = isDep
                                ? step.depends_on.filter((d) => d !== p.id)
                                : [...step.depends_on, p.id];
                              handleUpdateStep(idx, { depends_on: newDeps });
                            }}
                            className={`px-2 py-0.5 text-[11px] rounded-lg border font-mono transition ${
                              isDep
                                ? "bg-primary/15 border-primary/40 text-primary font-medium"
                                : "bg-card border-border text-muted-foreground hover:border-primary/20"
                            }`}
                          >
                            {p.name.slice(0, 18)}
                          </button>
                        );
                      })
                    )}
                  </div>
                </div>
              </div>

              {/* Step Prompt Instructions */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-medium text-muted-foreground">
                    Prompt Instructions & Variable Interpolation
                  </label>
                  {!readOnly && (
                    <div className="flex items-center gap-1 text-[11px]">
                      <span className="text-muted-foreground">Insert:</span>
                      <button
                        type="button"
                        onClick={() => handleInsertTag(idx, "{{goal}}")}
                        className="px-1.5 py-0.5 rounded bg-card border border-border hover:border-primary text-primary font-mono text-[10px]"
                      >
                        {"{{goal}}"}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleInsertTag(idx, "{{inputs.query}}")}
                        className="px-1.5 py-0.5 rounded bg-card border border-border hover:border-primary text-primary font-mono text-[10px]"
                      >
                        {"{{inputs.query}}"}
                      </button>
                      {priorSteps.map((p) => (
                        <button
                          key={p.id}
                          type="button"
                          onClick={() => handleInsertTag(idx, `{{steps.${p.id}.output.text}}`)}
                          className="px-1.5 py-0.5 rounded bg-card border border-border hover:border-primary text-accent font-mono text-[10px]"
                        >
                          {`{{${p.id}.output}}`}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <textarea
                  disabled={readOnly}
                  rows={3}
                  value={step.instructions}
                  onChange={(e) => handleUpdateStep(idx, { instructions: e.target.value })}
                  placeholder="Describe what the agent should do in this step..."
                  className="w-full text-xs font-mono bg-background/80 border border-border rounded-xl p-3 text-foreground focus:outline-none focus:ring-1 focus:ring-primary leading-relaxed resize-y"
                />
              </div>

              {/* Attached Tools & Knowledge Files */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1 border-t border-border/50 text-xs">
                {/* Script Tools */}
                <div>
                  <span className="font-medium text-muted-foreground flex items-center gap-1 mb-1.5">
                    <Zap size={12} className="text-amber-500" /> Attached Script Tools
                  </span>
                  {tools.length === 0 ? (
                    <span className="text-[11px] text-muted-foreground/60 italic">No tools available in library.</span>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {tools.map((tool) => {
                        const isAttached = step.tool_ids.includes(tool.id);
                        return (
                          <button
                            key={tool.id}
                            type="button"
                            disabled={readOnly}
                            onClick={() => {
                              const newToolIds = isAttached
                                ? step.tool_ids.filter((t) => t !== tool.id)
                                : [...step.tool_ids, tool.id];
                              handleUpdateStep(idx, { tool_ids: newToolIds });
                            }}
                            className={`px-2 py-0.5 rounded-lg border text-[11px] transition ${
                              isAttached
                                ? "bg-amber-500/15 border-amber-500/40 text-amber-500 font-medium"
                                : "bg-card border-border text-muted-foreground hover:border-amber-500/30"
                            }`}
                          >
                            ⚡ {tool.name}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Knowledge Base Files */}
                <div>
                  <span className="font-medium text-muted-foreground flex items-center gap-1 mb-1.5">
                    <FileText size={12} className="text-blue-500" /> Attached Knowledge Files
                  </span>
                  {knowledgeFiles.length === 0 ? (
                    <span className="text-[11px] text-muted-foreground/60 italic">No files in workflow knowledge base.</span>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {knowledgeFiles.map((file) => {
                        const isAttached = step.knowledge_file_ids.includes(file.id);
                        return (
                          <button
                            key={file.id}
                            type="button"
                            disabled={readOnly}
                            onClick={() => {
                              const newKfIds = isAttached
                                ? step.knowledge_file_ids.filter((k) => k !== file.id)
                                : [...step.knowledge_file_ids, file.id];
                              handleUpdateStep(idx, { knowledge_file_ids: newKfIds });
                            }}
                            className={`px-2 py-0.5 rounded-lg border text-[11px] transition ${
                              isAttached
                                ? "bg-blue-500/15 border-blue-500/40 text-blue-500 font-medium"
                                : "bg-card border-border text-muted-foreground hover:border-blue-500/30"
                            }`}
                          >
                            📄 {file.file_name}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })
      )}

      {!readOnly && steps.length > 0 && (
        <button
          onClick={handleAddStep}
          className="w-full py-2.5 border border-dashed border-border/80 rounded-xl bg-card/40 hover:bg-card hover:border-primary text-xs font-medium text-muted-foreground hover:text-foreground transition flex items-center justify-center gap-1.5"
        >
          <Plus size={14} /> Add Another Step
        </button>
      )}
    </div>
  );
}
