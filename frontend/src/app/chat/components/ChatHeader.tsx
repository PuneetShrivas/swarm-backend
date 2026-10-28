"use client";

import { Agent } from "../types";
import { Download, Trash2, Bot, Zap, Info, Layers } from "lucide-react";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";

interface ChatHeaderProps {
  agents: Agent[];
  selectedAgentId: string | null;
  onSelectAgent: (agentId: string | null) => void;
  onClearChat: () => void;
  onExportChat: () => void;
  activePathCount: number;
  sessionTitle?: string;
  totalTokensUsed?: number;
  onOpenUsage?: () => void;
  onInspectAgent?: (agent: Agent) => void;
}

export default function ChatHeader({
  agents,
  selectedAgentId,
  onSelectAgent,
  onClearChat,
  onExportChat,
  activePathCount,
  sessionTitle,
  totalTokensUsed,
  onOpenUsage,
  onInspectAgent,
}: ChatHeaderProps) {
  const currentAgent = agents.find((a) => a.id === selectedAgentId);
  const specialists = agents.filter((a) => !a.is_orchestrator && a.id !== "orchestrator");

  return (
    <header className="h-16 border-b border-border/80 bg-card/70 backdrop-blur-xl px-4 md:px-6 flex items-center justify-between sticky top-0 z-20 transition-colors duration-200">
      {/* Left: Swarm / Session Title */}
      <div className="flex items-center gap-3 truncate max-w-sm sm:max-w-md">
        <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/25 flex items-center justify-center text-primary shadow-subtle shrink-0">
          {currentAgent?.is_orchestrator || !currentAgent ? (
            <Layers size={18} />
          ) : (
            <Bot size={18} />
          )}
        </div>

        <div className="truncate">
          <div className="flex items-center gap-2 truncate">
            <span className="font-semibold text-foreground text-sm tracking-tight truncate">
              {sessionTitle || (currentAgent ? currentAgent.name : "Autonomous Agent Swarm")}
            </span>

            {/* Status & Inspect Trigger */}
            <button
              type="button"
              onClick={() => currentAgent && onInspectAgent && onInspectAgent(currentAgent)}
              disabled={!currentAgent}
              className={`hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium transition-all ${
                currentAgent
                  ? "bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 cursor-pointer"
                  : "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
              }`}
              title={currentAgent ? "View agent capabilities & tools" : "All swarm agents ready"}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              {currentAgent ? (
                <>
                  <span>{currentAgent.name}</span>
                  <Info size={10} className="ml-0.5 opacity-70" />
                </>
              ) : (
                <span>{agents.length > 0 ? `${agents.length} Online` : "Ready"}</span>
              )}
            </button>
          </div>

          <div className="text-[11px] text-muted-foreground truncate">
            {currentAgent
              ? `${currentAgent.name} · ${currentAgent.role}`
              : "Distributed multi-agent routing with Supabase history"}
          </div>
        </div>
      </div>

      {/* Right: Actions & ThemeSwitcher */}
      <div className="flex items-center gap-2 sm:gap-2.5">
        {/* Token Usage Badge */}
        {totalTokensUsed !== undefined && onOpenUsage && (
          <button
            type="button"
            onClick={onOpenUsage}
            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/25 text-amber-500 rounded-lg text-xs font-medium transition-all shadow-subtle"
            title="View token telemetry & usage data"
          >
            <Zap size={13} className="text-amber-500" />
            <span className="font-mono font-semibold">{totalTokensUsed.toLocaleString()}</span>
            <span className="text-[10px] text-amber-500/80 hidden sm:inline">tks</span>
          </button>
        )}

        {/* Grouped Agent Selector */}
        {agents.length > 0 && (
          <div className="hidden sm:flex items-center gap-1.5">
            <label htmlFor="agent-select" className="text-xs text-muted-foreground">
              Target:
            </label>
            <select
              id="agent-select"
              value={selectedAgentId || ""}
              onChange={(e) => onSelectAgent(e.target.value || null)}
              className="text-xs bg-muted/60 hover:bg-muted border border-border/80 rounded-lg px-2.5 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary transition-all cursor-pointer font-medium"
            >
              <option value="">Swarm Orchestrator (Auto Routing)</option>
              {specialists.length > 0 && (
                <optgroup label="Specialized Agents">
                  {specialists.map((ag) => (
                    <option key={ag.id} value={ag.id}>
                      {ag.name} ({ag.role.slice(0, 32)}...)
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
        )}

        {/* Theme Switcher */}
        <ThemeSwitcher compact={true} />

        {/* Export Button */}
        <button
          type="button"
          onClick={onExportChat}
          disabled={activePathCount <= 1}
          className="p-1.5 sm:px-2.5 sm:py-1.5 text-muted-foreground hover:text-foreground hover:bg-accent/80 border border-border/60 rounded-lg transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1.5 text-xs shadow-subtle"
          title="Export conversation as Markdown"
          aria-label="Export conversation"
        >
          <Download size={14} />
          <span className="hidden md:inline font-medium">Export</span>
        </button>

        {/* Clear Chat Button */}
        <button
          type="button"
          onClick={onClearChat}
          disabled={activePathCount <= 1}
          className="p-1.5 sm:px-2.5 sm:py-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 border border-border/60 hover:border-destructive/30 rounded-lg transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1.5 text-xs shadow-subtle"
          title="Clear current conversation"
          aria-label="Clear chat"
        >
          <Trash2 size={14} />
          <span className="hidden md:inline font-medium">Clear</span>
        </button>
      </div>
    </header>
  );
}
