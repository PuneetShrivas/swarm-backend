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
  Search,
  Users,
  Workflow,
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
  agents,
  isLoadingSessions,
}: SessionSidebarProps) {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

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

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <aside className="w-64 bg-canvas border-r border-hairline flex flex-col h-full z-10 hidden md:flex select-none font-sans">
      {/* Top Header Actions */}
      <div className="p-3 border-b border-hairline flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={onCreateSession}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 bg-linear-primary hover:bg-linear-hover text-white rounded-md text-xs font-medium transition-colors"
        >
          <Plus size={13} />
          <span>New Chat</span>
        </button>
      </div>

      {/* Instant Search Bar */}
      {sessions.length > 3 && (
        <div className="px-3 pt-2.5 pb-1">
          <div className="relative">
            <Search size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-tertiary" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter sessions..."
              className="w-full text-[11px] bg-surface-1 border border-hairline hover:border-hairline-strong rounded-md pl-7 pr-2 py-1 text-ink placeholder:text-ink-tertiary focus:outline-none focus:ring-1 focus:ring-linear-focus"
            />
          </div>
        </div>
      )}

      {/* Chat Sessions History List */}
      <div className="flex-1 overflow-y-auto px-2.5 py-1.5 space-y-0.5 min-h-[140px]">
        <div className="text-[10px] font-medium text-ink-subtle uppercase tracking-eyebrow px-2 py-1 flex items-center justify-between">
          <span>Conversations ({sessions.length})</span>
          {isLoadingSessions && <Loader2 size={10} className="animate-spin text-ink-subtle" />}
        </div>

        {filteredSessions.length === 0 ? (
          <div className="p-4 text-center text-ink-subtle text-xs leading-relaxed">
            {searchQuery
              ? "No matching sessions."
              : userEmail
              ? "No chats yet. Start a new conversation."
              : "Sign in to persist your chats."}
          </div>
        ) : (
          filteredSessions.map((s) => {
            const isActive = activeSessionId === s.id;
            const isEditing = editingSessionId === s.id;

            return (
              <div
                key={s.id}
                onClick={() => !isEditing && onSelectSession(s.id)}
                className={`group flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition-colors cursor-pointer border ${
                  isActive
                    ? "bg-surface-2 text-ink font-medium border-hairline-strong"
                    : "text-ink-subtle hover:text-ink hover:bg-surface-1 border-transparent"
                }`}
              >
                <div className="flex items-center gap-2 truncate flex-1 min-w-0">
                  <MessageSquare
                    size={12}
                    className={isActive ? "text-linear-primary shrink-0" : "text-ink-tertiary shrink-0"}
                  />
                  {isEditing ? (
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="bg-canvas border border-hairline-strong rounded px-1.5 py-0.5 text-xs text-ink w-full focus:outline-none ring-1 ring-linear-focus font-sans"
                      autoFocus
                    />
                  ) : (
                    <span className="truncate">{s.title}</span>
                  )}
                </div>

                {/* Edit & Delete Action Buttons */}
                <div className="flex items-center gap-0.5 shrink-0 ml-1">
                  {isEditing ? (
                    <>
                      <button
                        type="button"
                        onClick={(e) => saveEditing(s.id, e)}
                        className="p-1 text-semantic-success hover:bg-surface-2 rounded transition"
                        title="Save title"
                      >
                        <Check size={11} />
                      </button>
                      <button
                        type="button"
                        onClick={cancelEditing}
                        className="p-1 text-ink-subtle hover:bg-surface-2 rounded transition"
                        title="Cancel"
                      >
                        <X size={11} />
                      </button>
                    </>
                  ) : (
                    <div className="opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition-opacity">
                      <button
                        type="button"
                        onClick={(e) => startEditing(s, e)}
                        className="p-1 text-ink-subtle hover:text-ink hover:bg-surface-2 rounded transition"
                        title="Rename"
                      >
                        <Edit2 size={10} />
                      </button>
                      <button
                        type="button"
                        onClick={(e) => handleDelete(s.id, e)}
                        className="p-1 text-ink-subtle hover:text-red-400 hover:bg-surface-2 rounded transition"
                        title="Delete"
                      >
                        <Trash2 size={10} />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Sanitized Bottom Rail (Clean Links to Agents Studio & Workflows Studio) */}
      <div className="p-2.5 border-t border-hairline bg-surface-1/40 space-y-1">
        <Link
          href="/agents"
          className="flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs text-ink-subtle hover:text-ink hover:bg-surface-1 transition-colors group"
        >
          <div className="flex items-center gap-2">
            <Users size={12} className="text-linear-primary" />
            <span className="text-[11px] font-medium">{agents.length} Specialists Online</span>
          </div>
          <span className="text-[10px] text-ink-tertiary group-hover:text-ink transition-colors">→</span>
        </Link>

        <Link
          href="/workflows"
          className="flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs text-ink-subtle hover:text-ink hover:bg-surface-1 transition-colors group"
        >
          <div className="flex items-center gap-2">
            <Workflow size={12} className="text-linear-primary" />
            <span className="text-[11px] font-medium">Workflows Studio</span>
          </div>
          <span className="text-[10px] text-ink-tertiary group-hover:text-ink transition-colors">→</span>
        </Link>
      </div>
    </aside>
  );
}
