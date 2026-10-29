"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
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
  ChevronDown,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
  Activity,
  FolderArchive,
  Clock,
  Zap,
} from "lucide-react";
import { supabase } from "@/lib/supabase";

export interface SidebarSession {
  id: string;
  title: string;
  created_at?: string;
  updated_at?: string;
}

export interface SidebarWorkflow {
  id: string;
  title: string;
  goal?: string;
  steps_count?: number;
}

export interface SidebarWorkflowRun {
  id: string;
  workflow_id: string;
  workflow_title?: string;
  status: "completed" | "failed" | "running" | string;
  duration_ms?: number;
  total_tokens?: number;
  created_at?: string;
}

export interface SidebarAgent {
  id: string;
  name: string;
  model?: string;
  role?: string;
}

export interface SidebarAgentRun {
  agent_id: string;
  model?: string;
  total_tokens?: number;
  latency_ms?: number;
  created_at?: string;
}

interface AppUnifiedSidebarProps {
  activePage: "chat" | "workflows" | "agents" | "artifacts";
  // Chat Session Props
  sessions?: SidebarSession[];
  activeSessionId?: string | null;
  onSelectSession?: (id: string) => void;
  onCreateSession?: () => void;
  onDeleteSession?: (id: string) => void;
  onRenameSession?: (id: string, newTitle: string) => void;
  isLoadingSessions?: boolean;
  // External Action Triggers
  onCreateWorkflow?: () => void;
  onCreateAgent?: () => void;
}

