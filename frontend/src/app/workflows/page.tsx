"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Workflow,
} from "./types";
import AIWorkflowGeneratorModal from "./components/AIWorkflowGeneratorModal";
import AppNavigationRail from "@/app/components/AppNavigationRail";
import AppUnifiedSidebar from "@/components/AppUnifiedSidebar";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import {
  Plus,
  Search,
  Sparkles,
  Layers,
  ArrowRight,
  Globe,
  Lock,
  Trash2,
  Check,
  Bot,
  Share2,
  AlertCircle,
} from "lucide-react";
import { supabase, getAuthHeaders } from "@/lib/supabase";

export default function WorkflowsDashboardPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<"all" | "mine" | "shared">("all");
  const [userEmail, setUserEmail] = useState<string | null>(null);

  // Create & AI Modal states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isAIModalOpen, setIsAIModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newGoal, setNewGoal] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [copiedSlug, setCopiedSlug] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Check auth session
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUserEmail(session?.user?.email || null);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUserEmail(session?.user?.email || null);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    setUserEmail(null);
    fetchWorkflows();
  };

  const fetchWorkflows = useCallback(async () => {
    setIsLoading(true);
    try {
      const authHeaders = await getAuthHeaders();
      const res = await fetch(`${apiUrl}/api/workflows`, {
        headers: authHeaders,
      });
      if (res.ok) {
        const data: Workflow[] = await res.json();
        setWorkflows(data);
      }
    } catch (err) {
      console.error("Fetch workflows error:", err);
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  const handleCreate = async () => {
    if (!newTitle.trim() || !newGoal.trim()) return;
    setIsCreating(true);
    setCreateError(null);

    try {
      const payload = {
        title: newTitle.trim(),
        description: newDescription.trim(),
        goal: newGoal.trim(),
        visibility: "private",
        steps: [
          {
            id: "step_1",
            name: "Initial Discovery & Analysis",
            agent_id: "researcher",
            instructions: "Conduct investigative analysis for: {{goal}} with input: {{inputs.query}}",
            tool_ids: [],
            knowledge_file_ids: [],
            depends_on: [],
          },
          {
            id: "step_2",
            name: "Synthesis & Solution Delivery",
            agent_id: "synthesizer",
            instructions: "Synthesize findings into an executive report: {{steps.step_1.output.text}}",
            tool_ids: [],
            knowledge_file_ids: [],
            depends_on: ["step_1"],
          },
        ],
        edges: [{ source: "step_1", target: "step_2" }],
      };

      const authHeaders = await getAuthHeaders();
      const res = await fetch(`${apiUrl}/api/workflows`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const created: Workflow = await res.json();
        setIsCreateOpen(false);
        router.push(`/workflows/${created.id}`);
      } else {
        const errJson = await res.json().catch(() => ({}));
        if (res.status === 401) {
          setCreateError("Your session expired or you are not signed in. Please sign in to create workflows.");
        } else {
          setCreateError(errJson.detail || `Failed to create workflow (${res.status})`);
        }
      }
    } catch (err) {
      console.error("Create workflow error:", err);
      setCreateError("Network or server connection failed. Please ensure the backend is running.");
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this workflow?")) return;
    try {
      const authHeaders = await getAuthHeaders();
      await fetch(`${apiUrl}/api/workflows/${id}`, {
        method: "DELETE",
        headers: authHeaders,
      });
      setWorkflows((prev) => prev.filter((w) => w.id !== id));
    } catch (err) {
      console.error("Delete workflow error:", err);
    }
  };

  const handleCopyShare = (slug: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const url = `${window.location.origin}/workflows/share/${slug}`;
    navigator.clipboard.writeText(url);
    setCopiedSlug(slug);
    setTimeout(() => setCopiedSlug(null), 2000);
  };

  const filteredWorkflows = workflows.filter((w) => {
    const matchesSearch =
      w.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      w.goal.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;
    if (activeFilter === "shared") return w.visibility === "shared" || w.visibility === "public";
    if (activeFilter === "mine") return w.visibility === "private";
    return true;
  });

  return (
    <div className="min-h-screen bg-canvas text-ink flex flex-col font-sans selection:bg-linear-primary/25 selection:text-ink">
      {/* 1. Unified 3-Pillar Top Navigation Rail */}
      <AppNavigationRail
        currentTab="workflows"
        userEmail={userEmail}
        onSignOut={handleSignOut}
      />

      <div className="flex flex-1 overflow-hidden relative">
        {/* Unified Persistent Studio Sidebar */}
        <AppUnifiedSidebar
          activePage="workflows"
          onCreateWorkflow={() => setIsCreateOpen(true)}
        />

        <div className="flex-1 flex flex-col bg-canvas overflow-y-auto h-full">
          {/* 2. Workflows Studio Header Banner */}
          <div className="border-b border-hairline bg-surface-1/40 px-4 md:px-8 py-5">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-ink">
                Workflows Studio
              </h1>
              <span className="text-xs font-mono px-2 py-0.5 rounded-pill bg-surface-2 border border-hairline text-ink-subtle">
                {workflows.length} Pipelines
              </span>
            </div>
            <p className="text-xs text-ink-subtle mt-1 leading-relaxed">
              Design, test, and execute deterministic multi-agent DAG pipelines with conditions and Python tools.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0 self-stretch sm:self-auto">
            <button
              type="button"
              onClick={() => setIsAIModalOpen(true)}
              className="flex-1 sm:flex-none px-3.5 py-1.5 text-xs font-medium text-ink hover:text-white bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong rounded-md transition-colors shadow-xs flex items-center justify-center gap-1.5"
              title="Synthesize an autonomous workflow DAG using natural language with Gemini 3.8"
            >
              <Sparkles size={13} className="text-linear-primary" />
              <span>AI Architect</span>
            </button>
            <button
              onClick={() => {
                setNewTitle("New Autonomous Workflow");
                setNewGoal("Define the primary goal of this workflow...");
                setNewDescription("");
                setCreateError(null);
                setIsCreateOpen(true);
              }}
              className="flex-1 sm:flex-none px-3.5 py-1.5 text-xs font-medium bg-linear-primary hover:bg-linear-hover text-white rounded-md transition-colors shadow-xs flex items-center justify-center gap-1.5"
            >
              <Plus size={13} />
              <span>New Workflow</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 p-4 md:p-8 max-w-6xl w-full mx-auto space-y-6">
        {/* Search & Tabs Toolbar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Tabs in Linear pill toggle style */}
          <div className="flex items-center gap-1 p-0.5 rounded-pill bg-surface-1 border border-hairline self-start">
            <button
              onClick={() => setActiveFilter("all")}
              className={`px-3 py-1 text-xs rounded-pill font-medium transition-colors ${
                activeFilter === "all"
                  ? "bg-surface-2 text-ink border border-hairline-strong shadow-none"
                  : "text-ink-subtle hover:text-ink"
              }`}
            >
              All ({workflows.length})
            </button>
            <button
              onClick={() => setActiveFilter("mine")}
              className={`px-3 py-1 text-xs rounded-pill font-medium transition-colors ${
                activeFilter === "mine"
                  ? "bg-surface-2 text-ink border border-hairline-strong shadow-none"
                  : "text-ink-subtle hover:text-ink"
              }`}
            >
              My Workflows
            </button>
            <button
              onClick={() => setActiveFilter("shared")}
              className={`px-3 py-1 text-xs rounded-pill font-medium transition-colors ${
                activeFilter === "shared"
                  ? "bg-surface-2 text-ink border border-hairline-strong shadow-none"
                  : "text-ink-subtle hover:text-ink"
              }`}
            >
              Shared
            </button>
          </div>

          {/* Search Box */}
          <div className="relative max-w-xs w-full">
            <Search
              size={13}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-tertiary"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search workflows by goal..."
              className="w-full text-xs bg-surface-1 border border-hairline hover:border-hairline-strong rounded-md pl-8 pr-3 py-1.5 text-ink placeholder:text-ink-tertiary focus:outline-none focus:ring-1 focus:ring-linear-focus font-sans"
            />
          </div>
        </div>

        {/* Workflows Cards Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="p-5 rounded-lg bg-surface-1 border border-hairline animate-pulse flex flex-col justify-between h-44"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-md bg-surface-2 shrink-0" />
                      <div className="h-4 w-32 rounded bg-surface-2" />
                    </div>
                    <div className="h-4 w-12 rounded bg-surface-2" />
                  </div>
                  <div className="space-y-2">
                    <div className="h-3 w-full rounded bg-surface-2" />
                    <div className="h-3 w-4/5 rounded bg-surface-2" />
                  </div>
                </div>
                <div className="pt-3 border-t border-hairline flex items-center justify-between">
                  <div className="h-3 w-16 rounded bg-surface-2" />
                  <div className="h-3 w-20 rounded bg-surface-2" />
                </div>
              </div>
            ))}
          </div>
        ) : filteredWorkflows.length === 0 ? (
          <div className="p-12 text-center border border-hairline rounded-lg bg-surface-1 max-w-md mx-auto">
            <Layers className="w-10 h-10 text-ink-tertiary mx-auto mb-3" />
            <h3 className="text-sm font-medium text-ink">No workflows found</h3>
            <p className="text-xs text-ink-subtle mt-1 mb-5">
              Create your first multi-agent workflow to automate complex pipelines.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <button
                type="button"
                onClick={() => setIsAIModalOpen(true)}
                className="px-3.5 py-1.5 bg-surface-2 hover:bg-surface-3 border border-hairline hover:border-hairline-strong text-ink text-xs font-medium rounded-md transition-colors inline-flex items-center gap-1.5 shadow-card"
              >
                <Sparkles size={13} className="text-linear-primary" /> Architect with AI
              </button>
              <button
                onClick={() => setIsCreateOpen(true)}
                className="px-3.5 py-1.5 bg-linear-primary hover:bg-linear-hover text-white text-xs font-medium rounded-md transition-colors inline-flex items-center gap-1.5"
              >
                <Plus size={13} /> Create Manual
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredWorkflows.map((wf) => {
              const isShared = wf.visibility === "shared" || wf.visibility === "public";
              const stepCount = wf.steps?.length || 0;

              return (
                <SpotlightCard
                  key={wf.id}
                  onClick={() => router.push(`/workflows/${wf.id}`)}
                  className="p-5 flex flex-col justify-between cursor-pointer group"
                >
                  <div>
                    {/* Card Header */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-md bg-surface-2 text-linear-primary border border-hairline flex items-center justify-center shrink-0">
                          <Sparkles size={12} />
                        </span>
                        <h3 className="text-sm font-medium text-ink group-hover:text-linear-primary transition-colors line-clamp-1 tracking-card-title">
                          {wf.title}
                        </h3>
                      </div>

                      {isShared ? (
                        <span className="text-[10px] px-2 py-0.5 rounded-pill bg-surface-2 text-linear-primary border border-hairline font-mono flex items-center gap-1 shrink-0">
                          <Globe size={9} /> Shared
                        </span>
                      ) : (
                        <span className="text-[10px] px-2 py-0.5 rounded-pill bg-surface-2 text-ink-subtle border border-hairline font-mono flex items-center gap-1 shrink-0">
                          <Lock size={9} /> Private
                        </span>
                      )}
                    </div>

                    {/* Goal Snippet */}
                    <p className="text-xs text-ink-subtle line-clamp-3 mb-4 leading-relaxed tracking-body">
                      {wf.goal}
                    </p>
                  </div>

                  {/* Card Footer */}
                  <div className="pt-3 border-t border-hairline flex items-center justify-between text-[11px] text-ink-subtle">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1 font-mono text-[10px]">
                        <Bot size={11} className="text-linear-primary" /> {stepCount} steps
                      </span>
                    </div>

                    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                      {wf.share_slug && (
                        <button
                          onClick={(e) => handleCopyShare(wf.share_slug!, e)}
                          className="p-1 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-3 transition-colors"
                          title="Copy share link"
                        >
                          {copiedSlug === wf.share_slug ? (
                            <Check size={12} className="text-semantic-success" />
                          ) : (
                            <Share2 size={12} />
                          )}
                        </button>
                      )}
                      <button
                        onClick={(e) => handleDelete(wf.id, e)}
                        className="p-1 rounded-md text-ink-subtle hover:text-red-400 hover:bg-surface-3 transition-colors"
                        title="Delete workflow"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                </SpotlightCard>
              );
            })}
          </div>
        )}
      </main>
        </div>
      </div>

      {/* Create Workflow Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in font-sans">
          <div className="bg-surface-1 border border-hairline rounded-lg w-full max-w-lg p-6 space-y-4 shadow-card">
            <h3 className="text-sm font-medium text-ink tracking-card-title">Create Autonomous Workflow</h3>
            <p className="text-xs text-ink-subtle leading-relaxed">
              Define the title and primary goal. You will be redirected to the Workflow Studio to configure agents and steps.
            </p>

            <div className="flex items-center justify-between p-2 rounded-md bg-surface-2/60 border border-hairline">
              <div className="flex items-center gap-1.5 text-xs text-ink-muted">
                <Sparkles size={12} className="text-linear-primary shrink-0" />
                <span>Prefer natural language?</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setIsCreateOpen(false);
                  setIsAIModalOpen(true);
                }}
                className="text-[11px] font-medium text-linear-primary hover:text-linear-hover transition-colors flex items-center gap-1"
              >
                <span>Generate with AI Mode</span>
                <ArrowRight size={10} />
              </button>
            </div>

            <div className="space-y-3 pt-2">
              <div>
                <label className="text-xs font-medium text-ink-subtle block mb-1">
                  Workflow Title
                </label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Competitive Intel & Threat Analysis"
                  className="w-full text-xs bg-canvas border border-hairline hover:border-hairline-strong rounded-md px-3 py-1.5 text-ink placeholder:text-ink-tertiary focus:outline-none focus:ring-1 focus:ring-linear-focus font-sans"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-ink-subtle block mb-1">
                  Primary Workflow Goal
                </label>
                <textarea
                  rows={3}
                  value={newGoal}
                  onChange={(e) => setNewGoal(e.target.value)}
                  placeholder="What should this multi-agent workflow accomplish?"
                  className="w-full text-xs bg-canvas border border-hairline hover:border-hairline-strong rounded-md p-3 text-ink placeholder:text-ink-tertiary focus:outline-none focus:ring-1 focus:ring-linear-focus font-sans"
                />
              </div>
            </div>

            {createError && (
              <div className="p-2.5 rounded-md bg-surface-2 border border-red-500/30 text-red-400 text-xs flex items-start gap-2">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                <span>{createError}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-hairline">
              <button
                onClick={() => setIsCreateOpen(false)}
                className="px-3 py-1.5 text-xs text-ink-subtle hover:text-ink transition-colors"
              >
                Cancel
              </button>
              <button
                disabled={!newTitle.trim() || !newGoal.trim() || isCreating}
                onClick={handleCreate}
                className="px-3.5 py-1.5 text-xs font-medium bg-linear-primary hover:bg-linear-hover text-white rounded-md disabled:opacity-40 transition-colors flex items-center gap-1.5"
              >
                {isCreating ? "Creating..." : "Create & Open Studio"}
                <ArrowRight size={12} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI Workflow Generator Modal */}
      <AIWorkflowGeneratorModal
        isOpen={isAIModalOpen}
        onClose={() => setIsAIModalOpen(false)}
        onCreated={(createdWf) => {
          setIsAIModalOpen(false);
          router.push(`/workflows/${createdWf.id}`);
        }}
      />
    </div>
  );
}
