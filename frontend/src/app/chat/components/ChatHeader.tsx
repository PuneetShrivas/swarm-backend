"use client";

import { Agent } from "../types";
import { Download, Trash2, Bot, Layers, Info, Workflow, Cpu } from "lucide-react";

interface ChatHeaderProps {
  agents: Agent[];
  selectedAgentId: string | null;
  onSelectAgent: (agentId: string | null) => void;
  selectedModel?: string;
  onSelectModel?: (model: string) => void;
  onClearChat: () => void;
  onExportChat: () => void;
  activePathCount: number;
  sessionTitle?: string;
  totalTokensUsed?: number;
  onOpenUsage?: () => void;
  onInspectAgent?: (agent: Agent) => void;
  onOpenWorkflowPicker?: () => void;
}

export default function ChatHeader({
  agents,
  selectedAgentId,
  onSelectAgent,
  selectedModel = "",
  onSelectModel,
  onClearChat,
  onExportChat,
  activePathCount,
  sessionTitle,
  onInspectAgent,
  onOpenWorkflowPicker,
}: ChatHeaderProps) {
  const currentAgent = agents.find((a) => a.id === selectedAgentId);
  const specialists = agents.filter((a) => !a.is_orchestrator && a.id !== "orchestrator");

  return (
    <header className="h-12 border-b border-hairline bg-canvas/80 backdrop-blur-md px-4 md:px-6 flex items-center justify-between sticky top-0 z-20 font-sans">
      {/* Left: Swarm / Session Title */}
      <div className="flex items-center gap-2.5 truncate max-w-sm sm:max-w-md">
        <div className="w-6 h-6 rounded-md bg-surface-1 border border-hairline flex items-center justify-center text-linear-primary shrink-0">
          {currentAgent?.is_orchestrator || !currentAgent ? (
            <Layers size={13} />
          ) : (
            <Bot size={13} />
          )}
        </div>

        <div className="truncate">
          <div className="flex items-center gap-2 truncate">
            <span className="font-medium text-ink text-xs tracking-tight truncate">
              {sessionTitle || (currentAgent ? currentAgent.name : "Autonomous Swarm Session")}
            </span>

            {/* Status & Inspect Trigger */}
            <button
              type="button"
              onClick={() => currentAgent && onInspectAgent && onInspectAgent(currentAgent)}
              disabled={!currentAgent}
              className={`hidden sm:inline-flex items-center gap-1 px-1.5 py-0.2 rounded-pill text-[10px] font-mono transition-colors border ${
                currentAgent
                  ? "bg-surface-2 text-ink border-hairline hover:border-hairline-strong cursor-pointer"
                  : "bg-surface-2 text-semantic-success border-hairline"
              }`}
              title={currentAgent ? "View agent capabilities & tools" : "All swarm agents ready"}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-semantic-success" />
              {currentAgent ? (
                <>
                  <span>{currentAgent.name}</span>
                  <Info size={9} className="ml-0.5 opacity-60" />
                </>
              ) : (
                <span>{agents.length > 0 ? `${agents.length} Online` : "Ready"}</span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-1.5">
        {/* Quick Workflow Picker Trigger */}
        {onOpenWorkflowPicker && (
          <button
            type="button"
            onClick={onOpenWorkflowPicker}
            className="hidden sm:flex items-center gap-1 px-2 py-1 text-ink-subtle hover:text-ink bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong rounded-md text-xs transition-colors"
            title="Invoke Autonomous Workflow"
          >
            <Workflow size={12} className="text-linear-primary" />
            <span className="font-medium text-[11px]">Run Workflow</span>
          </button>
        )}

        {/* Grouped Agent Selector */}
        {agents.length > 0 && (
          <div className="flex items-center">
            <select
              id="agent-select"
              aria-label="Target Agent Selector"
              value={selectedAgentId || ""}
              onChange={(e) => onSelectAgent(e.target.value || null)}
              className="text-[11px] bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong rounded-md px-2 py-1 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus transition-colors cursor-pointer font-medium max-w-[140px] sm:max-w-[170px] truncate"
            >
              <option value="">Auto Routing (Orchestrator)</option>
              {specialists.length > 0 && (
                <optgroup label="Specialized Agents">
                  {specialists.map((ag) => (
                    <option key={ag.id} value={ag.id}>
                      {ag.name}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
        )}

        {/* Model Selector */}
        {onSelectModel && (
          <div className="hidden sm:flex items-center gap-1 bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong rounded-md px-2 py-0.5 transition-colors">
            <Cpu size={11} className="text-linear-primary shrink-0" />
            <select
              id="model-select"
              aria-label="Agent Model Override"
              value={selectedModel}
              onChange={(e) => onSelectModel(e.target.value)}
              className="text-[11px] bg-transparent text-ink focus:outline-none cursor-pointer font-medium max-w-[130px] truncate"
              title="Select LLM model for agent execution"
            >
              <option value="" className="bg-surface-1 text-ink">Default Model</option>
              <option value="gemini-2.5-flash" className="bg-surface-1 text-ink">Gemini 2.5 Flash</option>
              <option value="gemini-2.5-pro" className="bg-surface-1 text-ink">Gemini 2.5 Pro</option>
              <option value="sonar" className="bg-surface-1 text-ink">Perplexity Sonar</option>
              <option value="sonar-pro" className="bg-surface-1 text-ink">Perplexity Sonar Pro</option>
            </select>
          </div>
        )}

        {/* Export Button */}
        <button
          type="button"
          onClick={onExportChat}
          disabled={activePathCount <= 1}
          className="p-1.5 text-ink-subtle hover:text-ink bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong rounded-md transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1 text-xs"
          title="Export conversation as Markdown"
          aria-label="Export conversation"
        >
          <Download size={13} />
        </button>

        {/* Clear Chat Button */}
        <button
          type="button"
          onClick={onClearChat}
          disabled={activePathCount <= 1}
          className="p-1.5 text-ink-subtle hover:text-red-400 bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong rounded-md transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1 text-xs"
          title="Clear current conversation"
          aria-label="Clear chat"
        >
          <Trash2 size={13} />
        </button>
      </div>
    </header>
  );
}
