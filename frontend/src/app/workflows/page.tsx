"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Workflow,
} from "./types";
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
  MessageSquare,
  Bot,
  Loader2,
  Share2,
  LogIn,
  LogOut,
  AlertCircle,
} from "lucide-react";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { supabase, getAuthHeaders } from "@/lib/supabase";

export default function WorkflowsDashboardPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<"all" | "mine" | "shared">("all");
  const [userEmail, setUserEmail] = useState<string | null>(null);

  // Create Modal state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
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
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans transition-colors duration-200">
      {/* Top Navbar */}
      <header className="h-16 border-b border-border/80 bg-card/70 backdrop-blur-xl px-4 md:px-8 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/25 flex items-center justify-center text-primary shadow-subtle">
            <Layers size={18} />
          </div>
          <div>
            <h1 className="text-sm md:text-base font-bold text-foreground">
              Autonomous Workflows
            </h1>
            <p className="text-[11px] text-muted-foreground hidden sm:block">
              Build, test, debug & share multi-agent autonomous pipelines
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/chat"
            className="px-3 py-1.5 text-xs font-medium border border-border bg-card hover:bg-muted text-foreground rounded-xl transition flex items-center gap-1.5 shadow-subtle"
          >
            <MessageSquare size={13} /> Chat Workspace
          </Link>
          <button
            onClick={() => {
              setNewTitle("New Autonomous Workflow");
              setNewGoal("Define the primary goal of this workflow...");
              setNewDescription("");
              setCreateError(null);
              setIsCreateOpen(true);
            }}
            className="px-3.5 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-xl hover:opacity-90 transition flex items-center gap-1.5 shadow-subtle"
          >
            <Plus size={14} /> New Workflow
          </button>
          {userEmail ? (
            <div className="flex items-center gap-1.5 pl-1.5 border-l border-border/60">
              <span className="text-[11px] text-muted-foreground hidden lg:inline max-w-[140px] truncate" title={userEmail}>
                {userEmail}
              </span>
              <button
                onClick={handleSignOut}
                title="Sign out"
                className="p-1.5 rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted transition"
              >
                <LogOut size={13} />
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="px-2.5 py-1.5 text-xs border border-primary/30 bg-primary/10 text-primary hover:bg-primary/20 rounded-xl transition flex items-center gap-1"
            >
              <LogIn size={13} /> Sign In
            </Link>
          )}
          <ThemeSwitcher />
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto space-y-6">
        {/* Search & Tabs Toolbar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Tabs */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-card border border-border self-start">
            <button
              onClick={() => setActiveFilter("all")}
              className={`px-3 py-1 text-xs rounded-lg font-medium transition ${
                activeFilter === "all"
                  ? "bg-primary text-primary-foreground shadow-subtle"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              All Workflows ({workflows.length})
            </button>
            <button
              onClick={() => setActiveFilter("mine")}
              className={`px-3 py-1 text-xs rounded-lg font-medium transition ${
                activeFilter === "mine"
                  ? "bg-primary text-primary-foreground shadow-subtle"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              My Private
            </button>
            <button
              onClick={() => setActiveFilter("shared")}
              className={`px-3 py-1 text-xs rounded-lg font-medium transition ${
                activeFilter === "shared"
                  ? "bg-primary text-primary-foreground shadow-subtle"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Shared
            </button>
          </div>

          {/* Search Box */}
          <div className="relative max-w-xs w-full">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search workflows by goal..."
              className="w-full text-xs bg-card border border-border rounded-xl pl-9 pr-3 py-2 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        {/* Workflows Cards Grid */}
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center gap-3">
            <Loader2 size={28} className="animate-spin text-primary" />
            <span className="text-xs text-muted-foreground">Loading workflows...</span>
          </div>
        ) : filteredWorkflows.length === 0 ? (
          <div className="p-16 text-center border-2 border-dashed border-border/80 rounded-3xl bg-card/40 max-w-lg mx-auto">
            <Layers className="w-12 h-12 text-muted-foreground opacity-40 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-foreground">No workflows found</h3>
            <p className="text-xs text-muted-foreground mt-1 mb-6">
              Create your first multi-agent workflow to automate complex research, coding, or analytics pipelines.
            </p>
            <button
              onClick={() => setIsCreateOpen(true)}
              className="px-4 py-2 bg-primary text-primary-foreground text-xs font-medium rounded-xl hover:opacity-90 transition shadow-subtle inline-flex items-center gap-1.5"
            >
              <Plus size={14} /> Create Workflow
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredWorkflows.map((wf) => {
              const isShared = wf.visibility === "shared" || wf.visibility === "public";
              const stepCount = wf.steps?.length || 0;

              return (
                <div
                  key={wf.id}
                  onClick={() => router.push(`/workflows/${wf.id}`)}
                  className="p-5 rounded-2xl bg-card border border-border/80 shadow-subtle hover:border-primary/40 hover:shadow-medium transition cursor-pointer flex flex-col justify-between group"
                >
                  <div>
                    {/* Card Header */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-7 h-7 rounded-lg bg-primary/10 text-primary border border-primary/20 flex items-center justify-center shrink-0">
                          <Sparkles size={14} />
                        </span>
                        <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition line-clamp-1">
                          {wf.title}
                        </h3>
                      </div>

                      {isShared ? (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-medium flex items-center gap-1 shrink-0">
                          <Globe size={10} /> Shared
                        </span>
                      ) : (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground font-medium flex items-center gap-1 shrink-0">
                          <Lock size={10} /> Private
                        </span>
                      )}
                    </div>

                    {/* Goal Snippet */}
                    <p className="text-xs text-muted-foreground line-clamp-3 mb-4 leading-relaxed">
                      {wf.goal}
                    </p>
                  </div>

                  {/* Card Footer */}
                  <div className="pt-3 border-t border-border/60 flex items-center justify-between text-[11px] text-muted-foreground">
                    <div className="flex items-center gap-2.5">
                      <span className="flex items-center gap-1">
                        <Bot size={11} className="text-primary" /> {stepCount} steps
                      </span>
                    </div>

                    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                      {wf.share_slug && (
                        <button
                          onClick={(e) => handleCopyShare(wf.share_slug!, e)}
                          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
                          title="Copy share link"
                        >
                          {copiedSlug === wf.share_slug ? (
                            <Check size={13} className="text-emerald-500" />
                          ) : (
                            <Share2 size={13} />
                          )}
                        </button>
                      )}
                      <button
                        onClick={(e) => handleDelete(wf.id, e)}
                        className="p-1.5 rounded-lg text-destructive/80 hover:text-destructive hover:bg-destructive/10 transition"
                        title="Delete workflow"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      {/* Create Workflow Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-card border border-border rounded-2xl w-full max-w-lg p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-foreground">Create Autonomous Workflow</h3>
            <p className="text-xs text-muted-foreground">
              Define the title and primary goal. You will be redirected to the Workflow Studio to visually configure agents and steps.
            </p>

            <div className="space-y-3 pt-2">
              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  Workflow Title
                </label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Competitive Intel & Threat Analysis"
                  className="w-full text-xs bg-background border border-border rounded-xl px-3 py-2 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  Primary Workflow Goal
                </label>
                <textarea
                  rows={3}
                  value={newGoal}
                  onChange={(e) => setNewGoal(e.target.value)}
                  placeholder="What should this multi-agent workflow accomplish?"
                  className="w-full text-xs bg-background border border-border rounded-xl p-3 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            {createError && (
              <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-xs flex items-start gap-2">
                <AlertCircle size={15} className="shrink-0 mt-0.5" />
                <span>{createError}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
              <button
                onClick={() => setIsCreateOpen(false)}
                className="px-3.5 py-1.5 text-xs text-muted-foreground hover:text-foreground"
              >
                Cancel
              </button>
              <button
                disabled={!newTitle.trim() || !newGoal.trim() || isCreating}
                onClick={handleCreate}
                className="px-4 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-xl hover:opacity-90 disabled:opacity-50 transition shadow-subtle flex items-center gap-1.5"
              >
                {isCreating ? "Creating..." : "Create & Open Studio"}
                <ArrowRight size={13} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
