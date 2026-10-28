"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Workflow,
  KnowledgeFile,
} from "../../types";
import StepCardEditor from "../../components/StepCardEditor";
import VisualGraphEditor from "../../components/VisualGraphEditor";
import { getAuthHeaders } from "@/lib/supabase";
import {
  ArrowLeft,
  GitFork,
  Play,
  Globe,
  Loader2,
  AlertCircle,
  Sparkles,
  LayoutList,
  Network,
  Shield,
} from "lucide-react";

export default function SharedWorkflowViewPage() {
  const params = useParams();
  const router = useRouter();
  const shareSlug = params.shareSlug as string;

  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [agents, setAgents] = useState<Array<{ id: string; name: string; role?: string; icon?: string }>>([]);
  const [knowledgeFiles, setKnowledgeFiles] = useState<KnowledgeFile[]>([]);
  const [viewMode, setViewMode] = useState<"cards" | "graph">("cards");

  const [isLoading, setIsLoading] = useState(true);
  const [isForking, setIsForking] = useState(false);
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchSharedWorkflow = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/workflows/shared/${shareSlug}`);
      if (res.ok) {
        const data: Workflow = await res.json();
        setWorkflow(data);

        // Fetch agents & auxiliary
        const agRes = await fetch(`${apiUrl}/api/agents`);
        if (agRes.ok) setAgents(await agRes.json());

        const kbRes = await fetch(`${apiUrl}/api/workflows/${data.id}/knowledge`);
        if (kbRes.ok) setKnowledgeFiles(await kbRes.json());
      } else {
        setErrorMessage("Shared workflow not found or has been made private.");
      }
    } catch (err) {
      console.error(err);
      setErrorMessage("Could not load shared workflow.");
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl, shareSlug]);

  useEffect(() => {
    fetchSharedWorkflow();
  }, [fetchSharedWorkflow]);

  const handleFork = async () => {
    if (!workflow) return;
    setIsForking(true);
    try {
      const authHeaders = await getAuthHeaders();
      const res = await fetch(`${apiUrl}/api/workflows/${workflow.id}/fork`, {
        method: "POST",
        headers: authHeaders,
      });
      if (res.ok) {
        const forked: Workflow = await res.json();
        router.push(`/workflows/${forked.id}`);
      }
    } catch (err) {
      console.error("Fork error:", err);
    } finally {
      setIsForking(false);
    }
  };

  const handleRunSample = async () => {
    if (!workflow) return;
    setIsRunningTest(true);
    setTestResult(null);
    try {
      const authHeaders = await getAuthHeaders();
      const res = await fetch(`${apiUrl}/api/workflows/${workflow.id}/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({ inputs: { query: workflow.goal } }),
      });
      if (res.ok) {
        const data = await res.json();
        setTestResult(data.output_data?.final_result || "Test execution complete.");
      }
    } catch (err) {
      console.error("Sample run error:", err);
    } finally {
      setIsRunningTest(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background text-foreground">
        <Loader2 size={28} className="animate-spin text-primary" />
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="p-12 text-center text-foreground space-y-4">
        <AlertCircle size={32} className="text-destructive mx-auto" />
        <h2 className="text-base font-semibold">Workflow Not Available</h2>
        <p className="text-xs text-muted-foreground">{errorMessage || "This shared link is invalid."}</p>
        <Link href="/workflows" className="text-xs text-primary underline">
          Return to Workflows
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans transition-colors duration-200">
      {/* Read-Only Top Banner */}
      <div className="bg-primary/10 border-b border-primary/20 text-primary px-4 py-2 text-xs flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield size={14} className="shrink-0" />
          <span>
            Viewing shared workflow: <strong>{workflow.title}</strong> (View-Only Mode)
          </span>
        </div>
        <button
          disabled={isForking}
          onClick={handleFork}
          className="px-3 py-1 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:opacity-90 disabled:opacity-50 transition flex items-center gap-1.5 shadow-subtle"
        >
          <GitFork size={13} /> {isForking ? "Cloning..." : "Fork to My Workflows"}
        </button>
      </div>

      {/* Header */}
      <header className="h-16 border-b border-border/80 bg-card/70 backdrop-blur-xl px-4 md:px-8 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <Link
            href="/workflows"
            className="p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted transition"
          >
            <ArrowLeft size={16} />
          </Link>
          <div>
            <h1 className="text-sm md:text-base font-bold text-foreground flex items-center gap-2">
              {workflow.title}
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-medium flex items-center gap-1">
                <Globe size={10} /> Shared
              </span>
            </h1>
            <p className="text-[11px] text-muted-foreground">{workflow.steps?.length || 0} steps in pipeline</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            disabled={isRunningTest}
            onClick={handleRunSample}
            className="px-3.5 py-1.5 text-xs font-medium bg-emerald-600 text-white hover:bg-emerald-500 rounded-xl transition flex items-center gap-1.5 shadow-subtle disabled:opacity-50"
          >
            <Play size={13} className="fill-current" />
            <span>{isRunningTest ? "Running..." : "Test Run"}</span>
          </button>
        </div>
      </header>

      {/* Main Studio Body */}
      <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto space-y-6">
        {/* Goal Card */}
        <div className="p-5 rounded-2xl bg-card border border-border/80 shadow-subtle space-y-2">
          <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
            <Sparkles size={14} className="text-primary" /> Workflow Goal & Objective
          </label>
          <p className="text-xs text-foreground/90 leading-relaxed font-mono bg-background/60 p-3 rounded-xl border border-border/50">
            {workflow.goal}
          </p>
        </div>

        {/* Sample Run Result Banner */}
        {testResult && (
          <div className="p-4 rounded-2xl bg-background border border-emerald-500/40 space-y-2">
            <span className="text-xs font-semibold text-emerald-500 flex items-center gap-1.5">
              <Play size={13} className="fill-current" /> Sample Test Execution Output:
            </span>
            <p className="text-xs text-foreground leading-relaxed whitespace-pre-wrap font-mono">
              {testResult}
            </p>
          </div>
        )}

        {/* Switcher & Steps */}
        <div className="flex items-center justify-between pb-2 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground">Pipeline Steps & DAG</h3>
          <div className="flex items-center gap-1 p-1 rounded-xl bg-card border border-border">
            <button
              onClick={() => setViewMode("cards")}
              className={`px-2.5 py-1 text-xs rounded-lg font-medium transition flex items-center gap-1.5 ${
                viewMode === "cards"
                  ? "bg-primary text-primary-foreground shadow-subtle"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <LayoutList size={13} /> Cards
            </button>
            <button
              onClick={() => setViewMode("graph")}
              className={`px-2.5 py-1 text-xs rounded-lg font-medium transition flex items-center gap-1.5 ${
                viewMode === "graph"
                  ? "bg-primary text-primary-foreground shadow-subtle"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Network size={13} /> Graph
            </button>
          </div>
        </div>

        {viewMode === "cards" ? (
          <StepCardEditor
            steps={workflow.steps || []}
            onChangeSteps={() => {}}
            agents={agents}
            tools={[]}
            knowledgeFiles={knowledgeFiles}
            readOnly={true}
          />
        ) : (
          <VisualGraphEditor
            goal={workflow.goal}
            steps={workflow.steps || []}
            edges={workflow.edges || []}
            onChangeSteps={() => {}}
            onChangeEdges={() => {}}
            agents={agents}
            tools={[]}
            knowledgeFiles={knowledgeFiles}
            readOnly={true}
          />
        )}
      </main>
    </div>
  );
}
