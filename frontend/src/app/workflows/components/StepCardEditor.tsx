"use client";

import React, { useState } from "react";
import {
  WorkflowStep,
  ScriptTool,
  KnowledgeFile,
  WorkflowStepType,
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
  GitBranch,
  Terminal,
  RotateCcw,
  FileOutput,
  Cpu,
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
  const [showAddMenu, setShowAddMenu] = useState(false);

  const handleAddBlock = (blockType: WorkflowStepType) => {
    if (readOnly) return;
    const nextIdx = steps.length + 1;
    const newStepId = `step_${nextIdx}_${Date.now().toString(36).slice(-3)}`;
    const previousStepId = steps.length > 0 ? steps[steps.length - 1].id : undefined;

    let newStep: WorkflowStep;

    switch (blockType) {
      case "condition":
        newStep = {
          id: newStepId,
          name: `Step ${nextIdx}: Condition Check`,
          step_type: "condition",
          agent_id: "orchestrator",
          condition_expr: "len(inputs.get('query', '')) > 0",
          instructions: "Evaluate condition expression",
          tool_ids: [],
          knowledge_file_ids: [],
          depends_on: previousStepId ? [previousStepId] : [],
        };
        break;

      case "python_code":
        newStep = {
          id: newStepId,
          name: `Step ${nextIdx}: Python Processing`,
          step_type: "python_code",
          agent_id: "coder",
          code: "def execute(inputs, previous_outputs, context):\n    # Process data with Python\n    text = inputs.get('query', '')\n    return {'status': 'processed', 'length': len(text)}",
          instructions: "Execute sandboxed Python script",
          tool_ids: [],
          knowledge_file_ids: [],
          depends_on: previousStepId ? [previousStepId] : [],
        };
        break;

      case "loop":
        newStep = {
          id: newStepId,
          name: `Step ${nextIdx}: Iteration Loop`,
          step_type: "loop",
          agent_id: "orchestrator",
          loop_target_step_id: previousStepId,
          max_loop_iterations: 3,
          condition_expr: "context.get('loop_count', 0) < 3",
          instructions: "Loop back to target step until iteration limit",
          tool_ids: [],
          knowledge_file_ids: [],
          depends_on: previousStepId ? [previousStepId] : [],
        };
        break;

      case "artifact":
        newStep = {
          id: newStepId,
          name: `Step ${nextIdx}: Generate Artifact`,
          step_type: "artifact",
          agent_id: "synthesizer",
          artifact_title: `Generated Report ${nextIdx}`,
          artifact_type: "markdown",
          instructions: "# Final Report\n\nGenerated automatically by Swarm Backend Pipeline.",
          tool_ids: [],
          knowledge_file_ids: [],
          depends_on: previousStepId ? [previousStepId] : [],
        };
        break;

      default: // agent
        newStep = {
          id: newStepId,
          name: `Step ${nextIdx}: Specialist Action`,
          step_type: "agent",
          agent_id: agents[0]?.id || "orchestrator",
          model: "gemini-3.8-flash",
          instructions: previousStepId
            ? `Synthesize input from predecessor: {{steps.${previousStepId}.output.text}}`
            : "Analyze inputs: {{inputs.query}} and execute action based on goal: {{goal}}",
          tool_ids: [],
          knowledge_file_ids: [],
          depends_on: previousStepId ? [previousStepId] : [],
        };
        break;
    }

    onChangeSteps([...steps, newStep]);
    setShowAddMenu(false);
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
        true_target_step_id: s.true_target_step_id === targetId ? undefined : s.true_target_step_id,
        false_target_step_id: s.false_target_step_id === targetId ? undefined : s.false_target_step_id,
        loop_target_step_id: s.loop_target_step_id === targetId ? undefined : s.loop_target_step_id,
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

  const getBlockBadge = (type?: WorkflowStepType) => {
    switch (type) {
      case "condition":
        return {
          label: "Condition",
          icon: <GitBranch size={12} className="text-amber-400" />,
          classes: "bg-amber-500/10 border-amber-500/30 text-amber-400",
        };
      case "python_code":
        return {
          label: "Python Code",
          icon: <Terminal size={12} className="text-emerald-400" />,
          classes: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
        };
      case "loop":
        return {
          label: "Loop",
          icon: <RotateCcw size={12} className="text-cyan-400" />,
          classes: "bg-cyan-500/10 border-cyan-500/30 text-cyan-400",
        };
      case "artifact":
        return {
          label: "Artifact",
          icon: <FileOutput size={12} className="text-purple-400" />,
          classes: "bg-purple-500/10 border-purple-500/30 text-purple-400",
        };
      default:
        return {
          label: "Agent",
          icon: <Bot size={12} className="text-linear-primary" />,
          classes: "bg-surface-2 border-hairline text-linear-primary",
        };
    }
  };

  return (
    <div className="space-y-4 font-sans">
      {steps.length === 0 ? (
        <div className="p-8 text-center border border-dashed border-hairline rounded-lg bg-surface-1">
          <Layers className="w-10 h-10 text-ink-subtle mx-auto mb-3 opacity-60" />
          <h4 className="text-sm font-semibold text-ink">No steps in this workflow yet</h4>
          <p className="text-xs text-ink-subtle max-w-sm mx-auto mt-1 mb-4 leading-relaxed">
            Add blocks to orchestrate AI agents, evaluate conditional branches, execute sandboxed Python scripts, iterate loops, and generate artifacts.
          </p>
          {!readOnly && (
            <div className="flex flex-wrap items-center justify-center gap-2">
              <button
                type="button"
                onClick={() => handleAddBlock("agent")}
                className="px-3 py-1.5 bg-linear-primary hover:bg-linear-hover text-white text-xs font-medium rounded-md transition inline-flex items-center gap-1.5 shadow-card"
              >
                <Bot size={13} /> Add Agent Step
              </button>
              <button
                type="button"
                onClick={() => handleAddBlock("condition")}
                className="px-3 py-1.5 bg-surface-2 hover:bg-surface-1 border border-hairline text-amber-400 text-xs font-medium rounded-md transition inline-flex items-center gap-1.5"
              >
                <GitBranch size={13} /> Add Condition
              </button>
              <button
                type="button"
                onClick={() => handleAddBlock("python_code")}
                className="px-3 py-1.5 bg-surface-2 hover:bg-surface-1 border border-hairline text-emerald-400 text-xs font-medium rounded-md transition inline-flex items-center gap-1.5"
              >
                <Terminal size={13} /> Add Python
              </button>
            </div>
          )}
        </div>
      ) : (
        steps.map((step, idx) => {
          const priorSteps = steps.slice(0, idx);
          const blockType = step.step_type || "agent";
          const badge = getBlockBadge(blockType);

          return (
            <div
              key={step.id}
              className="p-5 rounded-lg bg-surface-1 border border-hairline shadow-card space-y-4 transition hover:border-hairline-strong"
            >
              {/* Step Card Header */}
              <div className="flex items-center justify-between gap-3 border-b border-hairline pb-3">
                <div className="flex items-center gap-2.5 flex-1 min-w-0">
                  <span className="w-6 h-6 rounded-md bg-surface-2 text-ink-subtle border border-hairline text-[11px] font-mono font-medium flex items-center justify-center shrink-0">
                    #{idx + 1}
                  </span>

                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <span
                      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-xs border text-[9px] font-mono uppercase shrink-0 ${badge.classes}`}
                    >
                      {badge.icon}
                      <span>{badge.label}</span>
                    </span>

                    <input
                      type="text"
                      disabled={readOnly}
                      value={step.name}
                      onChange={(e) => handleUpdateStep(idx, { name: e.target.value })}
                      className="font-medium text-xs text-ink bg-transparent border-b border-transparent hover:border-hairline focus:border-linear-focus focus:outline-none px-1 py-0.5 w-full transition tracking-card-title truncate"
                      placeholder="Step Name"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  {/* Block Type Switcher */}
                  <select
                    disabled={readOnly}
                    value={step.step_type || "agent"}
                    onChange={(e) =>
                      handleUpdateStep(idx, {
                        step_type: e.target.value as WorkflowStepType,
                      })
                    }
                    className="text-[10px] font-mono bg-surface-2 border border-hairline rounded-md px-2 py-1 text-ink focus:outline-none cursor-pointer"
                  >
                    <option value="agent">Agent Block</option>
                    <option value="condition">Condition Branch</option>
                    <option value="python_code">Python Processor</option>
                    <option value="loop">Iteration Loop</option>
                    <option value="artifact">Artifact Generator</option>
                  </select>

                  {onUnitTestStep && (
                    <button
                      type="button"
                      onClick={() => onUnitTestStep(step)}
                      className="px-2.5 py-1 text-xs font-medium text-semantic-success hover:text-white bg-surface-2 border border-hairline rounded-md hover:bg-surface-1 transition flex items-center gap-1"
                      title="Run isolated unit test on this step"
                    >
                      <Play size={10} className="fill-current" /> Test
                    </button>
                  )}

                  {!readOnly && (
                    <>
                      <button
                        type="button"
                        onClick={() => handleMove(idx, "up")}
                        disabled={idx === 0}
                        className="p-1 rounded text-ink-subtle hover:text-ink disabled:opacity-20 transition"
                        title="Move Up"
                      >
                        <ChevronUp size={14} />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleMove(idx, "down")}
                        disabled={idx === steps.length - 1}
                        className="p-1 rounded text-ink-subtle hover:text-ink disabled:opacity-20 transition"
                        title="Move Down"
                      >
                        <ChevronDown size={14} />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteStep(idx)}
                        className="p-1 rounded text-ink-subtle hover:text-red-400 transition"
                        title="Delete Step"
                      >
                        <Trash2 size={14} />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Dependencies Section */}
              <div>
                <label className="text-[10px] font-medium text-ink-tertiary mb-1 block flex items-center gap-1">
                  <ArrowRight size={11} className="text-linear-primary" /> Dependencies (Inputs from Predecessors)
                </label>
                <div className="flex flex-wrap gap-1.5 min-h-[30px] items-center p-1.5 rounded-md border border-hairline bg-canvas">
                  {priorSteps.length === 0 ? (
                    <span className="text-[10px] text-ink-tertiary px-1">
                      Initial entry step (receives goal and initial query)
                    </span>
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
                          className={`px-2 py-0.5 text-[10px] rounded-xs border font-mono transition ${
                            isDep
                              ? "bg-surface-2 border-linear-primary text-linear-primary font-medium"
                              : "bg-surface-1 border-hairline text-ink-muted hover:border-hairline-strong"
                          }`}
                        >
                          {p.name.slice(0, 24)}
                        </button>
                      );
                    })
                  )}
                </div>
              </div>

              {/* BLOCK TYPE SPECIFIC CONTROLS */}

              {/* 1. AGENT BLOCK */}
              {blockType === "agent" && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {/* Agent Selection */}
                    <div>
                      <label className="text-[10px] font-medium text-ink-tertiary mb-1 block flex items-center gap-1">
                        <Bot size={11} className="text-linear-primary" /> Assigned Specialist Agent
                      </label>
                      <select
                        disabled={readOnly}
                        value={step.agent_id}
                        onChange={(e) => handleUpdateStep(idx, { agent_id: e.target.value })}
                        className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none focus:border-linear-focus"
                      >
                        {agents.map((ag) => (
                          <option key={ag.id} value={ag.id}>
                            {ag.name} ({ag.role || ag.id})
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Model Selection */}
                    <div>
                      <label className="text-[10px] font-medium text-ink-tertiary mb-1 block flex items-center gap-1">
                        <Cpu size={11} className="text-linear-primary" /> Model Selection
                      </label>
                      <select
                        disabled={readOnly}
                        value={step.model || "gemini-3.8-flash"}
                        onChange={(e) => handleUpdateStep(idx, { model: e.target.value })}
                        className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none focus:border-linear-focus"
                      >
                        <option value="gemini-3.8-flash">Gemini 3.8 Flash (Fast Execution)</option>
                        <option value="gemini-4-argon">Gemini 4 Argon (Deep Complex Reasoning)</option>
                        <option value="sonar">Perplexity Sonar (Real Live Web Search)</option>
                        <option value="sonar-pro">Perplexity Sonar Pro (Advanced Synthesis)</option>
                      </select>
                    </div>
                  </div>

                  {/* Instructions */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-[10px] font-medium text-ink-tertiary">
                        Prompt Instructions & Variable Interpolation
                      </label>
                      {!readOnly && (
                        <div className="flex items-center gap-1 text-[10px]">
                          <span className="text-ink-tertiary">Insert:</span>
                          <button
                            type="button"
                            onClick={() => handleInsertTag(idx, "{{goal}}")}
                            className="px-1.5 py-0.2 rounded-xs bg-surface-2 border border-hairline hover:border-hairline-strong text-linear-primary font-mono"
                          >
                            {"{{goal}}"}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleInsertTag(idx, "{{inputs.query}}")}
                            className="px-1.5 py-0.2 rounded-xs bg-surface-2 border border-hairline hover:border-hairline-strong text-linear-primary font-mono"
                          >
                            {"{{inputs.query}}"}
                          </button>
                          {priorSteps.map((p) => (
                            <button
                              key={p.id}
                              type="button"
                              onClick={() => handleInsertTag(idx, `{{steps.${p.id}.output.text}}`)}
                              className="px-1.5 py-0.2 rounded-xs bg-surface-2 border border-hairline hover:border-hairline-strong text-ink font-mono"
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
                      className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md p-2.5 text-ink focus:outline-none focus:border-linear-focus leading-relaxed resize-y"
                    />
                  </div>

                  {/* Tools & Files */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-hairline text-xs">
                    <div>
                      <span className="font-medium text-ink-subtle flex items-center gap-1 mb-1.5 text-[10px]">
                        <Zap size={11} className="text-amber-400" /> Attached Script Tools
                      </span>
                      {tools.length === 0 ? (
                        <span className="text-[10px] text-ink-tertiary italic">No tools available in library.</span>
                      ) : (
                        <div className="flex flex-wrap gap-1">
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
                                className={`px-2 py-0.5 rounded-xs border text-[10px] transition ${
                                  isAttached
                                    ? "bg-amber-500/15 border-amber-500/40 text-amber-400 font-medium"
                                    : "bg-surface-2 border-hairline text-ink-muted hover:border-hairline-strong"
                                }`}
                              >
                                ⚡ {tool.name}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    <div>
                      <span className="font-medium text-ink-subtle flex items-center gap-1 mb-1.5 text-[10px]">
                        <FileText size={11} className="text-linear-primary" /> Attached Knowledge Files
                      </span>
                      {knowledgeFiles.length === 0 ? (
                        <span className="text-[10px] text-ink-tertiary italic">No files in workflow knowledge base.</span>
                      ) : (
                        <div className="flex flex-wrap gap-1">
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
                                className={`px-2 py-0.5 rounded-xs border text-[10px] transition ${
                                  isAttached
                                    ? "bg-surface-2 border-linear-primary text-linear-primary font-medium"
                                    : "bg-surface-2 border-hairline text-ink-muted hover:border-hairline-strong"
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
              )}

              {/* 2. CONDITION BLOCK */}
              {blockType === "condition" && (
                <div className="space-y-3">
                  <div>
                    <label className="text-[10px] font-medium text-amber-400 mb-1 block flex items-center justify-between">
                      <span>Condition Expression (Safe Python AST Evaluation)</span>
                      <span className="text-[9px] text-ink-tertiary font-mono">e.g. len(inputs.query) &gt; 10</span>
                    </label>
                    <input
                      type="text"
                      disabled={readOnly}
                      value={step.condition_expr || ""}
                      onChange={(e) => handleUpdateStep(idx, { condition_expr: e.target.value })}
                      placeholder="inputs.get('status') == 'success' or len(inputs.query) > 10"
                      className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-amber-300 focus:outline-none focus:border-amber-400"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] font-medium text-emerald-400 mb-1 block">
                        Target Step if TRUE
                      </label>
                      <select
                        disabled={readOnly}
                        value={step.true_target_step_id || ""}
                        onChange={(e) => handleUpdateStep(idx, { true_target_step_id: e.target.value })}
                        className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none"
                      >
                        <option value="">Default (Execute Next Step in Sequence)</option>
                        {steps.filter((s) => s.id !== step.id).map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name} ({s.id})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="text-[10px] font-medium text-rose-400 mb-1 block">
                        Target Step if FALSE
                      </label>
                      <select
                        disabled={readOnly}
                        value={step.false_target_step_id || ""}
                        onChange={(e) => handleUpdateStep(idx, { false_target_step_id: e.target.value })}
                        className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none"
                      >
                        <option value="">Default (End Workflow Run)</option>
                        {steps.filter((s) => s.id !== step.id).map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name} ({s.id})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* 3. PYTHON CODE BLOCK */}
              {blockType === "python_code" && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[10px] font-medium text-emerald-400 flex items-center gap-1">
                      <Terminal size={11} /> Inline Python Script
                    </label>
                    <span className="text-[9px] text-ink-tertiary font-mono">def execute(inputs, previous_outputs, context):</span>
                  </div>
                  <textarea
                    disabled={readOnly}
                    rows={6}
                    value={
                      step.code ||
                      "def execute(inputs, previous_outputs, context):\n    # Custom processing\n    query = inputs.get('query', '')\n    return {'result': query.upper(), 'status': 'ok'}"
                    }
                    onChange={(e) => handleUpdateStep(idx, { code: e.target.value })}
                    className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md p-2.5 text-emerald-300 focus:outline-none focus:border-emerald-400 resize-y"
                  />
                  <div className="text-[10px] text-ink-tertiary font-mono">
                    Executed inside AST security sandbox. Function must return a dictionary.
                  </div>
                </div>
              )}

              {/* 4. LOOP BLOCK */}
              {blockType === "loop" && (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] font-medium text-cyan-400 mb-1 block">
                        Loop Back Target Step
                      </label>
                      <select
                        disabled={readOnly}
                        value={step.loop_target_step_id || ""}
                        onChange={(e) => handleUpdateStep(idx, { loop_target_step_id: e.target.value })}
                        className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none"
                      >
                        <option value="">Select target step to loop back to...</option>
                        {steps.filter((s) => s.id !== step.id).map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name} ({s.id})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="text-[10px] font-medium text-cyan-400 mb-1 block">
                        Max Iterations (1-10)
                      </label>
                      <input
                        type="number"
                        min={1}
                        max={10}
                        disabled={readOnly}
                        value={step.max_loop_iterations ?? 3}
                        onChange={(e) =>
                          handleUpdateStep(idx, {
                            max_loop_iterations: parseInt(e.target.value, 10) || 1,
                          })
                        }
                        className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] font-medium text-ink-tertiary mb-1 block">
                      Termination Condition Expression (Optional)
                    </label>
                    <input
                      type="text"
                      disabled={readOnly}
                      value={step.condition_expr || ""}
                      onChange={(e) => handleUpdateStep(idx, { condition_expr: e.target.value })}
                      placeholder="context.get('loop_count', 0) < 3"
                      className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none"
                    />
                  </div>
                </div>
              )}

              {/* 5. ARTIFACT BLOCK */}
              {blockType === "artifact" && (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] font-medium text-purple-400 mb-1 block">
                        Artifact Title
                      </label>
                      <input
                        type="text"
                        disabled={readOnly}
                        value={step.artifact_title || ""}
                        onChange={(e) => handleUpdateStep(idx, { artifact_title: e.target.value })}
                        placeholder="e.g. Executive Analysis Report"
                        className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none"
                      />
                    </div>

                    <div>
                      <label className="text-[10px] font-medium text-purple-400 mb-1 block">
                        Artifact Type
                      </label>
                      <select
                        disabled={readOnly}
                        value={step.artifact_type || "markdown"}
                        onChange={(e) => handleUpdateStep(idx, { artifact_type: e.target.value })}
                        className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none"
                      >
                        <option value="markdown">Markdown Document (.md)</option>
                        <option value="code">Source Code (.py / .ts)</option>
                        <option value="json">Structured JSON (.json)</option>
                        <option value="report">Executive Report (.md)</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] font-medium text-ink-tertiary mb-1 block">
                      Content / Markdown Template
                    </label>
                    <textarea
                      disabled={readOnly}
                      rows={4}
                      value={step.instructions || ""}
                      onChange={(e) => handleUpdateStep(idx, { instructions: e.target.value })}
                      placeholder="Provide markdown template or instructions for artifact formatting..."
                      className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md p-2.5 text-ink focus:outline-none resize-y"
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })
      )}

      {/* Add Step Action */}
      {!readOnly && (
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowAddMenu(!showAddMenu)}
            className="w-full py-2.5 border border-dashed border-hairline hover:border-hairline-strong rounded-lg bg-surface-1/50 hover:bg-surface-1 text-xs font-medium text-ink-subtle hover:text-ink transition flex items-center justify-center gap-1.5 shadow-card"
          >
            <Plus size={13} />
            <span>Add Workflow Block</span>
            <ChevronDown size={11} className={`transition-transform ${showAddMenu ? "rotate-180" : ""}`} />
          </button>

          {showAddMenu && (
            <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-64 p-1.5 rounded-md bg-surface-1 border border-hairline shadow-card z-30 space-y-1">
              <button
                type="button"
                onClick={() => handleAddBlock("agent")}
                className="w-full text-left px-2 py-1.5 rounded text-xs text-ink hover:bg-surface-2 flex items-center gap-2"
              >
                <Bot size={13} className="text-linear-primary" />
                <div>
                  <div className="font-medium">Agent Step</div>
                  <div className="text-[10px] text-ink-subtle">Specialist LLM agent</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleAddBlock("condition")}
                className="w-full text-left px-2 py-1.5 rounded text-xs text-ink hover:bg-surface-2 flex items-center gap-2"
              >
                <GitBranch size={13} className="text-amber-400" />
                <div>
                  <div className="font-medium">Condition Branch</div>
                  <div className="text-[10px] text-ink-subtle">If / Else routing</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleAddBlock("python_code")}
                className="w-full text-left px-2 py-1.5 rounded text-xs text-ink hover:bg-surface-2 flex items-center gap-2"
              >
                <Terminal size={13} className="text-emerald-400" />
                <div>
                  <div className="font-medium">Python Processor</div>
                  <div className="text-[10px] text-ink-subtle">Sandboxed data compute</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleAddBlock("loop")}
                className="w-full text-left px-2 py-1.5 rounded text-xs text-ink hover:bg-surface-2 flex items-center gap-2"
              >
                <RotateCcw size={13} className="text-cyan-400" />
                <div>
                  <div className="font-medium">Loop Block</div>
                  <div className="text-[10px] text-ink-subtle">Iterate to step (max 10x)</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleAddBlock("artifact")}
                className="w-full text-left px-2 py-1.5 rounded text-xs text-ink hover:bg-surface-2 flex items-center gap-2"
              >
                <FileOutput size={13} className="text-purple-400" />
                <div>
                  <div className="font-medium">Artifact Generator</div>
                  <div className="text-[10px] text-ink-subtle">Reports & structured files</div>
                </div>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