export default function AppUnifiedSidebar({
  activePage,
  sessions: initialSessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onRenameSession,
  isLoadingSessions = false,
  onCreateWorkflow,
  onCreateAgent,
}: AppUnifiedSidebarProps) {
  const router = useRouter();

  // Collapsed state persisted in localStorage
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const [mounted, setMounted] = useState<boolean>(false);

  // Accordion section collapse state (collapsed by default across sections)
  const [openSections, setOpenSections] = useState({
    conversations: false,
    workflows: false,
    agents: false,
  });

  // Local state for sessions, workflows, runs, and agents
  const [sessions, setSessions] = useState<SidebarSession[]>(initialSessions || []);
  const [workflows, setWorkflows] = useState<SidebarWorkflow[]>([]);
  const [workflowRuns, setWorkflowRuns] = useState<SidebarWorkflowRun[]>([]);
  const [agents, setAgents] = useState<SidebarAgent[]>([]);
  const [agentRuns, setAgentRuns] = useState<SidebarAgentRun[]>([]);

  // Search & inline editing
  const [searchQuery, setSearchQuery] = useState("");
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  // Initialize persistence on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("swarm_sidebar_collapsed");
      if (saved !== null) {
        setIsCollapsed(saved === "true");
      }
    } catch {
      // Ignore storage errors
    }
    setMounted(true);
  }, []);

  // Update localStorage when isCollapsed changes
  const toggleCollapse = useCallback(() => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("swarm_sidebar_collapsed", String(next));
      } catch {
        // Ignore storage errors
      }
      return next;
    });
  }, []);

  // Sync initial sessions if prop changes
  useEffect(() => {
    if (initialSessions) {
      setSessions(initialSessions);
    }
  }, [initialSessions]);

  // Fetch workflows, workflow runs, agents, and telemetry
  useEffect(() => {
    const fetchData = async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();
        const headers: Record<string, string> = {};
        if (session?.access_token) {
          headers["Authorization"] = `Bearer ${session.access_token}`;
        }

        // 1. Fetch Workflows
        const wfRes = await fetch(`${apiUrl}/api/workflows`, { headers }).catch(() => null);
        if (wfRes && wfRes.ok) {
          const wfData = await wfRes.json();
          setWorkflows(
            wfData.map((w: Record<string, unknown>) => ({
              id: String(w.id),
              title: String(w.title || "Untitled Workflow"),
              goal: String(w.goal || ""),
              steps_count: Array.isArray(w.steps) ? w.steps.length : 0,
            }))
          );
        }

        // 2. Fetch Workflow Runs
        const runsRes = await fetch(`${apiUrl}/api/workflow-runs`, { headers }).catch(() => null);
        if (runsRes && runsRes.ok) {
          const rData = await runsRes.json();
          setWorkflowRuns(
            rData.map((r: Record<string, unknown>) => ({
              id: String(r.id),
              workflow_id: String(r.workflow_id),
              workflow_title: String(r.workflow_title || "Autonomous Workflow"),
              status: String(r.status || "completed"),
              duration_ms: Number(r.duration_ms || 0),
              total_tokens: Number(r.total_tokens || 0),
              created_at: String(r.created_at || ""),
            }))
          );
        }

        // 3. Fetch Agents
        const agRes = await fetch(`${apiUrl}/api/agents`, { headers }).catch(() => null);
        if (agRes && agRes.ok) {
          const agData = await agRes.json();
          setAgents(
            agData.map((a: Record<string, unknown>) => ({
              id: String(a.id),
              name: String(a.name || a.id),
              model: String(a.model || "gemini-3.8-flash"),
              role: String(a.role || ""),
            }))
          );
        }

        // 4. Fetch Usage / Agent Telemetry
        const usRes = await fetch(`${apiUrl}/api/usage`, { headers }).catch(() => null);
        if (usRes && usRes.ok) {
          const usData = await usRes.json();
          if (usData && Array.isArray(usData.recent_activity)) {
            setAgentRuns(
              usData.recent_activity.map((u: Record<string, unknown>) => ({
                agent_id: String(u.agent_id || "orchestrator"),
                model: String(u.model || "gemini-3.8-flash"),
                total_tokens: Number(u.total_tokens || 0),
                latency_ms: Number(u.latency_ms || 0),
                created_at: String(u.created_at || ""),
              }))
            );
          }
        }
      } catch (err) {
        console.warn("Sidebar data fetch notice:", err);
      }
    };

    fetchData();
  }, []);

  const toggleSection = (section: "conversations" | "workflows" | "agents") => {
    setOpenSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const handleStartRename = (s: SidebarSession, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(s.id);
    setEditTitle(s.title);
  };

  const handleSaveRename = (sId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (editTitle.trim() && onRenameSession) {
      onRenameSession(sId, editTitle.trim());
    }
    setEditingSessionId(null);
  };

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(null);
  };

  const handleDeleteSession = (sId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm("Delete this conversation?")) {
      if (onDeleteSession) {
        onDeleteSession(sId);
      }
    }
  };

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Avoid hydration mismatch on initial render
  if (!mounted) {
    return (
      <aside className="w-64 bg-canvas border-r border-hairline h-full hidden md:flex flex-col select-none font-sans" />
    );
  }

  // COLLAPSED ICON RAIL (w-14)
  if (isCollapsed) {
    return (
      <aside className="w-14 shrink-0 bg-canvas border-r border-hairline flex flex-col items-center py-3 justify-between h-full z-20 hidden md:flex select-none font-sans transition-all duration-200">
        <div className="flex flex-col items-center gap-3 w-full">
          {/* Expand Toggle */}
          <button
            type="button"
            onClick={toggleCollapse}
            title="Expand Sidebar"
            className="p-2 rounded-lg text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors border border-transparent hover:border-hairline"
          >
            <PanelLeftOpen size={16} />
          </button>

          <div className="w-8 h-px bg-hairline my-0.5" />

          {/* Quick Action Button */}
          <button
            type="button"
            onClick={() => {
              if (activePage === "chat" && onCreateSession) {
                onCreateSession();
              } else if (activePage === "workflows" && onCreateWorkflow) {
                onCreateWorkflow();
              } else if (activePage === "agents" && onCreateAgent) {
                onCreateAgent();
              } else {
                router.push("/chat");
              }
            }}
            title={activePage === "workflows" ? "New Workflow" : activePage === "agents" ? "New Agent" : "New Chat"}
            className="p-2.5 rounded-lg bg-linear-primary hover:bg-linear-hover text-white shadow-xs transition-transform hover:scale-105"
          >
            <Plus size={15} />
          </button>

          {/* Icon Navigation Shortcuts */}
          <div className="flex flex-col items-center gap-2 mt-2">
            <Link
              href="/chat"
              title={`Chat Conversations (${sessions.length})`}
              className={`p-2 rounded-lg transition-colors border relative ${
                activePage === "chat"
                  ? "bg-surface-2 text-linear-primary border-hairline-strong shadow-xs"
                  : "text-ink-subtle hover:text-ink hover:bg-surface-1 border-transparent"
              }`}
            >
              <MessageSquare size={16} />
              {sessions.length > 0 && (
                <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-linear-primary" />
              )}
            </Link>

            <Link
              href="/workflows"
              title={`Workflows & Runs (${workflows.length})`}
              className={`p-2 rounded-lg transition-colors border ${
                activePage === "workflows"
                  ? "bg-surface-2 text-linear-primary border-hairline-strong shadow-xs"
                  : "text-ink-subtle hover:text-ink hover:bg-surface-1 border-transparent"
              }`}
            >
              <Workflow size={16} />
            </Link>

            <Link
              href="/agents"
              title={`Specialist Agents (${agents.length})`}
              className={`p-2 rounded-lg transition-colors border ${
                activePage === "agents"
                  ? "bg-surface-2 text-linear-primary border-hairline-strong shadow-xs"
                  : "text-ink-subtle hover:text-ink hover:bg-surface-1 border-transparent"
              }`}
            >
              <Users size={16} />
            </Link>

            <Link
              href="/artifacts"
              title="Artifacts Studio"
              className={`p-2 rounded-lg transition-colors border ${
                activePage === "artifacts"
                  ? "bg-surface-2 text-linear-primary border-hairline-strong shadow-xs"
                  : "text-ink-subtle hover:text-ink hover:bg-surface-1 border-transparent"
              }`}
            >
              <FolderArchive size={16} />
            </Link>
          </div>
        </div>

        {/* Bottom Rail: Active Status Dot */}
        <div className="flex flex-col items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-semantic-success animate-pulse" title="Swarm Engine Online" />
        </div>
      </aside>
    );
  }

  // EXPANDED UNIFIED SIDEBAR (w-64)
  return (
    <aside className="w-64 shrink-0 bg-canvas border-r border-hairline flex flex-col h-full z-20 hidden md:flex select-none font-sans transition-all duration-200">
      {/* Top Header Actions */}
      <div className="p-3 border-b border-hairline flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => {
            if (activePage === "chat" && onCreateSession) {
              onCreateSession();
            } else if (activePage === "workflows" && onCreateWorkflow) {
              onCreateWorkflow();
            } else if (activePage === "agents" && onCreateAgent) {
              onCreateAgent();
            } else {
              router.push("/chat");
            }
          }}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 bg-linear-primary hover:bg-linear-hover text-white rounded-md text-xs font-medium transition-colors shadow-xs"
        >
          <Plus size={13} />
          <span>
            {activePage === "workflows"
              ? "New Workflow"
              : activePage === "agents"
              ? "New Agent"
              : "New Chat"}
          </span>
        </button>

        {/* Collapse Sidebar Button */}
        <button
          type="button"
          onClick={toggleCollapse}
          title="Collapse Sidebar"
          className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-1 transition-colors border border-hairline"
        >
          <PanelLeftClose size={14} />
        </button>
      </div>

      {/* Filter / Search Bar */}
      <div className="px-3 pt-2 pb-1.5">
        <div className="relative">
          <Search size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-tertiary" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations & workflows..."
            className="w-full text-[11px] bg-surface-1 border border-hairline hover:border-hairline-strong rounded-md pl-7 pr-2 py-1 text-ink placeholder:text-ink-tertiary focus:outline-none focus:ring-1 focus:ring-linear-focus"
          />
        </div>
      </div>

      {/* Main Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto px-2 py-1.5 space-y-3">
        {/* ==================================================== */}
        {/* 1. CONVERSATIONS SECTION */}
        {/* ==================================================== */}
        <div>
          <button
            type="button"
            onClick={() => toggleSection("conversations")}
            className="w-full flex items-center justify-between px-2 py-1 text-[10px] font-semibold text-ink-subtle uppercase tracking-eyebrow hover:text-ink transition-colors"
          >
            <div className="flex items-center gap-1.5">
              <MessageSquare size={11} className="text-linear-primary" />
              <span>Conversations ({sessions.length})</span>
            </div>
            {openSections.conversations ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
          </button>

          {openSections.conversations && (
            <div className="mt-1 space-y-0.5">
              {isLoadingSessions && sessions.length === 0 ? (
                <div className="space-y-1.5 px-1 py-1">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="h-7 rounded-md bg-surface-1/80 border border-hairline/60 animate-pulse flex items-center px-2.5 gap-2"
                    >
                      <div className="w-2.5 h-2.5 rounded bg-surface-2 shrink-0" />
                      <div className="h-2 rounded bg-surface-2" style={{ width: `${40 + (i * 15) % 40}%` }} />
                    </div>
                  ))}
                </div>
              ) : filteredSessions.length === 0 ? (
                <div className="px-3 py-2 text-center text-ink-subtle text-[11px] leading-relaxed">
                  {searchQuery ? "No matching chats." : "No saved chats. Start a new prompt."}
                </div>
              ) : (
                filteredSessions.map((s) => {
                  const isActive = activePage === "chat" && activeSessionId === s.id;
                  const isEditing = editingSessionId === s.id;

                  return (
                    <div
                      key={s.id}
                      onClick={() => {
                        if (!isEditing) {
                          if (activePage !== "chat") {
                            router.push(`/chat?session=${s.id}`);
                          } else if (onSelectSession) {
                            onSelectSession(s.id);
                          }
                        }
                      }}
                      className={`group flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition-colors cursor-pointer border ${
                        isActive
                          ? "bg-surface-2 text-ink font-medium border-hairline-strong"
                          : "text-ink-subtle hover:text-ink hover:bg-surface-1 border-transparent"
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate flex-1 min-w-0">
                        <MessageSquare
                          size={11}
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
                          <span className="truncate text-[11.5px]">{s.title}</span>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-0.5 shrink-0 ml-1">
                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={(e) => handleSaveRename(s.id, e)}
                              className="p-1 text-semantic-success hover:bg-surface-2 rounded"
                              title="Save"
                            >
                              <Check size={11} />
                            </button>
                            <button
                              type="button"
                              onClick={handleCancelRename}
                              className="p-1 text-ink-subtle hover:bg-surface-2 rounded"
                              title="Cancel"
                            >
                              <X size={11} />
                            </button>
                          </>
                        ) : (
                          <div className="opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition-opacity">
                            {onRenameSession && (
                              <button
                                type="button"
                                onClick={(e) => handleStartRename(s, e)}
                                className="p-1 text-ink-subtle hover:text-ink hover:bg-surface-2 rounded"
                                title="Rename"
                              >
                                <Edit2 size={10} />
                              </button>
                            )}
                            {onDeleteSession && (
                              <button
                                type="button"
                                onClick={(e) => handleDeleteSession(s.id, e)}
                                className="p-1 text-ink-subtle hover:text-red-400 hover:bg-surface-2 rounded"
                                title="Delete"
                              >
                                <Trash2 size={10} />
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>

        {/* ==================================================== */}
        {/* 2. WORKFLOWS & WORKFLOW RUNS SECTION */}
        {/* ==================================================== */}
        <div className="pt-2 border-t border-hairline">
          <button
            type="button"
            onClick={() => toggleSection("workflows")}
            className="w-full flex items-center justify-between px-2 py-1 text-[10px] font-semibold text-ink-subtle uppercase tracking-eyebrow hover:text-ink transition-colors"
          >
            <div className="flex items-center gap-1.5">
              <Workflow size={11} className="text-linear-primary" />
              <span>Workflows ({workflows.length})</span>
            </div>
            {openSections.workflows ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
          </button>

          {openSections.workflows && (
            <div className="mt-1 space-y-1">
              {/* Workflows List */}
              {workflows.length === 0 ? (
                <div className="px-3 py-1.5 text-center text-ink-subtle text-[11px]">
                  No pipelines yet.
                </div>
              ) : (
                workflows.slice(0, 5).map((w) => (
                  <Link
                    key={w.id}
                    href={`/workflows/${w.id}`}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs text-ink-subtle hover:text-ink hover:bg-surface-1 transition-colors border border-transparent hover:border-hairline group"
                  >
                    <div className="flex items-center gap-2 truncate min-w-0">
                      <span className="w-1.5 h-1.5 rounded-full bg-linear-primary/70 shrink-0" />
                      <span className="truncate text-[11.5px] font-medium">{w.title}</span>
                    </div>
                    <span className="text-[10px] font-mono text-ink-tertiary">
                      {w.steps_count}s
                    </span>
                  </Link>
                ))
              )}

              {/* Grouped Workflow Runs Sub-section */}
              {workflowRuns.length > 0 && (
                <div className="pt-2 mt-1">
                  <div className="px-2 pb-1 text-[9px] uppercase tracking-wider font-mono text-ink-tertiary flex items-center justify-between">
                    <span>Recent Workflow Runs</span>
                    <Clock size={9} />
                  </div>
                  <div className="space-y-0.5">
                    {workflowRuns.slice(0, 4).map((run) => (
                      <div
                        key={run.id}
                        className="px-2.5 py-1 rounded bg-surface-1/60 border border-hairline/80 flex items-center justify-between text-[10.5px]"
                      >
                        <div className="flex items-center gap-1.5 truncate min-w-0">
                          <span
                            className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                              run.status === "completed"
                                ? "bg-semantic-success"
                                : run.status === "failed"
                                ? "bg-red-400"
                                : "bg-amber-400 animate-pulse"
                            }`}
                          />
                          <span className="truncate text-ink font-mono">{run.workflow_title || run.workflow_id.slice(0, 8)}</span>
                        </div>
                        <span className="text-[9.5px] font-mono text-ink-tertiary shrink-0 ml-1">
                          {run.duration_ms ? `${Math.round(run.duration_ms)}ms` : "done"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ==================================================== */}
        {/* 3. AGENTS & AGENT RUNS SECTION */}
        {/* ==================================================== */}
        <div className="pt-2 border-t border-hairline">
          <button
            type="button"
            onClick={() => toggleSection("agents")}
            className="w-full flex items-center justify-between px-2 py-1 text-[10px] font-semibold text-ink-subtle uppercase tracking-eyebrow hover:text-ink transition-colors"
          >
            <div className="flex items-center gap-1.5">
              <Users size={11} className="text-linear-primary" />
              <span>Agents ({agents.length})</span>
            </div>
            {openSections.agents ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
          </button>

          {openSections.agents && (
            <div className="mt-1 space-y-1">
              {agents.slice(0, 6).map((a) => (
                <Link
                  key={a.id}
                  href={`/agents`}
                  className="flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs text-ink-subtle hover:text-ink hover:bg-surface-1 transition-colors border border-transparent hover:border-hairline group"
                >
                  <div className="flex items-center gap-2 truncate min-w-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                    <span className="truncate text-[11.5px] font-medium">{a.name}</span>
                  </div>
                  <span className="text-[9.5px] font-mono text-ink-tertiary">
                    {a.model?.replace("gemini-", "").replace("-flash", "")}
                  </span>
                </Link>
              ))}

              {/* Grouped Agent Runs Sub-section */}
              {agentRuns.length > 0 && (
                <div className="pt-2 mt-1">
                  <div className="px-2 pb-1 text-[9px] uppercase tracking-wider font-mono text-ink-tertiary flex items-center justify-between">
                    <span>Recent Telemetry Turns</span>
                    <Zap size={9} />
                  </div>
                  <div className="space-y-0.5">
                    {agentRuns.slice(0, 4).map((ar, idx) => (
                      <div
                        key={idx}
                        className="px-2.5 py-1 rounded bg-surface-1/60 border border-hairline/80 flex items-center justify-between text-[10.5px]"
                      >
                        <span className="truncate text-ink font-mono">{ar.agent_id}</span>
                        <span className="text-[9.5px] font-mono text-ink-tertiary shrink-0 ml-1">
                          {ar.total_tokens || 0} toks · {ar.latency_ms ? `${Math.round(ar.latency_ms)}ms` : "fast"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Sanitized Bottom Rail (Clean Links to Studios) */}
      <div className="p-2 border-t border-hairline bg-surface-1/40 flex items-center justify-between text-xs">
        <Link
          href="/artifacts"
          className="flex items-center gap-1.5 px-2 py-1 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-1 transition-colors"
        >
          <FolderArchive size={12} className="text-linear-primary" />
          <span className="text-[11px] font-medium">Artifacts</span>
        </Link>

        <span className="flex items-center gap-1 text-[10px] font-mono text-ink-tertiary">
          <Activity size={10} className="text-emerald-400" />
          <span>v2.0</span>
        </span>
      </div>
    </aside>
  );
}
