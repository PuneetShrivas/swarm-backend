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
import WorkflowSystemTestModal from "../components/WorkflowSystemTestModal";
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
  const [viewMode, setViewMode] = useState<ViewMode>("graph");
  const [unitTestStep, setUnitTestStep] = useState<WorkflowStep | null>(null);
  const [isUnitTestModalOpen, setIsUnitTestModalOpen] = useState(false);
  const [isSystemTestModalOpen, setIsSystemTestModalOpen] = useState(false);

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
      <div className="flex h-screen items-center justify-center bg-canvas text-ink font-sans">
        <div className="flex flex-col items-center gap-2">
          <Loader2 size={24} className="animate-spin text-linear-primary" />
          <span className="text-xs text-ink-subtle">Loading Workflow Studio...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas text-ink flex flex-col font-sans selection:bg-linear-primary/25 selection:text-ink">
      {/* Top Studio Navbar */}
      <header className="h-14 border-b border-hairline bg-canvas/90 backdrop-blur-md px-4 md:px-6 flex items-center justify-between sticky top-0 z-30">
        {/* Left: Back & Title */}
        <div className="flex items-center gap-2.5 min-w-0">
          <Link
            href="/workflows"
            className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-1 transition-colors border border-hairline"
            title="Back to Workflows"
          >
            <ArrowLeft size={14} />
          </Link>

          <div className="min-w-0">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Workflow Title"
              className="text-xs md:text-sm font-medium text-ink bg-transparent border-b border-transparent hover:border-hairline focus:border-linear-focus focus:outline-none px-1 py-0.5 truncate transition-colors max-w-[180px] sm:max-w-xs md:max-w-md font-sans"
            />
            <div className="flex items-center gap-1.5 text-[10px] text-ink-subtle px-1 font-mono">
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
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-1 border border-hairline text-xs">
            {visibility === "shared" ? (
              <Globe size={12} className="text-linear-primary" />
            ) : (
              <Lock size={12} className="text-ink-subtle" />
            )}
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value as "private" | "shared" | "public")}
              className="bg-transparent text-xs text-ink focus:outline-none cursor-pointer"
            >
              <option value="private">Private</option>
              <option value="shared">Shared (Link Only)</option>
              <option value="public">Public</option>
            </select>
          </div>

          {visibility !== "private" && (
            <button
              onClick={handleCopyShareLink}
              className="px-2.5 py-1.5 text-xs font-medium border border-hairline bg-surface-1 hover:bg-surface-2 text-ink rounded-md transition-colors flex items-center gap-1.5"
              title="Copy view-only share link"
            >
              {copiedShare ? (
                <>
                  <Check size={12} className="text-semantic-success" /> Copied
                </>
              ) : (
                <>
                  <Share2 size={12} /> Share
                </>
              )}
            </button>
          )}

          {/* System Test Trigger */}
          <button
            onClick={() => setIsSystemTestModalOpen(true)}
            className="px-3 py-1.5 text-xs font-medium bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong text-ink rounded-md transition-colors flex items-center gap-1.5"
            title="Execute entire workflow end-to-end with custom inputs"
          >
            <Play size={11} className="fill-current text-semantic-success" />
            <span className="hidden sm:inline">System Test</span>
          </button>

          {/* Save Button */}
          <button
            disabled={isSaving}
            onClick={handleSave}
            className="px-3.5 py-1.5 text-xs font-medium bg-linear-primary hover:bg-linear-hover text-white rounded-md transition-colors flex items-center gap-1.5 disabled:opacity-40"
          >
            {isSaving ? (
              <Loader2 size={12} className="animate-spin" />
            ) : saveSuccess ? (
              <Check size={12} className="text-white" />
            ) : (
              <Save size={12} />
            )}
            <span>{saveSuccess ? "Saved!" : "Save"}</span>
          </button>
        </div>
      </header>

      {/* Alert Banners */}
      {errorMessage && (
        <div className="bg-surface-2 border-b border-red-500/30 text-red-400 text-xs px-6 py-2 flex items-center gap-2 font-sans">
          <AlertCircle size={13} className="shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Studio Tab Navigation */}
      <div className="px-4 md:px-6 border-b border-hairline bg-canvas flex items-center justify-between h-11">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("editor")}
            className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === "editor"
                ? "bg-surface-2 text-ink border border-hairline-strong"
                : "text-ink-subtle hover:text-ink"
            }`}
          >
            <Sparkles size={12} className="text-linear-primary" /> Workflow Editor
          </button>
          <button
            onClick={() => setActiveTab("tools")}
            className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === "tools"
                ? "bg-surface-2 text-ink border border-hairline-strong"
                : "text-ink-subtle hover:text-ink"
            }`}
          >
            <Code2 size={12} /> Python Tools ({tools.length})
          </button>
          <button
            onClick={() => setActiveTab("knowledge")}
            className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === "knowledge"
                ? "bg-surface-2 text-ink border border-hairline-strong"
                : "text-ink-subtle hover:text-ink"
            }`}
          >
            <FolderOpen size={12} /> Knowledge ({knowledgeFiles.length})
          </button>
          <button
            onClick={() => setActiveTab("runs")}
            className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === "runs"
                ? "bg-surface-2 text-ink border border-hairline-strong"
                : "text-ink-subtle hover:text-ink"
            }`}
          >
            <Activity size={12} /> Runs ({runs.length})
          </button>
        </div>

        {/* View Mode Toggle (Active in Editor Tab) */}
        {activeTab === "editor" && (
          <div className="flex items-center gap-1 p-0.5 rounded-pill bg-surface-1 border border-hairline">
            <button
              onClick={() => setViewMode("cards")}
              className={`px-2.5 py-0.5 text-xs rounded-pill font-medium transition-colors flex items-center gap-1.5 ${
                viewMode === "cards"
                  ? "bg-surface-2 text-ink border border-hairline-strong shadow-none"
                  : "text-ink-subtle hover:text-ink"
              }`}
            >
              <LayoutList size={12} /> Cards
            </button>
            <button
              onClick={() => setViewMode("graph")}
              className={`px-2.5 py-0.5 text-xs rounded-pill font-medium transition-colors flex items-center gap-1.5 ${
                viewMode === "graph"
                  ? "bg-surface-2 text-ink border border-hairline-strong shadow-none"
                  : "text-ink-subtle hover:text-ink"
              }`}
            >
              <Network size={12} className="text-linear-primary" /> Visual DAG
            </button>
          </div>
        )}
      </div>

      {/* Main Studio Body */}
      <main className="flex-1 p-4 md:p-6 max-w-6xl w-full mx-auto space-y-6">
        {activeTab === "editor" && (
          <div className="space-y-4">
            {/* Goal Configuration Card */}
            <div className="p-4 rounded-lg bg-surface-1 border border-hairline space-y-2">
              <label className="text-xs font-medium text-ink flex items-center gap-1.5 tracking-card-title">
                <Sparkles size={13} className="text-linear-primary" /> Primary Workflow Goal & Objective
              </label>
              <textarea
                rows={2}
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="Describe the ultimate objective of this workflow..."
                className="w-full text-xs bg-canvas border border-hairline hover:border-hairline-strong rounded-md p-2.5 text-ink focus:outline-none focus:ring-1 focus:ring-linear-focus leading-relaxed font-sans"
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
                onRunSystemTest={() => setIsSystemTestModalOpen(true)}
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
                onRunSystemTest={() => setIsSystemTestModalOpen(true)}
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
        workflowGoal={goal}
        isOpen={isUnitTestModalOpen}
        onClose={() => {
          setIsUnitTestModalOpen(false);
          setUnitTestStep(null);
        }}
      />

      {/* Workflow End-to-End System Test Modal */}
      <WorkflowSystemTestModal
        workflowId={workflowId}
        workflowTitle={title}
        workflowGoal={goal}
        steps={steps}
        isOpen={isSystemTestModalOpen}
        onClose={() => setIsSystemTestModalOpen(false)}
        onRunComplete={fetchAuxiliary}
        onNavigateToRuns={() => setActiveTab("runs")}
      />
    </div>
  );
}
