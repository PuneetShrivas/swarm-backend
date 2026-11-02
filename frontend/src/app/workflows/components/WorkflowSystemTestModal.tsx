"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import { WorkflowStep, WorkflowRun, WorkflowStepRun, TestAttachedArtifact } from "../types";
import { getAuthHeaders } from "@/lib/supabase";
import {
  Play,
  X,
  Bot,
  Zap,
  Clock,
  CheckCircle2,
  XCircle,
  SlidersHorizontal,
  Code,
  Copy,
  Check,
  ChevronRight,
  Layers,
  FileText,
  Activity,
  Sparkles,
  Paperclip,
  FolderArchive,
  Terminal,
  Loader2,
  AlertTriangle,
  Upload,
  FileSpreadsheet,
  FileCode,
  Wrench,
  Search,
  ExternalLink,
} from "lucide-react";

interface WorkflowSystemTestModalProps {
  workflowId: string;
  workflowTitle: string;
  workflowGoal: string;
  steps: WorkflowStep[];
  isOpen: boolean;
  onClose: () => void;
  onRunComplete?: () => void;
  onNavigateToRuns?: () => void;
}

interface ConsoleLogEntry {
  id: string;
  timestamp: string;
  level: "info" | "success" | "warn" | "error";
  message: string;
}

