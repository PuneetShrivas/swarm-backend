"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Workflow,
  WorkflowStep,
  ScriptTool,
  KnowledgeFile,
  WorkflowRun,
} from "../types";
import StepCardEditor from "../components/StepCardEditor";
import VisualGraphEditor from "../components/VisualGraphEditor";
import ToolScriptEditor from "../components/ToolScriptEditor";
import { getAuthHeaders } from "@/lib/supabase";
import KnowledgeBaseManager from "../components/KnowledgeBaseManager";
import WorkflowRunsDebugger from "../components/WorkflowRunsDebugger";
import StepUnitTestModal from "../components/StepUnitTestModal";
import {
  ArrowLeft,
  Save,
  Play,
  Share2,
  Check,
  LayoutList,
  Network,
  Code2,
  FolderOpen,
  Activity,
  Globe,
  Lock,
  Loader2,
  AlertCircle,
  Sparkles,
} from "lucide-react";

type StudioTab = "editor" | "tools" | "knowledge" | "runs";
type ViewMode = "cards" | "graph";

export default function WorkflowStudioPage() {
  const params = useParams();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [agents, setAgents] = useState<Array<{ id: string; name: string; role?: string; icon?: string }>>([]);
  const [tools, setTools] = useState<ScriptTool[]>([]);
  const [knowledgeFiles, setKnowledgeFiles] = useState<KnowledgeFile[]>([]);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isRunningSystemTest, setIsRunningSystemTest] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [copiedShare, setCopiedShare] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Studio UI states
  const [activeTab, setActiveTab] = useState<StudioTab>("editor");
  const [viewMode, setViewMode] = useState<ViewMode>("cards");
  const [unitTestStep, setUnitTestStep] = useState<WorkflowStep | null>(null);
  const [isUnitTestModalOpen, setIsUnitTestModalOpen] = useState(false);

  // Form states
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [goal, setGoal] = useState("");
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [edges, setEdges] = useState<Array<{ id: string; source: string; target: string }>>([]);
  const [visibility, setVisibility] = useState<"private" | "shared" | "public">("private");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Fetch workflow detail
  const fetchWorkflow = useCallback(async () => {
    try {
      const authHeaders = await getAuthHeaders();
      const res = await fetch(`${apiUrl}/api/workflows/${workflowId}`, {
        headers: authHeaders,
      });
      if (res.ok) {
        const data: Workflow = await res.json();
        setWorkflow(data);
        setTitle(data.title);
        setDescription(data.description || "");
        setGoal(data.goal);
        setSteps(data.steps || []);
        setEdges(data.edges || []);
        setVisibility(data.visibility || "private");
      } else {
        setErrorMessage("Failed to load workflow.");
      }
    } catch (err) {
      console.error(err);
      setErrorMessage("Could not connect to API server.");
    }
  }, [apiUrl, workflowId]);

  // Fetch agents, tools, knowledge, runs
  const fetchAuxiliary = useCallback(async () => {
    try {
      const authHeaders = await getAuthHeaders();

      // 1. Agents (Prebuilt + Custom)
      const resAgents = await fetch(`${apiUrl}/api/agents`);
      if (resAgents.ok) {
        const agData = await resAgents.json();
        setAgents(agData);
      }

      // 2. Tools
      const resTools = await fetch(`${apiUrl}/api/workflow-tools`, {
        headers: authHeaders,
      });
      if (resTools.ok) {
        const toolData = await resTools.json();
        setTools(toolData);
      }

      // 3. Knowledge
      const resKb = await fetch(`${apiUrl}/api/workflows/${workflowId}/knowledge`, {
        headers: authHeaders,
      });
      if (resKb.ok) {
        const kbData = await resKb.json();
        setKnowledgeFiles(kbData);
      }

      // 4. Runs
      const resRuns = await fetch(`${apiUrl}/api/workflows/${workflowId}/runs`, {
        headers: authHeaders,
      });
      if (resRuns.ok) {
        const runData = await resRuns.json();
        setRuns(runData);
      }
    } catch (err) {
      console.error("Auxiliary fetch error:", err);
    }
  }, [apiUrl, workflowId]);

  useEffect(() => {
    setIsLoading(true);
    Promise.all([fetchWorkflow(), fetchAuxiliary()]).finally(() => {
      setIsLoading(false);
    });
  }, [fetchWorkflow, fetchAuxiliary]);

  // Save workflow
  const handleSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    setErrorMessage(null);

    const payload = {
      title,
      description,
      goal,
      steps,
      edges,
      visibility,
    };

    try {
      const authHeaders = await getAuthHeaders();
      const res = await fetch(`${apiUrl}/api/workflows/${workflowId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Save failed.");
      }

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
      fetchWorkflow();
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "An error occurred while saving.");
    } finally {
      setIsSaving(false);
    }
  };

  // Run full system test
  const handleRunSystemTest = async () => {
    setIsRunningSystemTest(true);
    setErrorMessage(null);

    try {
      const authHeaders = await getAuthHeaders();
      const res = await fetch(`${apiUrl}/api/workflows/${workflowId}/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({ inputs: { query: goal } }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Run failed.");
      }

      // Refresh runs and switch to Runs tab
      await fetchAuxiliary();
      setActiveTab("runs");
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "System execution run failed.");
    } finally {
      setIsRunningSystemTest(false);
    }
  };

  // Copy share link
  const handleCopyShareLink = () => {
    if (!workflow?.share_slug) return;
    const shareUrl = `${window.location.origin}/workflows/share/${workflow.share_slug}`;
    navigator.clipboard.writeText(shareUrl);
    setCopiedShare(true);
    setTimeout(() => setCopiedShare(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background text-foreground">
        <div className="flex flex-col items-center gap-3">
          <Loader2 size={28} className="animate-spin text-primary" />
          <span className="text-xs text-muted-foreground font-medium">Loading Workflow Studio...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans transition-colors duration-200">
      {/* Top Studio Navbar */}
      <header className="h-16 border-b border-border/80 bg-card/70 backdrop-blur-xl px-4 md:px-6 flex items-center justify-between sticky top-0 z-30">
        {/* Left: Back & Title */}
        <div className="flex items-center gap-3 min-w-0">
          <Link
            href="/workflows"
            className="p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted transition"
            title="Back to Workflows"
          >
            <ArrowLeft size={16} />
          </Link>

          <div className="min-w-0">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Workflow Title"
              className="text-sm md:text-base font-bold text-foreground bg-transparent border-b border-transparent hover:border-border focus:border-primary focus:outline-none px-1 py-0.5 truncate transition max-w-[200px] sm:max-w-xs md:max-w-md"
            />
            <div className="flex items-center gap-2 text-[11px] text-muted-foreground px-1">
              <span>{steps.length} steps</span>
              <span>•</span>
              <span>{tools.length} tools</span>
              <span>•</span>
              <span>{knowledgeFiles.length} docs</span>
            </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* Visibility selector */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-card border border-border text-xs">
            {visibility === "shared" ? (
              <Globe size={13} className="text-primary" />
            ) : (
              <Lock size={13} className="text-muted-foreground" />
            )}
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value as "private" | "shared" | "public")}
              className="bg-transparent text-xs text-foreground focus:outline-none"
            >
              <option value="private">Private</option>
              <option value="shared">Shared (Link Only)</option>
              <option value="public">Public</option>
            </select>
          </div>

          {visibility !== "private" && (
            <button
              onClick={handleCopyShareLink}
              className="px-2.5 py-1.5 text-xs font-medium border border-border bg-card hover:bg-muted text-foreground rounded-xl transition flex items-center gap-1.5"
              title="Copy view-only share link"
            >
              {copiedShare ? (
                <>
                  <Check size={13} className="text-emerald-500" /> Copied
                </>
              ) : (
                <>
                  <Share2 size={13} /> Share
                </>
              )}
            </button>
          )}

          {/* System Test Trigger */}
          <button
            disabled={isRunningSystemTest}
            onClick={handleRunSystemTest}
            className="px-3 py-1.5 text-xs font-medium bg-emerald-600 text-white hover:bg-emerald-500 rounded-xl transition flex items-center gap-1.5 shadow-subtle disabled:opacity-50"
            title="Execute entire workflow end-to-end"
          >
            <Play size={13} className="fill-current" />
            <span className="hidden sm:inline">
              {isRunningSystemTest ? "Running..." : "System Test"}
            </span>
          </button>

          {/* Save Button */}
          <button
            disabled={isSaving}
            onClick={handleSave}
            className="px-3.5 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-xl hover:opacity-90 transition flex items-center gap-1.5 shadow-subtle disabled:opacity-50"
          >
            {isSaving ? (
              <Loader2 size={13} className="animate-spin" />
            ) : saveSuccess ? (
              <Check size={13} className="text-primary-foreground" />
            ) : (
              <Save size={13} />
            )}
            <span>{saveSuccess ? "Saved!" : "Save"}</span>
          </button>
        </div>
      </header>

      {/* Alert Banners */}
      {errorMessage && (
        <div className="bg-destructive/10 border-b border-destructive/20 text-destructive text-xs px-6 py-2.5 flex items-center gap-2">
          <AlertCircle size={14} className="shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Studio Tab Navigation */}
      <div className="px-4 md:px-6 border-b border-border bg-card/40 flex items-center justify-between">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveTab("editor")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-1.5 ${
              activeTab === "editor"
                ? "border-primary text-primary font-semibold"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Sparkles size={13} /> Workflow Editor
          </button>
          <button
            onClick={() => setActiveTab("tools")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-1.5 ${
              activeTab === "tools"
                ? "border-primary text-primary font-semibold"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Code2 size={13} /> Python Tools ({tools.length})
          </button>
          <button
            onClick={() => setActiveTab("knowledge")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-1.5 ${
              activeTab === "knowledge"
                ? "border-primary text-primary font-semibold"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <FolderOpen size={13} /> Knowledge Base ({knowledgeFiles.length})
          </button>
          <button
            onClick={() => setActiveTab("runs")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-1.5 ${
              activeTab === "runs"
                ? "border-primary text-primary font-semibold"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Activity size={13} /> Runs & Debugging ({runs.length})
          </button>
        </div>

        {/* View Mode Toggle (Active in Editor Tab) */}
        {activeTab === "editor" && (
          <div className="flex items-center gap-1 p-1 rounded-xl bg-card border border-border">
            <button
              onClick={() => setViewMode("cards")}
              className={`px-2.5 py-1 text-xs rounded-lg font-medium transition flex items-center gap-1.5 ${
                viewMode === "cards"
                  ? "bg-primary text-primary-foreground shadow-subtle"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <LayoutList size={13} /> Structured Cards
            </button>
            <button
              onClick={() => setViewMode("graph")}
              className={`px-2.5 py-1 text-xs rounded-lg font-medium transition flex items-center gap-1.5 ${
                viewMode === "graph"
                  ? "bg-primary text-primary-foreground shadow-subtle"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Network size={13} /> Visual Graph (DAG)
            </button>
          </div>
        )}
      </div>

      {/* Main Studio Body */}
      <main className="flex-1 p-4 md:p-6 max-w-7xl w-full mx-auto space-y-6">
        {activeTab === "editor" && (
          <div className="space-y-6">
            {/* Goal Configuration Card */}
            <div className="p-5 rounded-2xl bg-card border border-border/80 shadow-subtle space-y-3">
              <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Sparkles size={14} className="text-primary" /> Primary Workflow Goal & Objective
              </label>
              <textarea
                rows={2}
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="Describe the ultimate objective of this workflow..."
                className="w-full text-xs bg-background/80 border border-border rounded-xl p-3 text-foreground focus:outline-none focus:ring-1 focus:ring-primary leading-relaxed resize-y"
              />
            </div>

            {/* Switchable Editor Canvas */}
            {viewMode === "cards" ? (
              <StepCardEditor
                steps={steps}
                onChangeSteps={setSteps}
                agents={agents}
                tools={tools}
                knowledgeFiles={knowledgeFiles}
                onUnitTestStep={(st) => {
                  setUnitTestStep(st);
                  setIsUnitTestModalOpen(true);
                }}
              />
            ) : (
              <VisualGraphEditor
                goal={goal}
                steps={steps}
                edges={edges}
                onChangeSteps={setSteps}
                onChangeEdges={setEdges}
                agents={agents}
                tools={tools}
                knowledgeFiles={knowledgeFiles}
                onUnitTestStep={(st) => {
                  setUnitTestStep(st);
                  setIsUnitTestModalOpen(true);
                }}
              />
            )}
          </div>
        )}

        {activeTab === "tools" && (
          <ToolScriptEditor
            tools={tools}
            onRefreshTools={fetchAuxiliary}
          />
        )}

        {activeTab === "knowledge" && (
          <KnowledgeBaseManager
            workflowId={workflowId}
            files={knowledgeFiles}
            onRefreshFiles={fetchAuxiliary}
          />
        )}

        {activeTab === "runs" && (
          <WorkflowRunsDebugger
            runs={runs}
            onRefreshRuns={fetchAuxiliary}
            onTriggerRun={handleRunSystemTest}
            isRunning={isRunningSystemTest}
          />
        )}
      </main>

      {/* Step Unit Test Modal */}
      <StepUnitTestModal
        workflowId={workflowId}
        step={unitTestStep}
        isOpen={isUnitTestModalOpen}
        onClose={() => {
          setIsUnitTestModalOpen(false);
          setUnitTestStep(null);
        }}
      />
    </div>
  );
}
