"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Plus,
  MessageSquare,
  Trash2,
  Edit2,
  Check,
  X,
  LogOut,
  LogIn,
  Zap,
  Bot,
  ChevronDown,
  ChevronUp,
  Sparkles,
  ArrowLeft,
  Loader2,
  Info,
  Layers,
  Search,
  Code2,
  ShieldCheck,
  BarChart2,
  FileText,
} from "lucide-react";
import { ChatSession, Agent } from "../types";

interface SessionSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  onRenameSession: (sessionId: string, newTitle: string) => void;
  userEmail: string | null;
  onSignOut: () => void;
  onOpenUsage: () => void;
  totalTokensUsed: number;
  agents: Agent[];
  selectedAgentId: string | null;
  onSelectAgent: (agentId: string | null) => void;
  isLoadingSessions: boolean;
  onInspectAgent?: (agent: Agent) => void;
}

export default function SessionSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onRenameSession,
  userEmail,
  onSignOut,
  onOpenUsage,
  totalTokensUsed,
  agents,
  selectedAgentId,
  onSelectAgent,
  isLoadingSessions,
  onInspectAgent,
}: SessionSidebarProps) {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [isSwarmExpanded, setIsSwarmExpanded] = useState(true);

  const startEditing = (s: ChatSession, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(s.id);
    setEditTitle(s.title);
  };

  const saveEditing = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      onRenameSession(sessionId, editTitle.trim());
    }
    setEditingSessionId(null);
  };

  const cancelEditing = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(null);
  };

  const handleDelete = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm("Delete this conversation session?")) {
      onDeleteSession(sessionId);
    }
  };

  const getAgentIcon = (id: string, isOrchestrator?: boolean) => {
    if (isOrchestrator || id === "orchestrator") return <Layers className="w-3.5 h-3.5 text-primary" />;
    switch (id) {
      case "researcher":
        return <Search className="w-3.5 h-3.5 text-blue-500" />;
      case "coder":
        return <Code2 className="w-3.5 h-3.5 text-emerald-500" />;
      case "reviewer":
        return <ShieldCheck className="w-3.5 h-3.5 text-amber-500" />;
      case "data_analyst":
        return <BarChart2 className="w-3.5 h-3.5 text-violet-500" />;
      case "synthesizer":
        return <FileText className="w-3.5 h-3.5 text-cyan-500" />;
      default:
        return <Bot className="w-3.5 h-3.5 text-muted-foreground" />;
    }
  };

  // Sort: Orchestrator pinned first, then alphabetical specialists
  const sortedAgents = [...agents].sort((a, b) => {
    const aIsOrch = a.is_orchestrator || a.id === "orchestrator";
    const bIsOrch = b.is_orchestrator || b.id === "orchestrator";
    if (aIsOrch) return -1;
    if (bIsOrch) return 1;
    return a.name.localeCompare(b.name);
  });

  return (
    <aside className="w-72 bg-card border-r border-border/80 flex flex-col h-full shadow-subtle z-10 hidden md:flex select-none transition-colors duration-200">
      {/* Top Header / App Brand */}
      <div className="p-4 border-b border-border/60 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/25 flex items-center justify-center text-primary shadow-subtle group-hover:scale-105 transition-transform">
            <Bot size={18} />
          </div>
          <div>
            <h2 className="text-sm font-semibold tracking-tight text-foreground flex items-center gap-1.5">
              Agent Swarm
              <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-primary/15 text-primary">v2.0</span>
            </h2>
            <div className="text-[10px] text-muted-foreground">Modular Multi-Agent System</div>
          </div>
        </Link>

        {/* Quick New Chat Button */}
        <button
          type="button"
          onClick={onCreateSession}
          className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent/80 rounded-lg transition-all border border-border/60 shadow-subtle"
          title="Start a new chat"
        >
          <Plus size={15} />
        </button>
      </div>

      {/* Action Button: + New Chat */}
      <div className="p-3 pb-1.5">
        <button
          type="button"
          onClick={onCreateSession}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-primary text-primary-foreground hover:opacity-90 rounded-xl text-xs font-semibold shadow-sm transition-all"
        >
          <Plus size={15} />
          <span>New Chat</span>
        </button>
      </div>

      {/* Workflows Studio Navigation Link */}
      <div className="px-3 pb-2">
        <Link
          href="/workflows"
          className="w-full flex items-center justify-between py-2 px-3 bg-card border border-border/80 hover:border-primary/40 hover:bg-muted text-foreground rounded-xl text-xs font-semibold shadow-subtle transition-all group"
        >
          <div className="flex items-center gap-2">
            <Layers size={14} className="text-primary group-hover:scale-110 transition-transform" />
            <span>Workflows Studio</span>
          </div>
          <span className="text-[10px] text-muted-foreground group-hover:text-primary transition-colors">→</span>
        </Link>
      </div>

      {/* Chat Sessions History */}
      <div className="flex-1 overflow-y-auto px-3 py-1 space-y-1 min-h-[140px]">
        <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-2 py-1 flex items-center justify-between">
          <span>Conversations</span>
          {isLoadingSessions && <Loader2 size={11} className="animate-spin text-muted-foreground" />}
        </div>

        {sessions.length === 0 ? (
          <div className="p-4 text-center text-muted-foreground text-xs leading-relaxed">
            {userEmail ? "No conversation history yet." : "Sign in to persist your chats."}
          </div>
        ) : (
          sessions.map((s) => {
            const isActive = activeSessionId === s.id;
            const isEditing = editingSessionId === s.id;

            return (
              <div
                key={s.id}
                onClick={() => !isEditing && onSelectSession(s.id)}
                className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs transition-all cursor-pointer ${
                  isActive
                    ? "bg-primary/15 text-primary font-medium border border-primary/30 shadow-subtle"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/60 border border-transparent"
                }`}
              >
                <div className="flex items-center gap-2 truncate flex-1 min-w-0">
                  <MessageSquare
                    size={14}
                    className={isActive ? "text-primary shrink-0" : "text-muted-foreground shrink-0"}
                  />
                  {isEditing ? (
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="bg-background border border-primary/60 rounded px-1.5 py-0.5 text-xs text-foreground w-full focus:outline-none ring-1 ring-primary/40"
                      autoFocus
                    />
                  ) : (
                    <span className="truncate">{s.title}</span>
                  )}
                </div>

                {/* Edit & Delete Action Buttons */}
                <div className="flex items-center gap-1 shrink-0 ml-1">
                  {isEditing ? (
                    <>
                      <button
                        type="button"
                        onClick={(e) => saveEditing(s.id, e)}
                        className="p-1 text-emerald-500 hover:bg-emerald-500/10 rounded transition"
                        title="Save title"
                      >
                        <Check size={13} />
                      </button>
                      <button
                        type="button"
                        onClick={cancelEditing}
                        className="p-1 text-muted-foreground hover:bg-accent rounded transition"
                        title="Cancel"
                      >
                        <X size={13} />
                      </button>
                    </>
                  ) : (
                    <div className="opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition-opacity">
                      <button
                        type="button"
                        onClick={(e) => startEditing(s, e)}
                        className="p-1 text-muted-foreground hover:text-foreground hover:bg-accent rounded transition"
                        title="Rename"
                      >
                        <Edit2 size={12} />
                      </button>
                      <button
                        type="button"
                        onClick={(e) => handleDelete(s.id, e)}
                        className="p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded transition"
                        title="Delete"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Swarm Roster Section (Pinning Orchestrator + Specialized Agents) */}
      <div className="border-t border-border/60 px-3 py-2">
        <button
          type="button"
          onClick={() => setIsSwarmExpanded(!isSwarmExpanded)}
          className="w-full flex items-center justify-between text-[11px] font-semibold text-muted-foreground uppercase tracking-wider py-1.5 px-2 hover:bg-accent/60 rounded-lg transition"
        >
          <span className="flex items-center gap-1.5">
            <Sparkles size={12} className="text-primary" />
            Active Swarm ({agents.length})
          </span>
          {isSwarmExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        {isSwarmExpanded && (
          <div className="mt-1 space-y-1.5 max-h-56 overflow-y-auto pr-1">
            {sortedAgents.map((agent) => {
              const isSelected = selectedAgentId === agent.id;
              const isOrch = agent.is_orchestrator || agent.id === "orchestrator";
              const toolsCount = agent.tools?.length || 0;
              const skillsCount = agent.skills?.length || 0;
              const mcpCount = agent.mcp_servers?.length || 0;

              return (
                <div
                  key={agent.id}
                  onClick={() => onSelectAgent(isSelected ? null : agent.id)}
                  className={`group relative p-2 rounded-xl text-xs cursor-pointer transition-all border ${
                    isSelected
                      ? "bg-primary/15 text-primary border-primary/40 shadow-subtle"
                      : isOrch
                      ? "bg-card border-border/80 hover:border-primary/40 hover:bg-accent/40"
                      : "bg-card/50 border-border/60 hover:bg-accent/60 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-1.5 truncate">
                      {getAgentIcon(agent.id, isOrch)}
                      <span className={`font-semibold text-[11px] truncate ${isOrch ? "text-primary" : "text-foreground"}`}>
                        {agent.name}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      {onInspectAgent && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onInspectAgent(agent);
                          }}
                          className="opacity-0 group-hover:opacity-100 p-0.5 text-muted-foreground hover:text-primary transition-opacity"
                          title={`Inspect ${agent.name} capabilities`}
                        >
                          <Info size={12} />
                        </button>
                      )}
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          agent.status === "active" ? "bg-emerald-500" : "bg-amber-400"
                        }`}
                      />
                    </div>
                  </div>

                  <div className="text-[10px] text-muted-foreground truncate mb-1.5">
                    {agent.role}
                  </div>

                  {/* Capabilities Badges */}
                  <div className="flex items-center gap-1 text-[9px] font-mono">
                    {toolsCount > 0 && (
                      <span className="px-1.5 py-0.2 rounded bg-muted/80 text-muted-foreground border border-border/50">
                        ⚡ {toolsCount} tools
                      </span>
                    )}
                    {skillsCount > 0 && (
                      <span className="px-1.5 py-0.2 rounded bg-muted/80 text-muted-foreground border border-border/50">
                        ✦ {skillsCount} skills
                      </span>
                    )}
                    {mcpCount > 0 && (
                      <span className="px-1.5 py-0.2 rounded bg-muted/80 text-muted-foreground border border-border/50">
                        🔌 {mcpCount} mcp
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Bottom User Profile & Telemetry Card */}
      <div className="p-3 border-t border-border/60 bg-muted/30">
        {userEmail ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 truncate">
                <div className="w-7 h-7 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs shrink-0 shadow-subtle">
                  {userEmail[0].toUpperCase()}
                </div>
                <div className="truncate">
                  <div className="text-xs font-medium text-foreground truncate">
                    {userEmail}
                  </div>
                  <div className="text-[10px] text-emerald-500 flex items-center gap-1 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    Supabase Auth
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={onSignOut}
                className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition"
                title="Sign Out"
              >
                <LogOut size={15} />
              </button>
            </div>

            {/* Token Usage Quick Trigger */}
            <button
              type="button"
              onClick={onOpenUsage}
              className="w-full flex items-center justify-between px-2.5 py-1.5 bg-card border border-border/80 rounded-lg text-foreground text-xs hover:border-amber-500/50 hover:bg-amber-500/10 transition-all shadow-subtle"
            >
              <div className="flex items-center gap-1.5 text-amber-500 font-medium text-[11px]">
                <Zap size={13} />
                <span>Usage Data</span>
              </div>
              <span className="font-mono text-[11px] font-semibold text-foreground">
                {totalTokensUsed.toLocaleString()} tks
              </span>
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground block">Guest Session</span>
              History is stored in local memory.
            </div>
            <Link
              href="/login"
              className="w-full flex items-center justify-center gap-1.5 py-1.5 bg-primary text-primary-foreground hover:opacity-90 rounded-lg text-xs font-medium transition shadow-subtle"
            >
              <LogIn size={13} />
              <span>Sign in to save chats</span>
            </Link>
          </div>
        )}

        <Link
          href="/"
          className="mt-3 flex items-center justify-center text-[11px] font-medium text-muted-foreground hover:text-foreground transition"
        >
          <ArrowLeft size={12} className="mr-1.5" />
          Back to Overview
        </Link>
      </div>
    </aside>
  );
}