export default function WorkflowSystemTestModal({
  workflowId,
  workflowTitle,
  workflowGoal,
  steps,
  isOpen,
  onClose,
  onRunComplete,
  onNavigateToRuns,
}: WorkflowSystemTestModalProps) {
  const [activeInputMode, setActiveInputMode] = useState<"visual" | "json">("visual");
  const [activeResultTab, setActiveResultTab] = useState<"final" | "steps" | "console" | "artifacts" | "raw">("final");
  const [selectedStepIndex, setSelectedStepIndex] = useState<number>(0);

  // Form Inputs state
  const [formInputs, setFormInputs] = useState<Record<string, string>>({});
  const [jsonInputs, setJsonInputs] = useState<string>('{\n  "query": "Sample workflow execution query"\n}');

  // Custom key-value additions
  const [customKey, setCustomKey] = useState("");
  const [customVal, setCustomVal] = useState("");

  // Test File Attachments state
  const [attachedArtifacts, setAttachedArtifacts] = useState<TestAttachedArtifact[]>([]);
  const [showArtifactPicker, setShowArtifactPicker] = useState(false);
  const [availableWorkspaceArtifacts, setAvailableWorkspaceArtifacts] = useState<TestAttachedArtifact[]>([]);
  const [artifactSearchQuery, setArtifactSearchQuery] = useState("");
  const [isLoadingArtifacts, setIsLoadingArtifacts] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Execution & Live Telemetry state
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState<WorkflowRun | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Real-time progress tracking
  const [stepStatuses, setStepStatuses] = useState<Record<string, "pending" | "running" | "completed" | "failed">>({});
  const [stepMetrics, setStepMetrics] = useState<
    Record<
      string,
      {
        duration_ms?: number;
        tokens_used?: number;
        tool_calls?: Array<Record<string, unknown>>;
        output_preview?: string;
        step_name?: string;
        agent_id?: string;
      }
    >
  >({});
  const [activeStepId, setActiveStepId] = useState<string | null>(null);
  const [completedStepsCount, setCompletedStepsCount] = useState<number>(0);
  const [elapsedMs, setElapsedMs] = useState<number>(0);
  const [consoleLogs, setConsoleLogs] = useState<ConsoleLogEntry[]>([]);
  const [autoScrollLogs, setAutoScrollLogs] = useState(true);
  const consoleBottomRef = useRef<HTMLDivElement>(null);

  // Discover all unique inputs.<varName> referenced in any step of the workflow
  const discoveredInputVars = useMemo(() => {
    const vars: string[] = [];
    const regex = /\{\{\s*inputs\.([\w\.\-]+)\s*\}\}/g;

    steps.forEach((step) => {
      if (!step.instructions) return;
      const matches = Array.from(step.instructions.matchAll(regex)).map((m) => m[1]);
      matches.forEach((v) => {
        if (!vars.includes(v) && v !== "attached_artifacts") vars.push(v);
      });
    });

    return vars;
  }, [steps]);

  // Initialize inputs on open
  useEffect(() => {
    if (!isOpen) return;

    const initial: Record<string, string> = {};
    if (discoveredInputVars.length > 0) {
      discoveredInputVars.forEach((v) => {
        initial[v] = `Test input for ${v}`;
      });
    } else {
      initial["query"] = workflowGoal || "Sample pipeline test task";
    }

    setFormInputs(initial);
    setJsonInputs(JSON.stringify(initial, null, 2));
    setRunResult(null);
    setErrorMessage(null);
    setIsRunning(false);
    setCompletedStepsCount(0);
    setActiveStepId(null);
    setElapsedMs(0);
    setConsoleLogs([]);

    const initialStatuses: Record<string, "pending" | "running" | "completed" | "failed"> = {};
    steps.forEach((s) => {
      initialStatuses[s.id] = "pending";
    });
    setStepStatuses(initialStatuses);
    setStepMetrics({});
  }, [isOpen, discoveredInputVars, workflowGoal, steps]);

  // Stopwatch timer during execution
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isRunning) {
      const start = Date.now();
      interval = setInterval(() => {
        setElapsedMs(Date.now() - start);
      }, 100);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning]);

  // Auto-scroll console logs
  useEffect(() => {
    if (autoScrollLogs && consoleBottomRef.current) {
      consoleBottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [consoleLogs, autoScrollLogs]);

  // Load available workspace artifacts when picker opens
  useEffect(() => {
    if (!showArtifactPicker) return;

    const fetchWorkspaceArtifacts = async () => {
      setIsLoadingArtifacts(true);
      const list: TestAttachedArtifact[] = [];

      // 1. From local storage
      try {
        const rawLocal = localStorage.getItem("swarm_local_artifacts");
        if (rawLocal) {
          const parsed = JSON.parse(rawLocal);
          if (Array.isArray(parsed)) {
            parsed.forEach((item) => {
              if (item && item.id) list.push(item);
            });
          }
        }
      } catch {
        // ignore
      }

      // 2. From backend API
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const authHeaders = await getAuthHeaders();
        const res = await fetch(`${apiUrl}/api/artifacts`, { headers: authHeaders });
        if (res.ok) {
          const backendList = await res.json();
          if (Array.isArray(backendList)) {
            const seen = new Set(list.map((a) => a.id));
            backendList.forEach((b) => {
              if (b && b.id && !seen.has(b.id)) {
                list.push({
                  id: b.id,
                  filename: b.filename || b.title || "artifact",
                  name: b.title || b.filename || "artifact",
                  type: b.type || "txt",
                  content: b.content || "",
                  mime_type: b.mime_type || "text/plain",
                  role: b.type === "spreadsheet" ? "source" : b.type === "template" ? "template" : "reference",
                  size_bytes: b.size_bytes || (b.content ? b.content.length : 0),
                  source_title: b.title,
                });
                seen.add(b.id);
              }
            });
          }
        }
      } catch {
        // ignore
      }

      setAvailableWorkspaceArtifacts(list);
      setIsLoadingArtifacts(false);
    };

    fetchWorkspaceArtifacts();
  }, [showArtifactPicker]);

  const handleInputChange = (key: string, value: string) => {
    const updated = { ...formInputs, [key]: value };
    setFormInputs(updated);
    setJsonInputs(JSON.stringify(updated, null, 2));
  };

  const handleAddCustomInput = () => {
    const trimmedKey = customKey.trim();
    if (!trimmedKey) return;
    const updated = { ...formInputs, [trimmedKey]: customVal };
    setFormInputs(updated);
    setJsonInputs(JSON.stringify(updated, null, 2));
    setCustomKey("");
    setCustomVal("");
  };

  const handleRemoveInput = (key: string) => {
    const copy = { ...formInputs };
    delete copy[key];
    setFormInputs(copy);
    setJsonInputs(JSON.stringify(copy, null, 2));
  };

  // Local file upload handler
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    Array.from(files).forEach((file) => {
      const isText =
        file.name.endsWith(".txt") ||
        file.name.endsWith(".md") ||
        file.name.endsWith(".json") ||
        file.name.endsWith(".csv") ||
        file.name.endsWith(".py") ||
        file.type.startsWith("text/");

      const reader = new FileReader();
      if (isText) {
        reader.onload = () => {
          const text = (reader.result as string) || "";
          const newArt: TestAttachedArtifact = {
            id: `test-file-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
            filename: file.name,
            name: file.name,
            type: file.name.split(".").pop() || "txt",
            content: text,
            is_base64: false,
            mime_type: file.type || "text/plain",
            size_bytes: file.size,
            role: file.name.toLowerCase().includes("template")
              ? "template"
              : file.name.toLowerCase().includes("data") || file.name.endsWith(".csv")
              ? "source"
              : "reference",
          };
          setAttachedArtifacts((prev) => [...prev, newArt]);
        };
        reader.readAsText(file);
      } else {
        reader.onload = () => {
          const dataUrl = (reader.result as string) || "";
          const newArt: TestAttachedArtifact = {
            id: `test-file-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
            filename: file.name,
            name: file.name,
            type: file.name.split(".").pop() || "bin",
            content: dataUrl,
            is_base64: true,
            mime_type: file.type || "application/octet-stream",
            size_bytes: file.size,
            role: file.name.endsWith(".xlsx") || file.name.endsWith(".xls")
              ? "source"
              : file.name.toLowerCase().includes("template")
              ? "template"
              : "reference",
          };
          setAttachedArtifacts((prev) => [...prev, newArt]);
        };
        reader.readAsDataURL(file);
      }
    });

    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleRemoveArtifact = (id: string) => {
    setAttachedArtifacts((prev) => prev.filter((a) => a.id !== id));
  };

  const handleUpdateArtifactRole = (id: string, role: string) => {
    setAttachedArtifacts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, role } : a))
    );
  };

  const handleSelectWorkspaceArtifact = (art: TestAttachedArtifact) => {
    if (!attachedArtifacts.some((a) => a.id === art.id)) {
      setAttachedArtifacts((prev) => [...prev, art]);
    }
    setShowArtifactPicker(false);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "0 KB";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (filename: string) => {
    const lower = filename.toLowerCase();
    if (lower.endsWith(".xlsx") || lower.endsWith(".xls") || lower.endsWith(".csv")) {
      return <FileSpreadsheet size={13} className="text-emerald-400" />;
    }
    if (lower.endsWith(".py") || lower.endsWith(".json") || lower.endsWith(".js") || lower.endsWith(".ts")) {
      return <FileCode size={13} className="text-amber-400" />;
    }
    return <FileText size={13} className="text-linear-primary" />;
  };

  const formatElapsed = (ms: number) => {
    const secs = Math.floor(ms / 1000);
    const tenths = Math.floor((ms % 1000) / 100);
    const mins = Math.floor(secs / 60);
    const remSecs = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${remSecs.toString().padStart(2, "0")}.${tenths}`;
  };

  // Execute system test with real-time SSE telemetry
  const handleExecuteSystemTest = async () => {
    setIsRunning(true);
    setRunResult(null);
    setErrorMessage(null);
    setCompletedStepsCount(0);
    setActiveStepId(null);
    setElapsedMs(0);

    const initialStatuses: Record<string, "pending" | "running" | "completed" | "failed"> = {};
    steps.forEach((s) => {
      initialStatuses[s.id] = "pending";
    });
    setStepStatuses(initialStatuses);
    setStepMetrics({});

    const startTimeStr = new Date().toLocaleTimeString();
    setConsoleLogs([
      {
        id: `${Date.now()}-init`,
        timestamp: startTimeStr,
        level: "info",
        message: `🚀 Initiating system test pipeline (${steps.length} steps, ${attachedArtifacts.length} attached test files)...`,
      },
    ]);

    let parsedInputs: Record<string, unknown> = {};
    if (activeInputMode === "visual") {
      parsedInputs = { ...formInputs };
    } else {
      try {
        parsedInputs = JSON.parse(jsonInputs);
      } catch {
        setErrorMessage("Invalid JSON in Inputs. Please check syntax.");
        setIsRunning(false);
        return;
      }
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const authHeaders = await getAuthHeaders();

    const payload = {
      inputs: parsedInputs,
      attached_artifacts: attachedArtifacts,
    };

    try {
      const res = await fetch(`${apiUrl}/api/workflows/${workflowId}/run-stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok || !res.body) {
        // Fallback to unary /run if /run-stream isn't supported in current environment
        console.warn("SSE stream unavailable, falling back to standard execution.");
        const fallbackRes = await fetch(`${apiUrl}/api/workflows/${workflowId}/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeaders },
          body: JSON.stringify(payload),
        });
        if (!fallbackRes.ok) {
          const errJson = await fallbackRes.json().catch(() => ({}));
          throw new Error(errJson.detail || "System test execution failed.");
        }
        const data: WorkflowRun = await fallbackRes.json();
        setRunResult(data);
        setCompletedStepsCount(steps.length);
        steps.forEach((s) => {
          setStepStatuses((prev) => ({ ...prev, [s.id]: "completed" }));
        });
        setActiveResultTab("final");
        if (onRunComplete) onRunComplete();
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const jsonStr = trimmed.replace(/^data:\s*/, "");
          if (!jsonStr) continue;

          try {
            const evt = JSON.parse(jsonStr);
            const timeStr = new Date().toLocaleTimeString();

            if (evt.type === "pipeline_start") {
              setConsoleLogs((prev) => [
                ...prev,
                {
                  id: `${Date.now()}-${Math.random()}`,
                  timestamp: timeStr,
                  level: "info",
                  message: `📋 Pipeline queued: ${evt.total_steps} steps topologically ordered.`,
                },
              ]);
            } else if (evt.type === "step_start") {
              const sId = evt.step_id;
              setActiveStepId(sId);
              setStepStatuses((prev) => ({ ...prev, [sId]: "running" }));
              const matchingIdx = steps.findIndex((s) => s.id === sId);
              if (matchingIdx !== -1) setSelectedStepIndex(matchingIdx);

              setConsoleLogs((prev) => [
                ...prev,
                {
                  id: `${Date.now()}-${Math.random()}`,
                  timestamp: timeStr,
                  level: "info",
                  message: `▶️ Step ${evt.step_index + 1}/${steps.length} [${evt.step_name || sId}] started with agent @${evt.agent_id} (${evt.model || "default"}).`,
                },
              ]);
            } else if (evt.type === "step_completed") {
              const sId = evt.step_id;
              setCompletedStepsCount((c) => c + 1);
              setStepStatuses((prev) => ({ ...prev, [sId]: "completed" }));
              setStepMetrics((prev) => ({
                ...prev,
                [sId]: {
                  duration_ms: evt.duration_ms,
                  tokens_used: evt.tokens_used,
                  tool_calls: evt.tool_calls || [],
                  output_preview: evt.output_preview,
                  step_name: evt.step_name,
                  agent_id: evt.agent_id,
                },
              }));
              const toolStr = evt.tool_calls?.length ? ` · ${evt.tool_calls.length} tool(s)` : "";
              setConsoleLogs((prev) => [
                ...prev,
                {
                  id: `${Date.now()}-${Math.random()}`,
                  timestamp: timeStr,
                  level: "success",
                  message: `✅ Step [${evt.step_name || sId}] completed in ${evt.duration_ms}ms (${evt.tokens_used} tokens${toolStr}).`,
                },
              ]);
            } else if (evt.type === "step_failed") {
              const sId = evt.step_id;
              setStepStatuses((prev) => ({ ...prev, [sId]: "failed" }));
              setConsoleLogs((prev) => [
                ...prev,
                {
                  id: `${Date.now()}-${Math.random()}`,
                  timestamp: timeStr,
                  level: "error",
                  message: `❌ Step [${sId}] failed: ${evt.error}`,
                },
              ]);
            } else if (evt.type === "pipeline_complete") {
              const finalRun = evt.run as WorkflowRun;
              setRunResult(finalRun);
              setActiveStepId(null);
              setCompletedStepsCount(steps.length);
              setConsoleLogs((prev) => [
                ...prev,
                {
                  id: `${Date.now()}-${Math.random()}`,
                  timestamp: timeStr,
                  level: "success",
                  message: `🎉 Pipeline completed in ${finalRun.duration_ms}ms! Status: ${finalRun.status.toUpperCase()} (${finalRun.total_tokens} tokens total).`,
                },
              ]);
              setActiveResultTab("final");
              if (onRunComplete) onRunComplete();
            } else if (evt.type === "error") {
              setErrorMessage(evt.error || "Execution error");
              setConsoleLogs((prev) => [
                ...prev,
                {
                  id: `${Date.now()}-${Math.random()}`,
                  timestamp: timeStr,
                  level: "error",
                  message: `💥 Pipeline error: ${evt.error}`,
                },
              ]);
            }
          } catch (parseErr) {
            console.warn("SSE json parse error:", parseErr);
          }
        }
      }
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "System execution test failed.");
    } finally {
      setIsRunning(false);
    }
  };

  const handleCopyOutput = () => {
    if (!runResult?.output_data) return;
    const text =
      typeof runResult.output_data.final_result === "string"
        ? runResult.output_data.final_result
        : JSON.stringify(runResult.output_data, null, 2);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyLogs = () => {
    const fullLogs = consoleLogs
      .map((l) => `[${l.timestamp}] [${l.level.toUpperCase()}] ${l.message}`)
      .join("\n");
    navigator.clipboard.writeText(fullLogs);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Active step inspection details
  const targetStepDef = steps[selectedStepIndex] || null;
  const activeStepRun: WorkflowStepRun | null = useMemo(() => {
    if (!targetStepDef) return null;
    if (runResult?.step_runs) {
      const match = runResult.step_runs.find((sr) => sr.step_id === targetStepDef.id);
      if (match) return match;
    }
    // Synthesize partial telemetry from real-time events if runResult not yet finished
    const liveMetric = stepMetrics[targetStepDef.id];
    if (liveMetric) {
      return {
        id: `live-${targetStepDef.id}`,
        run_id: "current",
        step_id: targetStepDef.id,
        step_name: targetStepDef.name,
        step_index: selectedStepIndex,
        agent_id: targetStepDef.agent_id,
        status: stepStatuses[targetStepDef.id] || "pending",
        prompt_rendered: targetStepDef.instructions,
        input_data: formInputs,
        output_data: { text: liveMetric.output_preview },
        tool_calls: liveMetric.tool_calls || [],
        tokens_used: liveMetric.tokens_used || 0,
        duration_ms: liveMetric.duration_ms || 0,
        resources: targetStepDef.resources || [],
      } as WorkflowStepRun;
    }
    return null;
  }, [targetStepDef, runResult, stepMetrics, stepStatuses, selectedStepIndex, formInputs]);

  const progressPercent = steps.length > 0 ? Math.round((completedStepsCount / steps.length) * 100) : 0;
  const activeStepDef = steps.find((s) => s.id === activeStepId) || null;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/75 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-canvas border border-hairline rounded-xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-5 py-3 border-b border-hairline flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0 bg-surface-1/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-surface-1 border border-hairline text-linear-primary flex items-center justify-center shadow-xs">
              <Layers size={16} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-semibold text-ink tracking-tight">
                  System Test: {workflowTitle || "Workflow Execution"}
                </h3>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-xs bg-surface-2 text-ink-subtle border border-hairline">
                  {steps.length} Steps DAG
                </span>
                {isRunning && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-linear-primary/10 text-linear-primary border border-linear-primary/30 animate-pulse">
                    <Loader2 size={10} className="animate-spin" /> Live Running
                  </span>
                )}
              </div>
              <p className="text-[11px] text-ink-subtle truncate max-w-sm sm:max-w-lg font-mono">
                Goal: {workflowGoal || "Execute multi-agent workflow"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Visual vs JSON toggle */}
            <div className="flex items-center p-0.5 rounded-pill bg-surface-1 border border-hairline text-[11px]">
              <button
                type="button"
                onClick={() => setActiveInputMode("visual")}
                className={`flex items-center gap-1 px-2.5 py-0.5 rounded-pill font-medium transition-colors cursor-pointer ${
                  activeInputMode === "visual"
                    ? "bg-surface-2 text-ink border border-hairline-strong shadow-xs"
                    : "text-ink-subtle hover:text-ink"
                }`}
              >
                <SlidersHorizontal size={11} />
                <span>Visual Inputs</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveInputMode("json")}
                className={`flex items-center gap-1 px-2.5 py-0.5 rounded-pill font-medium transition-colors cursor-pointer ${
                  activeInputMode === "json"
                    ? "bg-surface-2 text-ink border border-hairline-strong shadow-xs"
                    : "text-ink-subtle hover:text-ink"
                }`}
              >
                <Code size={11} />
                <span>JSON</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors border border-hairline cursor-pointer"
              title="Close modal"
            >
              <X size={14} />
            </button>
          </div>
        </div>

        {/* Live Execution Progress Bar (Shown while running or when completed) */}
        {(isRunning || completedStepsCount > 0) && (
          <div className="px-5 py-2.5 bg-surface-2/40 border-b border-hairline space-y-1.5 shrink-0">
            <div className="flex items-center justify-between text-[11px] font-mono">
              <div className="flex items-center gap-2 text-ink">
                {isRunning ? (
                  <>
                    <Loader2 size={12} className="animate-spin text-linear-primary" />
                    <span>
                      Executing Step {Math.min(completedStepsCount + 1, steps.length)} of {steps.length}:{" "}
                      <strong className="text-linear-primary">
                        {activeStepDef?.name || activeStepId || "Processing"}
                      </strong>{" "}
                      {activeStepDef?.agent_id ? `(@${activeStepDef.agent_id})` : ""}
                    </span>
                  </>
                ) : runResult?.status === "failed" ? (
                  <>
                    <XCircle size={12} className="text-red-400" />
                    <span className="text-red-400 font-semibold">
                      Pipeline execution stopped due to step failure.
                    </span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={12} className="text-emerald-400" />
                    <span className="text-emerald-400 font-semibold">
                      Pipeline Execution Completed Successfully!
                    </span>
                  </>
                )}
              </div>

              <div className="flex items-center gap-2 text-ink-subtle">
                <span className="flex items-center gap-1">
                  <Clock size={11} />
                  <span>{formatElapsed(runResult?.duration_ms || elapsedMs)}</span>
                </span>
                <span>·</span>
                <span className="font-semibold text-ink">{progressPercent}%</span>
              </div>
            </div>

            {/* Progress Bar Track */}
            <div className="w-full h-1.5 bg-surface-3 rounded-full overflow-hidden border border-hairline">
              <div
                className={`h-full transition-all duration-300 ${
                  runResult?.status === "failed"
                    ? "bg-red-400"
                    : isRunning
                    ? "bg-linear-primary"
                    : "bg-emerald-400"
                }`}
                style={{ width: `${Math.min(progressPercent, 100)}%` }}
              />
            </div>
          </div>
        )}

        {/* Scrollable Body */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1 text-xs">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono flex items-center gap-2">
              <AlertTriangle size={14} className="shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Test Inputs & File Attachments Section */}
          <div className="p-3.5 rounded-lg bg-surface-1 border border-hairline space-y-3.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-semibold text-ink flex items-center gap-1.5">
                <SlidersHorizontal size={12} className="text-linear-primary" />
                Custom Workflow Test Inputs
              </span>
              <span className="text-[10px] text-ink-subtle font-mono">
                {Object.keys(formInputs).length} variable(s) · {attachedArtifacts.length} test file(s)
              </span>
            </div>

            {/* Key/Value Inputs */}
            {activeInputMode === "visual" ? (
              <div className="space-y-2.5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {Object.entries(formInputs).map(([k, v]) => (
                    <div key={k} className="space-y-1">
                      <div className="flex items-center justify-between text-[10px] font-mono text-ink-subtle">
                        <span>
                          {"{{inputs."}<span className="text-ink font-semibold">{k}</span>{"}}"}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleRemoveInput(k)}
                          className="hover:text-red-400 transition cursor-pointer"
                          title="Remove variable"
                        >
                          <X size={10} />
                        </button>
                      </div>
                      <input
                        type="text"
                        value={v}
                        onChange={(e) => handleInputChange(k, e.target.value)}
                        placeholder={`Input value for ${k}`}
                        className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md px-2.5 py-1.5 text-ink focus:outline-hidden focus:border-linear-primary transition-colors"
                      />
                    </div>
                  ))}
                </div>

                {/* Add Custom Input Key/Value Row */}
                <div className="pt-2 border-t border-hairline flex flex-wrap items-center gap-2">
                  <input
                    type="text"
                    value={customKey}
                    onChange={(e) => setCustomKey(e.target.value)}
                    placeholder="New variable (e.g. topic)"
                    className="text-xs font-mono bg-canvas border border-hairline rounded-md px-2.5 py-1 text-ink focus:outline-hidden focus:border-linear-primary max-w-[180px]"
                  />
                  <input
                    type="text"
                    value={customVal}
                    onChange={(e) => setCustomVal(e.target.value)}
                    placeholder="Value"
                    className="text-xs font-mono bg-canvas border border-hairline rounded-md px-2.5 py-1 text-ink focus:outline-hidden focus:border-linear-primary flex-1 min-w-[140px]"
                    onKeyDown={(e) => e.key === "Enter" && handleAddCustomInput()}
                  />
                  <button
                    type="button"
                    onClick={handleAddCustomInput}
                    disabled={!customKey.trim()}
                    className="px-2.5 py-1 text-xs font-medium bg-surface-2 hover:bg-surface-3 border border-hairline text-ink rounded-md transition-colors disabled:opacity-40 cursor-pointer"
                  >
                    + Add Field
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <textarea
                  rows={4}
                  value={jsonInputs}
                  onChange={(e) => setJsonInputs(e.target.value)}
                  className="w-full text-xs font-mono bg-canvas border border-hairline rounded-md p-2.5 text-ink focus:outline-hidden focus:border-linear-primary"
                />
              </div>
            )}

            {/* Attached Test Files & Datasets Sub-Section */}
            <div className="pt-2.5 border-t border-hairline space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="font-medium text-ink flex items-center gap-1.5">
                  <Paperclip size={12} className="text-linear-primary" />
                  Attached Test Files & Datasets ({attachedArtifacts.length})
                </span>

                <div className="flex items-center gap-2">
                  {/* Hidden file input */}
                  <input
                    type="file"
                    ref={fileInputRef}
                    multiple
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="px-2 py-0.5 text-[11px] font-medium bg-surface-2 hover:bg-surface-3 border border-hairline text-ink rounded-md transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <Upload size={11} />
                    <span>Upload File</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setShowArtifactPicker(true)}
                    className="px-2 py-0.5 text-[11px] font-medium bg-surface-2 hover:bg-surface-3 border border-hairline text-ink rounded-md transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <FolderArchive size={11} />
                    <span>From Artifacts Studio</span>
                  </button>
                </div>
              </div>

              {/* List of Attached Test Files */}
              {attachedArtifacts.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                  {attachedArtifacts.map((art) => (
                    <div
                      key={art.id}
                      className="p-2 rounded-md bg-surface-2/60 border border-hairline flex items-center justify-between gap-2 text-[11px] font-mono"
                    >
                      <div className="flex items-center gap-1.5 min-w-0">
                        {getFileIcon(art.filename)}
                        <span className="truncate text-ink font-medium" title={art.filename}>
                          {art.filename}
                        </span>
                        <span className="text-[9px] text-ink-subtle shrink-0">
                          ({formatFileSize(art.size_bytes)})
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0">
                        {/* Role selector dropdown */}
                        <select
                          value={art.role || "reference"}
                          onChange={(e) => handleUpdateArtifactRole(art.id, e.target.value)}
                          className="text-[9px] font-mono px-1 py-0.5 rounded bg-surface-3 border border-hairline text-linear-primary focus:outline-hidden"
                          title="Assign semantic role in pipeline"
                        >
                          <option value="reference">Reference</option>
                          <option value="source">Source Data</option>
                          <option value="template">Template</option>
                        </select>

                        <button
                          type="button"
                          onClick={() => handleRemoveArtifact(art.id)}
                          className="p-0.5 text-ink-subtle hover:text-red-400 transition-colors cursor-pointer"
                          title="Remove file"
                        >
                          <X size={11} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 rounded-md border border-dashed border-hairline text-center text-ink-subtle text-[11px]">
                  No test files attached. Click <strong className="text-ink">Upload File</strong> or{" "}
                  <strong className="text-ink">From Artifacts Studio</strong> to test pipeline with sample PDFs, spreadsheets, or report formats.
                </div>
              )}
            </div>
          </div>

          {/* Interactive DAG Execution Sequence Bar */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-medium text-ink-subtle flex items-center gap-1.5">
                <Activity size={12} className="text-linear-primary" /> Execution Flow ({steps.length} Steps)
              </span>
              <span className="text-[10px] text-ink-subtle font-mono">
                Click any step to inspect live traces & debug
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-1.5">
              {steps.map((st, i) => {
                const status = stepStatuses[st.id] || "pending";
                const isSelected = selectedStepIndex === i;
                const metric = stepMetrics[st.id];

                return (
                  <div
                    key={st.id}
                    onClick={() => {
                      setSelectedStepIndex(i);
                      setActiveResultTab("steps");
                    }}
                    className={`flex items-center gap-1.5 text-[11px] font-mono px-2 py-1 rounded-md border transition-all cursor-pointer ${
                      isSelected
                        ? "bg-surface-2 text-ink border-linear-primary ring-1 ring-linear-primary/40 shadow-xs"
                        : "bg-surface-1 text-ink-subtle border-hairline hover:text-ink hover:bg-surface-2"
                    }`}
                  >
                    {/* Status Icon */}
                    {status === "running" ? (
                      <Loader2 size={11} className="text-linear-primary animate-spin" />
                    ) : status === "completed" ? (
                      <CheckCircle2 size={11} className="text-emerald-400" />
                    ) : status === "failed" ? (
                      <XCircle size={11} className="text-red-400" />
                    ) : (
                      <Bot size={11} className="text-ink-subtle" />
                    )}

                    <span className="font-medium text-ink truncate max-w-[130px]">{st.name || st.id}</span>
                    <span className="text-[9px] text-ink-subtle">(@{st.agent_id})</span>
                    {metric?.duration_ms ? (
                      <span className="text-[8px] text-emerald-400/80 font-mono">
                        {metric.duration_ms}ms
                      </span>
                    ) : null}

                    {i < steps.length - 1 && (
                      <ChevronRight size={11} className="text-ink-subtle/50 ml-0.5" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Results, Debug Console & Step Inspector Container */}
          <div className="p-3.5 rounded-lg bg-surface-1 border border-hairline space-y-3 mt-2">
            {/* Navigation Tabs */}
            <div className="flex items-center justify-between pb-2 border-b border-hairline flex-wrap gap-2 text-[11px]">
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setActiveResultTab("final")}
                  className={`px-2.5 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 cursor-pointer ${
                    activeResultTab === "final"
                      ? "bg-surface-2 text-ink border border-hairline shadow-xs"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  <FileText size={12} />
                  <span>Final Output</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveResultTab("steps")}
                  className={`px-2.5 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 cursor-pointer ${
                    activeResultTab === "steps"
                      ? "bg-surface-2 text-ink border border-hairline shadow-xs"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  <Bot size={12} className="text-linear-primary" />
                  <span>Step Inspector ({steps.length})</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveResultTab("console")}
                  className={`px-2.5 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 cursor-pointer ${
                    activeResultTab === "console"
                      ? "bg-surface-2 text-ink border border-hairline shadow-xs"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  <Terminal size={12} className="text-amber-400" />
                  <span>Debug Console ({consoleLogs.length})</span>
                  {isRunning && (
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping ml-0.5" />
                  )}
                </button>

                {Boolean(runResult?.artifacts && runResult.artifacts.length > 0) && (
                  <button
                    type="button"
                    onClick={() => setActiveResultTab("artifacts")}
                    className={`px-2.5 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 cursor-pointer ${
                      activeResultTab === "artifacts"
                        ? "bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-xs"
                        : "text-purple-400 hover:text-purple-300"
                    }`}
                  >
                    <Sparkles size={12} />
                    <span>Artifacts ({runResult?.artifacts?.length || 0})</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => setActiveResultTab("raw")}
                  className={`px-2.5 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 cursor-pointer ${
                    activeResultTab === "raw"
                      ? "bg-surface-2 text-ink border border-hairline shadow-xs"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  <Code size={12} />
                  <span>Raw Payload</span>
                </button>
              </div>

              {/* Quick Actions */}
              <div className="flex items-center gap-2">
                {activeResultTab === "console" && (
                  <>
                    <label className="flex items-center gap-1 text-[10px] text-ink-subtle cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={autoScrollLogs}
                        onChange={(e) => setAutoScrollLogs(e.target.checked)}
                        className="rounded bg-surface-2 border-hairline"
                      />
                      <span>Auto-scroll</span>
                    </label>
                    <button
                      type="button"
                      onClick={handleCopyLogs}
                      className="flex items-center gap-1 text-[10px] text-ink-subtle hover:text-ink bg-surface-2 px-2 py-0.5 rounded-md border border-hairline transition-colors cursor-pointer"
                    >
                      {copied ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                      <span>{copied ? "Copied" : "Copy Logs"}</span>
                    </button>
                  </>
                )}

                {activeResultTab === "final" && runResult?.output_data && (
                  <button
                    type="button"
                    onClick={handleCopyOutput}
                    className="flex items-center gap-1 text-[10px] text-ink-subtle hover:text-ink bg-surface-2 px-2 py-0.5 rounded-md border border-hairline transition-colors cursor-pointer"
                  >
                    {copied ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                    <span>{copied ? "Copied" : "Copy Output"}</span>
                  </button>
                )}

                {onNavigateToRuns && (
                  <button
                    type="button"
                    onClick={() => {
                      onClose();
                      onNavigateToRuns();
                    }}
                    className="text-[10px] text-linear-primary hover:underline font-mono inline-flex items-center gap-0.5"
                  >
                    <span>Runs History</span>
                    <ExternalLink size={10} />
                  </button>
                )}
              </div>
            </div>

            {/* TAB 1: Final Output Content */}
            {activeResultTab === "final" && (
              <div className="space-y-2">
                {runResult?.output_data ? (
                  <pre className="font-mono text-[11px] text-ink leading-relaxed bg-canvas p-3 rounded-md border border-hairline whitespace-pre-wrap max-h-72 overflow-y-auto">
                    {typeof runResult.output_data.final_result === "string"
                      ? runResult.output_data.final_result
                      : JSON.stringify(runResult.output_data, null, 2)}
                  </pre>
                ) : isRunning ? (
                  <div className="py-12 text-center space-y-2 text-ink-subtle">
                    <Loader2 size={24} className="animate-spin text-linear-primary mx-auto" />
                    <p className="text-xs">Pipeline executing in real-time... Observe live traces in Debug Console or Step Inspector.</p>
                  </div>
                ) : (
                  <p className="text-ink-subtle py-6 text-center text-xs">
                    Click <strong>Execute System Test</strong> below to run the pipeline and view output here.
                  </p>
                )}
              </div>
            )}

            {/* TAB 2: Deep Step Inspector */}
            {activeResultTab === "steps" && (
              <div className="space-y-3">
                {/* Step Selector Horizontal Strip */}
                <div className="flex flex-wrap items-center gap-1 pb-2 border-b border-hairline">
                  {steps.map((st, idx) => {
                    const stStatus = stepStatuses[st.id] || "pending";
                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setSelectedStepIndex(idx)}
                        className={`px-2 py-0.5 rounded-md text-[10px] font-mono border transition-all flex items-center gap-1 cursor-pointer ${
                          selectedStepIndex === idx
                            ? "bg-surface-2 text-ink border-linear-primary font-semibold shadow-xs"
                            : "bg-surface-1 text-ink-subtle border-hairline hover:text-ink"
                        }`}
                      >
                        {stStatus === "running" ? (
                          <Loader2 size={10} className="text-linear-primary animate-spin" />
                        ) : stStatus === "completed" ? (
                          <CheckCircle2 size={10} className="text-emerald-400" />
                        ) : stStatus === "failed" ? (
                          <XCircle size={10} className="text-red-400" />
                        ) : (
                          <Bot size={10} className="text-ink-subtle" />
                        )}
                        <span>{st.name || st.id}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Inspected Step Detail Card */}
                {targetStepDef ? (
                  <div className="p-3.5 rounded-md bg-canvas border border-hairline space-y-3 font-mono text-[11px]">
                    {/* Header */}
                    <div className="flex items-center justify-between pb-2 border-b border-hairline">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-ink text-xs">
                          {selectedStepIndex + 1}. {targetStepDef.name || targetStepDef.id}
                        </span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-surface-2 text-linear-primary border border-hairline uppercase font-bold">
                          @{targetStepDef.agent_id}
                        </span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-surface-3 text-ink-subtle border border-hairline">
                          {targetStepDef.step_type || "agent"}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-[10px] text-ink-subtle">
                        {activeStepRun?.duration_ms !== undefined && (
                          <span className="flex items-center gap-0.5 text-emerald-400 font-semibold">
                            <Clock size={10} /> {activeStepRun.duration_ms}ms
                          </span>
                        )}
                        {activeStepRun?.tokens_used !== undefined && activeStepRun.tokens_used > 0 && (
                          <span className="flex items-center gap-0.5">
                            <Zap size={10} className="text-linear-primary" /> {activeStepRun.tokens_used} tok
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Error Diagnostic Card (if failed) */}
                    {activeStepRun?.error && (
                      <div className="p-2.5 rounded bg-red-500/10 border border-red-500/30 text-red-400 space-y-1">
                        <div className="flex items-center gap-1.5 font-semibold text-xs">
                          <XCircle size={13} />
                          <span>Step Execution Failure</span>
                        </div>
                        <p className="text-[10px] whitespace-pre-wrap">{activeStepRun.error}</p>
                      </div>
                    )}

                    {/* Rendered Prompt Section */}
                    <div className="space-y-1">
                      <span className="text-[10px] uppercase text-ink-subtle font-semibold flex items-center justify-between">
                        <span>Interpolated Prompt:</span>
                        <button
                          type="button"
                          onClick={() => {
                            navigator.clipboard.writeText(
                              activeStepRun?.prompt_rendered || targetStepDef.instructions
                            );
                            setCopied(true);
                            setTimeout(() => setCopied(false), 2000);
                          }}
                          className="hover:text-ink text-[9px] flex items-center gap-1 cursor-pointer"
                        >
                          <Copy size={9} /> Copy Prompt
                        </button>
                      </span>
                      <pre className="p-2.5 rounded bg-surface-1 border border-hairline text-ink leading-relaxed whitespace-pre-wrap max-h-32 overflow-y-auto">
                        {activeStepRun?.prompt_rendered || targetStepDef.instructions}
                      </pre>
                    </div>

                    {/* Injected Knowledge & Step Resources Section */}
                    {Boolean(
                      activeStepRun?.system_instructions ||
                        (targetStepDef.resources && targetStepDef.resources.length > 0)
                    ) && (
                      <div className="space-y-1">
                        <span className="text-[10px] uppercase text-ink-subtle font-semibold flex items-center gap-1">
                          <Paperclip size={10} className="text-linear-primary" />
                          <span>Injected Knowledge & Step Resources:</span>
                        </span>
                        <pre className="p-2.5 rounded bg-surface-1 border border-hairline text-ink-subtle leading-relaxed whitespace-pre-wrap max-h-28 overflow-y-auto text-[10px]">
                          {activeStepRun?.system_instructions ||
                            JSON.stringify(targetStepDef.resources, null, 2)}
                        </pre>
                      </div>
                    )}

                    {/* Tool Invocations Section */}
                    {Boolean(activeStepRun?.tool_calls && activeStepRun.tool_calls.length > 0) && (
                      <div className="space-y-1">
                        <span className="text-[10px] uppercase text-ink-subtle font-semibold flex items-center gap-1">
                          <Wrench size={10} className="text-amber-400" />
                          <span>Tools Executed ({activeStepRun?.tool_calls?.length}):</span>
                        </span>
                        <div className="space-y-1.5">
                          {activeStepRun?.tool_calls?.map((tc, tIdx) => (
                            <div
                              key={tIdx}
                              className="p-2 rounded bg-surface-1 border border-hairline text-[10px] space-y-1"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-linear-primary">
                                  {tc.tool_name || tc.tool_id || "tool"}
                                </span>
                                <span className="text-ink-subtle font-mono text-[9px]">
                                  {tc.status || "executed"} {tc.duration_ms ? `(${tc.duration_ms}ms)` : ""}
                                </span>
                              </div>
                              {tc.stdout && (
                                <pre className="p-1 rounded bg-canvas text-ink-subtle text-[9px] whitespace-pre-wrap overflow-x-auto">
                                  {tc.stdout}
                                </pre>
                              )}
                              {tc.result !== undefined && (
                                <pre className="p-1 rounded bg-canvas text-ink-subtle text-[9px] whitespace-pre-wrap overflow-x-auto">
                                  {typeof tc.result === "string" ? tc.result : JSON.stringify(tc.result, null, 2)}
                                </pre>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Step Output Produced */}
                    <div className="space-y-1">
                      <span className="text-[10px] uppercase text-ink-subtle font-semibold">
                        Step Output Produced:
                      </span>
                      <pre className="p-2.5 rounded bg-surface-1 border border-hairline text-ink leading-relaxed whitespace-pre-wrap max-h-40 overflow-y-auto">
                        {activeStepRun?.output_data
                          ? typeof activeStepRun.output_data.text === "string"
                            ? activeStepRun.output_data.text
                            : JSON.stringify(activeStepRun.output_data, null, 2)
                          : "Pending step execution."}
                      </pre>
                    </div>
                  </div>
                ) : (
                  <p className="text-ink-subtle py-4 text-center">Select a step to inspect traces.</p>
                )}
              </div>
            )}

            {/* TAB 3: Real-Time Debug Console Log Stream */}
            {activeResultTab === "console" && (
              <div className="space-y-2">
                <div className="rounded-md bg-canvas border border-hairline p-3 font-mono text-[11px] leading-relaxed max-h-72 overflow-y-auto space-y-1.5 shadow-inner">
                  {consoleLogs.length > 0 ? (
                    consoleLogs.map((log) => {
                      const color =
                        log.level === "error"
                          ? "text-red-400"
                          : log.level === "success"
                          ? "text-emerald-400"
                          : log.level === "warn"
                          ? "text-amber-400"
                          : "text-ink";
                      return (
                        <div key={log.id} className="flex items-start gap-2">
                          <span className="text-ink-subtle select-none shrink-0 font-mono text-[10px]">
                            [{log.timestamp}]
                          </span>
                          <span className={`${color} break-all whitespace-pre-wrap`}>
                            {log.message}
                          </span>
                        </div>
                      );
                    })
                  ) : (
                    <p className="text-ink-subtle text-center py-8">
                      Console stream is idle. Start execution below to stream live telemetry.
                    </p>
                  )}
                  <div ref={consoleBottomRef} />
                </div>
              </div>
            )}

            {/* TAB 4: Generated Artifacts Viewer */}
            {activeResultTab === "artifacts" && (
              <div className="space-y-3 max-h-72 overflow-y-auto">
                {runResult?.artifacts?.map((art, aIdx) => (
                  <div
                    key={aIdx}
                    className="p-3 rounded-md bg-canvas border border-purple-500/30 space-y-2 font-mono text-[11px]"
                  >
                    <div className="flex items-center justify-between pb-1.5 border-b border-hairline">
                      <div className="flex items-center gap-2">
                        <span className="text-purple-400 font-semibold">{art.title}</span>
                        <span className="text-[9px] uppercase px-1.5 py-0.2 rounded-xs bg-purple-500/20 text-purple-300 border border-purple-500/40">
                          {art.type}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          navigator.clipboard.writeText(art.content);
                          setCopied(true);
                          setTimeout(() => setCopied(false), 2000);
                        }}
                        className="text-[10px] text-ink-subtle hover:text-ink px-1.5 py-0.5 rounded bg-surface-2 border border-hairline transition-colors flex items-center gap-1 cursor-pointer"
                      >
                        <Copy size={10} /> Copy Content
                      </button>
                    </div>
                    <pre className="p-2.5 rounded bg-surface-1 border border-hairline text-ink leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
                      {art.content}
                    </pre>
                  </div>
                ))}
              </div>
            )}

            {/* TAB 5: Raw Run JSON */}
            {activeResultTab === "raw" && (
              <pre className="font-mono text-[10px] text-ink-muted bg-canvas p-3 rounded-md border border-hairline overflow-x-auto max-h-60">
                {JSON.stringify(runResult, null, 2)}
              </pre>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="h-14 px-5 border-t border-hairline flex items-center justify-between bg-surface-1/60 shrink-0">
          <div className="text-[11px] text-ink-subtle font-mono">
            {isRunning ? (
              <span className="flex items-center gap-1.5 text-linear-primary font-medium animate-pulse">
                <Sparkles size={12} /> Pipeline executing in swarm backend ({formatElapsed(elapsedMs)})...
              </span>
            ) : runResult?.status === "completed" ? (
              <span className="text-emerald-400 flex items-center gap-1">
                <CheckCircle2 size={12} /> Test Run Completed in {runResult.duration_ms}ms
              </span>
            ) : (
              <span>Ready to test workflow DAG</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isRunning}
              className="px-3 py-1.5 text-xs text-ink-subtle hover:text-ink transition-colors cursor-pointer"
            >
              Close
            </button>
            <button
              type="button"
              disabled={isRunning}
              onClick={handleExecuteSystemTest}
              className="px-4 py-1.5 text-xs font-medium bg-linear-primary hover:bg-linear-hover text-white rounded-md transition-colors disabled:opacity-40 flex items-center gap-1.5 shadow-sm cursor-pointer active:scale-95"
            >
              {isRunning ? (
                <>
                  <Loader2 size={12} className="animate-spin" />
                  <span>Executing Pipeline...</span>
                </>
              ) : (
                <>
                  <Play size={12} className="fill-current" />
                  <span>Execute System Test</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Artifact Studio Picker Modal */}
      {showArtifactPicker && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs">
          <div className="bg-surface-1 border border-hairline rounded-xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
            <div className="px-4 py-3 border-b border-hairline flex items-center justify-between bg-surface-2/60">
              <div className="flex items-center gap-2">
                <FolderArchive size={15} className="text-linear-primary" />
                <h4 className="text-xs font-semibold text-ink">Attach from Workspace Artifacts Studio</h4>
              </div>
              <button
                type="button"
                onClick={() => setShowArtifactPicker(false)}
                className="p-1 rounded text-ink-subtle hover:text-ink hover:bg-surface-3 transition cursor-pointer"
              >
                <X size={14} />
              </button>
            </div>

            <div className="p-3 border-b border-hairline bg-surface-1">
              <div className="relative">
                <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-subtle" />
                <input
                  type="text"
                  value={artifactSearchQuery}
                  onChange={(e) => setArtifactSearchQuery(e.target.value)}
                  placeholder="Search artifacts by title or format..."
                  className="w-full pl-8 pr-3 py-1.5 text-xs bg-canvas border border-hairline rounded-md text-ink focus:outline-hidden focus:border-linear-primary font-mono"
                />
              </div>
            </div>

            <div className="p-3 overflow-y-auto space-y-1.5 flex-1 max-h-64">
              {isLoadingArtifacts ? (
                <div className="py-8 text-center text-ink-subtle text-xs">
                  <Loader2 size={16} className="animate-spin mx-auto mb-1 text-linear-primary" />
                  <span>Loading workspace artifacts...</span>
                </div>
              ) : availableWorkspaceArtifacts.length === 0 ? (
                <div className="py-8 text-center text-ink-subtle text-xs">
                  No artifacts found in workspace.
                </div>
              ) : (
                availableWorkspaceArtifacts
                  .filter((art) =>
                    artifactSearchQuery
                      ? (art.filename || art.name || "").toLowerCase().includes(artifactSearchQuery.toLowerCase())
                      : true
                  )
                  .map((art) => {
                    const isAlreadyAttached = attachedArtifacts.some((a) => a.id === art.id);
                    return (
                      <div
                        key={art.id}
                        className="p-2.5 rounded-lg bg-surface-2/60 border border-hairline flex items-center justify-between gap-2 hover:bg-surface-3 transition-colors text-xs font-mono"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          {getFileIcon(art.filename)}
                          <div className="truncate">
                            <span className="font-medium text-ink block truncate">{art.filename || art.name}</span>
                            <span className="text-[10px] text-ink-subtle">
                              {art.type} · {formatFileSize(art.size_bytes)}
                            </span>
                          </div>
                        </div>

                        <button
                          type="button"
                          disabled={isAlreadyAttached}
                          onClick={() => handleSelectWorkspaceArtifact(art)}
                          className="px-2 py-1 text-[10px] font-medium rounded bg-linear-primary hover:bg-linear-hover text-white transition disabled:opacity-40 shrink-0 cursor-pointer"
                        >
                          {isAlreadyAttached ? "Attached" : "+ Add to Test"}
                        </button>
                      </div>
                    );
                  })
              )}
            </div>

            <div className="p-3 border-t border-hairline bg-surface-2/40 flex justify-end">
              <button
                type="button"
                onClick={() => setShowArtifactPicker(false)}
                className="px-3 py-1 text-xs text-ink-subtle hover:text-ink transition cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
