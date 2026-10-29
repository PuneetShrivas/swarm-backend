"use client";

import React, { useState } from "react";
import { getAuthHeaders } from "@/lib/supabase";
import { AgentCardData } from "./AgentCard";
import {
  X,
  Sparkles,
  Terminal,
  Cpu,
  Check,
  Save,
  Play,
} from "lucide-react";

interface AIAgentGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: (agent: AgentCardData) => void;
  onTestAgent?: (agent: AgentCardData) => void;
}

const SAMPLE_IDEAS = [
  "Database Query Optimizer that analyzes PostgreSQL execution plans and suggests indexes",
  "Cloud Security Auditor for AWS Terraform infrastructure and IAM least privilege policies",
  "FinTech Risk Analyst calculating portfolio Value-at-Risk and liquidity metrics",
  "API Architect evaluating REST and GraphQL schema design against best practices",
];

export default function AIAgentGeneratorModal({
  isOpen,
  onClose,
  onSaved,
  onTestAgent,
}: AIAgentGeneratorModalProps) {
  const [prompt, setPrompt] = useState(SAMPLE_IDEAS[0]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Generated Agent State
  const [generatedAgent, setGeneratedAgent] = useState<AgentCardData | null>(null);

  if (!isOpen) return null;

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    setIsGenerating(true);
    setErrorMessage(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const authHeaders = await getAuthHeaders();

      const res = await fetch(`${apiUrl}/api/ai/generate-agent`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "AI agent generation failed.");
      }

      const data = await res.json();
      const rawAgent = data.agent || {};

      const newAgent: AgentCardData = {
        id: rawAgent.id || `agent-${Date.now().toString(36)}`,
        name: rawAgent.name || "AI Generated Specialist",
        role: rawAgent.role || "Domain Specialist",
        description: rawAgent.description || prompt.trim(),
        system_prompt: rawAgent.system_prompt || "You are a specialized AI assistant.",
        model: rawAgent.model || "qwen-3.8",
        temperature: rawAgent.temperature ?? 0.3,
        icon: rawAgent.icon || "Bot",
        is_custom: true,
        tools: rawAgent.tools || [],
        skills: rawAgent.skills || [],
      };

      setGeneratedAgent(newAgent);
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "Failed to generate agent.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveToRoster = async () => {
    if (!generatedAgent) return;

    setIsSaving(true);
    setErrorMessage(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const authHeaders = await getAuthHeaders();

      const res = await fetch(`${apiUrl}/api/custom-agents`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(generatedAgent),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save generated agent.");
      }

      const saved: AgentCardData = await res.json();
      onSaved(saved);
      onClose();
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "Save error.");
    } finally {
      setIsSaving(false);
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
              <h3 className="text-xs font-semibold text-ink tracking-tight">
                AI Agent Generator
              </h3>
              <p className="text-[10px] text-ink-subtle">
                Generate agent system prompts, tool bindings, and model configurations from a prompt
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
                Describe the Agent You Need
              </label>
            </div>

            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Create a database query optimizer that inspects SQL execution plans, recommends indexes, and detects slow queries..."
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
                  <span>Synthesizing Agent...</span>
                </>
              ) : (
                <>
                  <Sparkles size={11} />
                  <span>{generatedAgent ? "Regenerate Agent" : "Generate Agent"}</span>
                </>
              )}
            </button>
          </div>

          {/* Generated Agent Review & Edit Card */}
          {generatedAgent && (
            <div className="p-4 rounded-lg bg-surface-1 border border-hairline space-y-3 mt-3 animate-fade-in">
              <div className="flex items-center justify-between pb-2 border-b border-hairline">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold flex items-center gap-1">
                    <Check size={11} /> Generated Specification
                  </span>
                  <span className="text-xs font-semibold text-ink">Review & Refine</span>
                </div>

                <div className="flex items-center gap-2">
                  {onTestAgent && (
                    <button
                      type="button"
                      onClick={() => onTestAgent(generatedAgent)}
                      className="px-2 py-1 text-[11px] font-medium text-semantic-success hover:bg-surface-2 rounded border border-hairline flex items-center gap-1"
                      title="Test this agent in Playground before saving"
                    >
                      <Play size={10} className="fill-current" />
                      <span>Test in Playground</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Editable Fields */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-medium text-ink-subtle mb-1 block">
                    Agent Name
                  </label>
                  <input
                    type="text"
                    value={generatedAgent.name}
                    onChange={(e) =>
                      setGeneratedAgent({ ...generatedAgent, name: e.target.value })
                    }
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none focus:border-linear-focus font-medium"
                  />
                </div>

                <div>
                  <label className="text-[10px] font-medium text-ink-subtle mb-1 block">
                    Role & Specialization
                  </label>
                  <input
                    type="text"
                    value={generatedAgent.role || ""}
                    onChange={(e) =>
                      setGeneratedAgent({ ...generatedAgent, role: e.target.value })
                    }
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none focus:border-linear-focus"
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="text-[10px] font-medium text-ink-subtle mb-1 block">
                  Description
                </label>
                <input
                  type="text"
                  value={generatedAgent.description || ""}
                  onChange={(e) =>
                    setGeneratedAgent({ ...generatedAgent, description: e.target.value })
                  }
                  className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none focus:border-linear-focus"
                />
              </div>

              {/* Model & Temperature */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-medium text-ink-subtle mb-1 block flex items-center gap-1">
                    <Cpu size={10} className="text-linear-primary" /> Model
                  </label>
                  <select
                    value={generatedAgent.model || "qwen-3.8"}
                    onChange={(e) =>
                      setGeneratedAgent({ ...generatedAgent, model: e.target.value })
                    }
                    className="w-full text-xs bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-none"
                  >
                    <option value="qwen-3.8">Qwen 3.8 (Groq Default)</option>
                    <option value="llama-3.3-70b-versatile">Llama 3.3 70B (Groq)</option>
                    <option value="sonar">Perplexity Sonar (Live Web)</option>
                    <option value="sonar-pro">Perplexity Sonar Pro</option>
                    <option value="gemini-3.8-flash">Gemini 3.8 Flash</option>
                    <option value="gemini-4-argon">Gemini 4 Argon</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-medium text-ink-subtle mb-1 block">
                    Temperature ({generatedAgent.temperature ?? 0.3})
                  </label>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={generatedAgent.temperature ?? 0.3}
                    onChange={(e) =>
                      setGeneratedAgent({
                        ...generatedAgent,
                        temperature: parseFloat(e.target.value),
                      })
                    }
                    className="w-full accent-linear-primary cursor-pointer mt-1"
                  />
                </div>
              </div>

              {/* Generated System Instructions */}
              <div>
                <label className="text-[10px] font-medium text-ink-subtle mb-1 block flex items-center gap-1">
                  <Terminal size={11} className="text-linear-primary" /> Generated System Instructions Prompt
                </label>
                <textarea
                  rows={6}
                  value={generatedAgent.system_prompt || ""}
                  onChange={(e) =>
                    setGeneratedAgent({
                      ...generatedAgent,
                      system_prompt: e.target.value,
                    })
                  }
                  className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md p-2.5 text-ink focus:outline-none leading-relaxed resize-y"
                />
              </div>

              {/* Save Footer */}
              <div className="pt-2 border-t border-hairline flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={handleSaveToRoster}
                  disabled={isSaving}
                  className="px-4 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors shadow-card flex items-center gap-1.5 disabled:opacity-50"
                >
                  {isSaving ? (
                    <>
                      <span className="w-3 h-3 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                      <span>Saving to Roster...</span>
                    </>
                  ) : (
                    <>
                      <Save size={12} />
                      <span>Save Agent to Roster</span>
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
