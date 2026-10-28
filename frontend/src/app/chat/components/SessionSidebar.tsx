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
}: SessionSidebarProps) {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [isSwarmExpanded, setIsSwarmExpanded] = useState(false);

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

  return (
    <aside className="w-72 bg-card border-r border-border/80 flex flex-col h-full shadow-subtle z-10 hidden md:flex select-none transition-colors duration-200">
      {/* Top Header / App Brand */}
      <div className="p-4 border-b border-border/60 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/25 flex items-center justify-center text-primary shadow-subtle group-hover:scale-105 transition-transform">
            <Bot size={18} />
          </div>
          <div>
            <h2 className="text-sm font-semibold tracking-tight text-foreground">
              Agent Swarm
            </h2>
            <div className="text-[10px] text-muted-foreground">Conversations & Roster</div>
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
      <div className="p-3">
        <button
          type="button"
          onClick={onCreateSession}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-primary text-primary-foreground hover:opacity-90 rounded-xl text-xs font-semibold shadow-sm transition-all"
        >
          <Plus size={15} />
          <span>New Chat</span>
        </button>
      </div>

      {/* Chat Sessions History */}
      <div className="flex-1 overflow-y-auto px-3 py-1 space-y-1">
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

      {/* Collapsible Swarm Roster Section */}
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
          <div className="mt-1 space-y-1 max-h-36 overflow-y-auto">
            {agents.map((agent) => {
              const isSelected = selectedAgentId === agent.id;
              return (
                <div
                  key={agent.id}
                  onClick={() => onSelectAgent(isSelected ? null : agent.id)}
                  className={`p-2 rounded-lg text-xs cursor-pointer transition-all ${
                    isSelected
                      ? "bg-primary/15 text-primary border border-primary/30"
                      : "hover:bg-accent/60 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-[11px] text-foreground">{agent.name}</span>
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        agent.status === "active" ? "bg-emerald-500" : "bg-amber-400"
                      }`}
                    />
                  </div>
                  <div className="text-[10px] text-muted-foreground truncate">{agent.role}</div>
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
