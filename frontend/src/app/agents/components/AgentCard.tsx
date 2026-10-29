"use client";

import React from "react";
import Link from "next/link";
import {
  Bot,
  Search,
  Code2,
  ShieldCheck,
  BarChart2,
  FileText,
  Sparkles,
  Zap,
  Server,
  Play,
  MessageSquare,
  Edit3,
  Trash2,
  Cpu,
  Layers,
  Thermometer,
  Info,
} from "lucide-react";

export interface AgentCardData {
  id: string;
  name: string;
  role?: string;
  description?: string;
  system_prompt?: string;
  model?: string;
  temperature?: number;
  icon?: string;
  is_orchestrator?: boolean;
  is_custom?: boolean;
  tools?: Array<Record<string, unknown>>;
  skills?: Array<Record<string, unknown>>;
  mcp_servers?: Array<Record<string, unknown>>;
  created_at?: string;
  updated_at?: string;
}

interface AgentCardProps {
  agent: AgentCardData;
  onTest: (agent: AgentCardData) => void;
  onEdit?: (agent: AgentCardData) => void;
  onDelete?: (agentId: string) => void;
  onInspect?: (agent: AgentCardData) => void;
}

export default function AgentCard({
  agent,
  onTest,
  onEdit,
  onDelete,
  onInspect,
}: AgentCardProps) {
  const isCustom = Boolean(agent.is_custom || agent.id.startsWith("agent-"));
  const isOrchestrator = Boolean(agent.is_orchestrator || agent.id === "orchestrator");

  const getAgentAvatar = () => {
    const iconName = (agent.icon || "").toLowerCase();
    const id = agent.id.toLowerCase();

    if (isOrchestrator || iconName === "layers") {
      return <Layers size={14} className="text-linear-primary" />;
    }
    if (id === "researcher" || iconName === "search") {
      return <Search size={14} className="text-blue-400" />;
    }
    if (id === "coder" || iconName === "code2" || iconName === "terminal") {
      return <Code2 size={14} className="text-emerald-400" />;
    }
    if (id === "reviewer" || iconName === "shieldcheck") {
      return <ShieldCheck size={14} className="text-amber-400" />;
    }
    if (id === "data_analyst" || iconName === "barchart2") {
      return <BarChart2 size={14} className="text-purple-400" />;
    }
    if (id === "synthesizer" || iconName === "filetext") {
      return <FileText size={14} className="text-cyan-400" />;
    }
    if (iconName === "sparkles") {
      return <Sparkles size={14} className="text-linear-primary" />;
    }
    return <Bot size={14} className="text-linear-primary" />;
  };

  const getModelLabel = () => {
    const m = agent.model || "gemini-3.8-flash";
    if (m === "gemini-3.8-flash" || m === "gemini-2.5-flash") return "Gemini 3.8 Flash";
    if (m === "gemini-4-argon" || m === "gemini-2.5-pro") return "Gemini 4 Argon";
    if (m === "sonar") return "Sonar (Live Web)";
    if (m === "sonar-pro") return "Sonar Pro";
    return m;
  };

  return (
    <div className="p-4 rounded-lg bg-surface-1 border border-hairline hover:border-hairline-strong transition-all shadow-card flex flex-col justify-between font-sans group select-none">
      {/* Top Header */}
      <div>
        <div className="flex items-start justify-between gap-2 mb-2 pb-2 border-b border-hairline">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-md bg-surface-2 border border-hairline flex items-center justify-center shrink-0">
              {getAgentAvatar()}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <h3 className="text-xs font-semibold text-ink truncate tracking-card-title">
                  {agent.name}
                </h3>
              </div>
              <p className="text-[10px] text-ink-subtle truncate">
                {agent.role || "Swarm Specialist"}
              </p>
            </div>
          </div>

          {/* Badges: Core vs Custom & Online Status */}
          <div className="flex items-center gap-1 shrink-0">
            {isCustom ? (
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-xs bg-linear-primary/10 border border-linear-primary/30 text-linear-primary font-medium">
                CUSTOM
              </span>
            ) : (
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-xs bg-surface-2 border border-hairline text-ink-subtle">
                SWARM CORE
              </span>
            )}
          </div>
        </div>

        {/* Description */}
        <p className="text-xs text-ink-subtle line-clamp-2 leading-relaxed mb-3 tracking-body min-h-[32px]">
          {agent.description || "Autonomous agent specialized for swarm workflows."}
        </p>

        {/* Model & Temperature Pill */}
        <div className="flex flex-wrap items-center gap-1.5 mb-3 text-[10px] font-mono text-ink-tertiary">
          <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-xs bg-surface-2 border border-hairline text-ink-muted">
            <Cpu size={10} className="text-linear-primary" /> {getModelLabel()}
          </span>
          {agent.temperature !== undefined && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-xs bg-surface-2 border border-hairline text-ink-muted">
              <Thermometer size={10} /> {agent.temperature}
            </span>
          )}
        </div>
      </div>

      {/* Capabilities & Actions Footer */}
      <div className="pt-2 border-t border-hairline space-y-2.5">
        {/* Capability Counters */}
        <div className="flex items-center justify-between text-[10px] font-mono text-ink-tertiary">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1">
              <Zap size={10} className="text-amber-400" /> {agent.tools?.length || 0} tools
            </span>
            <span className="flex items-center gap-1">
              <Sparkles size={10} className="text-linear-primary" /> {agent.skills?.length || 0} skills
            </span>
            {agent.mcp_servers && agent.mcp_servers.length > 0 && (
              <span className="flex items-center gap-1">
                <Server size={10} /> {agent.mcp_servers.length} mcp
              </span>
            )}
          </div>

          {onInspect && (
            <button
              type="button"
              onClick={() => onInspect(agent)}
              className="text-ink-subtle hover:text-ink transition-colors flex items-center gap-0.5"
              title="Inspect agent capabilities & instructions"
            >
              <Info size={11} />
              <span>Details</span>
            </button>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between gap-1.5 pt-1">
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => onTest(agent)}
              className="px-2.5 py-1 text-xs font-medium text-ink bg-surface-2 hover:bg-surface-3 border border-hairline hover:border-hairline-strong rounded-md transition-colors flex items-center gap-1"
              title="Launch isolated agent testing playground"
            >
              <Play size={10} className="fill-current text-semantic-success" />
              <span>Test</span>
            </button>

            <Link
              href={`/chat?agent=${agent.id}`}
              className="px-2.5 py-1 text-xs font-medium text-ink-subtle hover:text-ink bg-surface-1 hover:bg-surface-2 border border-hairline rounded-md transition-colors flex items-center gap-1"
              title="Start a new chat session with this agent"
            >
              <MessageSquare size={11} className="text-linear-primary" />
              <span>Chat</span>
            </Link>
          </div>

          {isCustom && (
            <div className="flex items-center gap-1">
              {onEdit && (
                <button
                  type="button"
                  onClick={() => onEdit(agent)}
                  className="p-1 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors border border-hairline"
                  title="Edit custom agent profile"
                >
                  <Edit3 size={11} />
                </button>
              )}
              {onDelete && (
                <button
                  type="button"
                  onClick={() => onDelete(agent.id)}
                  className="p-1 rounded-md text-ink-subtle hover:text-red-400 hover:bg-surface-2 transition-colors border border-hairline"
                  title="Delete custom agent"
                >
                  <Trash2 size={11} />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
