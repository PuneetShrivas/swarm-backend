"use client";

import React, { useState, useEffect } from "react";
import { getAuthHeaders } from "@/lib/supabase";
import { AgentCardData } from "./AgentCard";
import {
  X,
  Bot,
  Search,
  Code2,
  ShieldCheck,
  BarChart2,
  FileText,
  Sparkles,
  Terminal,
  Cpu,
  Layers,
  Save,
} from "lucide-react";

interface AgentEditorModalProps {
  agent: AgentCardData | null; // null = create new agent
  isOpen: boolean;
  onClose: () => void;
  onSaved: (savedAgent: AgentCardData) => void;
}

const AVAILABLE_ICONS = [
  { name: "Bot", icon: Bot },
  { name: "Layers", icon: Layers },
  { name: "Search", icon: Search },
  { name: "Code2", icon: Code2 },
  { name: "ShieldCheck", icon: ShieldCheck },
  { name: "BarChart2", icon: BarChart2 },
  { name: "FileText", icon: FileText },
  { name: "Sparkles", icon: Sparkles },
  { name: "Terminal", icon: Terminal },
  { name: "Cpu", icon: Cpu },
];

export default function AgentEditorModal({
  agent,
  isOpen,
  onClose,
  onSaved,
}: AgentEditorModalProps) {
  const isEditing = Boolean(agent && agent.id);

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [role, setRole] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [model, setModel] = useState("gemini-3.8-flash");
  const [temperature, setTemperature] = useState(0.3);
  const [icon, setIcon] = useState("Bot");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (agent) {
      setName(agent.name || "");
      setSlug(agent.id || "");
      setRole(agent.role || "");
      setDescription(agent.description || "");
      setSystemPrompt(agent.system_prompt || "");
      const currentModel = agent.model || "gemini-3.8-flash";
      setModel(currentModel === "gemini-2.5-flash" ? "gemini-3.8-flash" : currentModel === "gemini-2.5-pro" ? "gemini-4-argon" : currentModel);
      setTemperature(agent.temperature ?? 0.3);
      setIcon(agent.icon || "Bot");
    } else {
      setName("");
      setSlug("");
      setRole("Domain Specialist");
      setDescription("");
      setSystemPrompt(
        "You are a specialized AI assistant. Provide concise, accurate responses with clear reasoning and actionable recommendations."
      );
      setModel("gemini-3.8-flash");
      setTemperature(0.3);
      setIcon("Bot");
    }
    setErrorMessage(null);
  }, [agent, isOpen]);

  // Auto-generate slug from name if creating
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setName(val);
    if (!isEditing) {
      const generatedSlug = `agent-${val
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "")
        .slice(0, 24)}`;
      setSlug(generatedSlug);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setErrorMessage("Agent display name is required.");
      return;
    }
    if (!systemPrompt.trim()) {
      setErrorMessage("System instructions prompt is required.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const authHeaders = await getAuthHeaders();
      const finalSlug = slug.trim() || `agent-${Date.now().toString(36)}`;

      const payload = {
        id: finalSlug,
        name: name.trim(),
        role: role.trim() || "Specialist",
        description: description.trim(),
        system_prompt: systemPrompt.trim(),
        model,
        temperature,
        icon,
        is_public: false,
      };

      const url = isEditing
        ? `${apiUrl}/api/custom-agents/${encodeURIComponent(agent!.id)}`
        : `${apiUrl}/api/custom-agents`;

      const method = isEditing ? "PUT" : "POST";

      const res = await fetch(url, {
        method,
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server responded with status ${res.status}`);
      }

      const saved: AgentCardData = await res.json();
      onSaved(saved);
      onClose();
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "Failed to save agent profile.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-canvas border border-hairline rounded-xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden select-none">
        {/* Modal Header */}
        <div className="h-14 px-5 border-b border-hairline flex items-center justify-between shrink-0 bg-surface-1/50">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md bg-surface-2 border border-hairline text-linear-primary flex items-center justify-center">
              <Bot size={13} />
            </div>
            <div>
              <h3 className="text-xs font-semibold text-ink tracking-tight">
                {isEditing ? `Edit Agent: ${agent?.name}` : "Create Specialized Agent"}
              </h3>
              <p className="text-[10px] text-ink-subtle">
                Configure persona, instructions, reasoning model, and parameters
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors border border-hairline"
            title="Close editor"
          >
            <X size={14} />
          </button>
        </div>

        {/* Modal Form Body */}
        <form onSubmit={handleSave} className="p-5 overflow-y-auto space-y-4 flex-1 text-xs">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono">
              {errorMessage}
            </div>
          )}

          {/* Name & Slug */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-medium text-ink-subtle mb-1 block">
                Agent Display Name <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={handleNameChange}
                placeholder="e.g. Senior Security Auditor"
                className="w-full text-xs bg-surface-1 border border-hairline hover:border-hairline-strong focus:border-linear-focus rounded-md px-3 py-2 text-ink focus:outline-none transition-colors"
              />
            </div>

            <div>
              <label className="text-[11px] font-medium text-ink-subtle mb-1 block">
                Unique Identifier (Slug)
              </label>
              <input
                type="text"
                disabled={isEditing}
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="agent-security-auditor"
                className="w-full text-xs font-mono bg-surface-1 border border-hairline rounded-md px-3 py-2 text-ink-muted focus:outline-none disabled:opacity-60"
              />
            </div>
          </div>

          {/* Role & Icon Picker */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2">
              <label className="text-[11px] font-medium text-ink-subtle mb-1 block">
                Role & Specialization
              </label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="e.g. Vulnerability Detection & Hardening"
                className="w-full text-xs bg-surface-1 border border-hairline hover:border-hairline-strong focus:border-linear-focus rounded-md px-3 py-2 text-ink focus:outline-none transition-colors"
              />
            </div>

            <div>
              <label className="text-[11px] font-medium text-ink-subtle mb-1 block">
                Avatar Icon
              </label>
              <div className="flex flex-wrap gap-1 p-1 bg-surface-1 border border-hairline rounded-md max-h-[38px] overflow-hidden items-center justify-between">
                {AVAILABLE_ICONS.slice(0, 6).map((item) => {
                  const IconComp = item.icon;
                  const isSelected = icon === item.name;
                  return (
                    <button
                      key={item.name}
                      type="button"
                      onClick={() => setIcon(item.name)}
                      className={`p-1 rounded transition-colors ${
                        isSelected
                          ? "bg-linear-primary text-white"
                          : "text-ink-subtle hover:text-ink hover:bg-surface-2"
                      }`}
                      title={item.name}
                    >
                      <IconComp size={13} />
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="text-[11px] font-medium text-ink-subtle mb-1 block">
              Agent Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief summary of what this agent does..."
              className="w-full text-xs bg-surface-1 border border-hairline hover:border-hairline-strong focus:border-linear-focus rounded-md px-3 py-2 text-ink focus:outline-none transition-colors"
            />
          </div>

          {/* Model Selection & Temperature */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 border-t border-hairline">
            <div>
              <label className="text-[11px] font-medium text-ink-subtle mb-1 block flex items-center gap-1">
                <Cpu size={12} className="text-linear-primary" /> Reasoning Model
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full text-xs bg-surface-1 border border-hairline hover:border-hairline-strong rounded-md px-3 py-2 text-ink focus:outline-none focus:border-linear-focus transition-colors cursor-pointer"
              >
                <option value="gemini-3.8-flash">Gemini 3.8 Flash (Ultra Fast)</option>
                <option value="gemini-4-argon">Gemini 4 Argon (Deep Complex Reasoning)</option>
                <option value="sonar">Perplexity Sonar (Real Live Web Search)</option>
                <option value="sonar-pro">Perplexity Sonar Pro (Advanced Synthesis)</option>
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-medium text-ink-subtle">
                  Sampling Temperature
                </label>
                <span className="font-mono text-[10px] text-ink">{temperature}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-linear-primary cursor-pointer mt-1"
              />
              <div className="flex justify-between text-[9px] font-mono text-ink-tertiary">
                <span>Precise (0.0)</span>
                <span>Balanced (0.3)</span>
                <span>Creative (1.0)</span>
              </div>
            </div>
          </div>

          {/* System Prompt Instructions */}
          <div className="space-y-1 pt-1 border-t border-hairline">
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-medium text-ink flex items-center gap-1">
                <Terminal size={12} className="text-linear-primary" /> System Instructions & Persona <span className="text-red-400">*</span>
              </label>
              <span className="text-[10px] font-mono text-ink-tertiary">Markdown & formatting supported</span>
            </div>
            <textarea
              required
              rows={8}
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="Define agent personality, behavior rules, instructions, and domain guidelines..."
              className="w-full text-xs font-mono bg-canvas border border-hairline hover:border-hairline-strong focus:border-linear-focus rounded-md p-3 text-ink focus:outline-none leading-relaxed resize-y"
            />
          </div>

          {/* Action Footer */}
          <div className="pt-3 border-t border-hairline flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-3 py-1.5 text-xs text-ink-subtle hover:text-ink bg-surface-1 hover:bg-surface-2 border border-hairline rounded-md transition-colors"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors shadow-card flex items-center gap-1.5 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <span className="w-3 h-3 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save size={12} />
                  <span>{isEditing ? "Save Changes" : "Create Agent"}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
