'use client';

import { useState } from 'react';
import Link from 'next/link';
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
} from 'lucide-react';
import { ChatSession, Agent } from '../types';

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
  const [editTitle, setEditTitle] = useState('');
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
    if (window.confirm('Delete this conversation session?')) {
      onDeleteSession(sessionId);
    }
  };

  return (
    <aside className="w-72 bg-white border-r border-slate-200 flex flex-col h-full shadow-xs z-10 hidden md:flex select-none">
      {/* Top Header / App Brand */}
      <div className="p-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs">
            <Bot size={18} />
          </div>
          <div>
            <h2 className="text-sm font-bold tracking-tight text-slate-800">
              Agent Swarm
            </h2>
            <div className="text-[10px] text-slate-400">Conversations & Roster</div>
          </div>
        </div>

        {/* Quick New Chat Button */}
        <button
          type="button"
          onClick={onCreateSession}
          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition border border-slate-200"
          title="Start a new chat"
        >
          <Plus size={16} />
        </button>
      </div>

      {/* Action Button: + New Chat */}
      <div className="p-3">
        <button
          type="button"
          onClick={onCreateSession}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-xs transition"
        >
          <Plus size={15} />
          <span>New Chat</span>
        </button>
      </div>

      {/* Chat Sessions History */}
      <div className="flex-1 overflow-y-auto px-3 py-1 space-y-1">
        <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2 py-1 flex items-center justify-between">
          <span>Conversations</span>
          {isLoadingSessions && <Loader2 size={11} className="animate-spin text-slate-400" />}
        </div>

        {sessions.length === 0 ? (
          <div className="p-4 text-center text-slate-400 text-xs">
            {userEmail ? 'No conversation history yet.' : 'Sign in to persist your chats.'}
          </div>
        ) : (
          sessions.map((s) => {
            const isActive = activeSessionId === s.id;
            const isEditing = editingSessionId === s.id;

            return (
              <div
                key={s.id}
                onClick={() => !isEditing && onSelectSession(s.id)}
                className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs transition cursor-pointer ${
                  isActive
                    ? 'bg-blue-50/80 text-blue-900 font-medium border border-blue-200/80'
                    : 'text-slate-700 hover:bg-slate-100/80 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2 truncate flex-1 min-w-0">
                  <MessageSquare
                    size={14}
                    className={isActive ? 'text-blue-600 shrink-0' : 'text-slate-400 shrink-0'}
                  />
                  {isEditing ? (
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="bg-white border border-blue-400 rounded px-1.5 py-0.5 text-xs text-slate-800 w-full focus:outline-none"
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
                        className="p-1 text-emerald-600 hover:bg-emerald-50 rounded"
                        title="Save title"
                      >
                        <Check size={13} />
                      </button>
                      <button
                        type="button"
                        onClick={cancelEditing}
                        className="p-1 text-slate-400 hover:bg-slate-100 rounded"
                        title="Cancel"
                      >
                        <X size={13} />
                      </button>
                    </>
                  ) : (
                    <div className="opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition">
                      <button
                        type="button"
                        onClick={(e) => startEditing(s, e)}
                        className="p-1 text-slate-400 hover:text-slate-700 hover:bg-white rounded"
                        title="Rename"
                      >
                        <Edit2 size={12} />
                      </button>
                      <button
                        type="button"
                        onClick={(e) => handleDelete(s.id, e)}
                        className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded"
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
      <div className="border-t border-slate-100 px-3 py-2">
        <button
          type="button"
          onClick={() => setIsSwarmExpanded(!isSwarmExpanded)}
          className="w-full flex items-center justify-between text-[11px] font-semibold text-slate-500 uppercase tracking-wider py-1.5 px-2 hover:bg-slate-50 rounded-lg transition"
        >
          <span className="flex items-center gap-1.5">
            <Sparkles size={12} className="text-blue-500" />
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
                  className={`p-2 rounded-lg text-xs cursor-pointer transition ${
                    isSelected
                      ? 'bg-blue-50 text-blue-900 border border-blue-200'
                      : 'hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-[11px]">{agent.name}</span>
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        agent.status === 'active' ? 'bg-emerald-500' : 'bg-amber-400'
                      }`}
                    />
                  </div>
                  <div className="text-[10px] text-slate-400 truncate">{agent.role}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Bottom User Profile & Telemetry Card */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/50">
        {userEmail ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 truncate">
                <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs shrink-0">
                  {userEmail[0].toUpperCase()}
                </div>
                <div className="truncate">
                  <div className="text-xs font-medium text-slate-800 truncate">
                    {userEmail}
                  </div>
                  <div className="text-[10px] text-emerald-600 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    Supabase Auth
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={onSignOut}
                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                title="Sign Out"
              >
                <LogOut size={15} />
              </button>
            </div>

            {/* Token Usage Quick Trigger */}
            <button
              type="button"
              onClick={onOpenUsage}
              className="w-full flex items-center justify-between px-2.5 py-1.5 bg-white border border-slate-200/80 rounded-lg text-slate-700 text-xs hover:border-amber-400/80 hover:bg-amber-50/30 transition shadow-2xs"
            >
              <div className="flex items-center gap-1.5 text-amber-600 font-medium text-[11px]">
                <Zap size={13} />
                <span>Usage Data</span>
              </div>
              <span className="font-mono text-[11px] font-semibold text-slate-800">
                {totalTokensUsed.toLocaleString()} tks
              </span>
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-xs text-slate-500">
              <span className="font-medium text-slate-700 block">Guest Mode</span>
              History is stored in local memory.
            </div>
            <Link
              href="/login"
              className="w-full flex items-center justify-center gap-1.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-medium transition"
            >
              <LogIn size={13} />
              <span>Sign in to save chats</span>
            </Link>
          </div>
        )}

        <Link
          href="/"
          className="mt-3 flex items-center justify-center text-[11px] font-medium text-slate-400 hover:text-slate-700 transition"
        >
          <ArrowLeft size={12} className="mr-1.5" />
          Back to Overview
        </Link>
      </div>
    </aside>
  );
}
