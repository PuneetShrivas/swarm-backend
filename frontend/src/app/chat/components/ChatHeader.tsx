'use client';

import { Agent } from '../types';
import { Download, Trash2, Bot, Zap } from 'lucide-react';

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
}: ChatHeaderProps) {
  const currentAgent = agents.find((a) => a.id === selectedAgentId);

  return (
    <header className="h-16 border-b border-slate-200/80 bg-white/80 backdrop-blur-md px-4 md:px-8 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Swarm / Session Title */}
      <div className="flex items-center gap-3 truncate max-w-sm sm:max-w-md">
        <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shadow-xs shrink-0">
          <Bot size={18} />
        </div>

        <div className="truncate">
          <div className="flex items-center gap-2 truncate">
            <span className="font-semibold text-slate-800 text-sm truncate">
              {sessionTitle || (currentAgent ? currentAgent.name : 'Autonomous Agent Swarm')}
            </span>
            <span className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/60 shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              {agents.length > 0 ? `${agents.length} Online` : 'Ready'}
            </span>
          </div>

          <div className="text-[11px] text-slate-400 truncate">
            {currentAgent ? `${currentAgent.name} · ${currentAgent.role}` : 'Distributed multi-agent routing with Supabase history'}
          </div>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Token Usage Badge */}
        {totalTokensUsed !== undefined && onOpenUsage && (
          <button
            type="button"
            onClick={onOpenUsage}
            className="flex items-center gap-1 px-2.5 py-1.5 bg-amber-50 hover:bg-amber-100/70 border border-amber-200/70 text-amber-800 rounded-lg text-xs font-medium transition"
            title="View token telemetry & usage data"
          >
            <Zap size={13} className="text-amber-600" />
            <span className="font-mono">{totalTokensUsed.toLocaleString()}</span>
            <span className="text-[10px] text-amber-600 hidden sm:inline">tks</span>
          </button>
        )}

        {/* Agent Selector */}
        {agents.length > 0 && (
          <div className="hidden sm:flex items-center gap-1.5">
            <label htmlFor="agent-select" className="text-xs text-slate-500">
              Target:
            </label>
            <select
              id="agent-select"
              value={selectedAgentId || ''}
              onChange={(e) => onSelectAgent(e.target.value || null)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">Swarm Orchestrator (Auto)</option>
              {agents.map((ag) => (
                <option key={ag.id} value={ag.id}>
                  {ag.name} ({ag.role})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Export Button */}
        <button
          type="button"
          onClick={onExportChat}
          disabled={activePathCount <= 1}
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1 text-xs"
          title="Export conversation as Markdown"
          aria-label="Export conversation"
        >
          <Download size={15} />
          <span className="hidden md:inline font-medium">Export</span>
        </button>

        {/* Clear Chat Button */}
        <button
          type="button"
          onClick={onClearChat}
          disabled={activePathCount <= 1}
          className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1 text-xs"
          title="Clear current conversation"
          aria-label="Clear chat"
        >
          <Trash2 size={15} />
          <span className="hidden md:inline font-medium">Clear</span>
        </button>
      </div>
    </header>
  );
}
