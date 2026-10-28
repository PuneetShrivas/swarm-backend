"use client";

import React, { useState } from "react";
import { ScriptTool } from "../types";
import { getAuthHeaders } from "@/lib/supabase";
import {
  Code2,
  Plus,
  Play,
  Trash2,
  Edit2,
  Check,
  AlertCircle,
  Clock,
  Terminal,
  Shield,
  FileCode,
} from "lucide-react";

interface ToolScriptEditorProps {
  tools: ScriptTool[];
  onRefreshTools: () => void;
  readOnly?: boolean;
}

const DEFAULT_PYTHON_TEMPLATE = `def execute(input_data: dict, context: dict) -> dict:
    """
    Standard interface for user-defined Python script tools.
    
    Args:
        input_data: Key-value arguments passed into this step.
        context: Execution state (goal, step_id, previous_outputs).
        
    Returns:
        JSON-serializable dictionary with tool execution results.
    """
    text = input_data.get("text", "")
    words = text.split()
    
    return {
        "word_count": len(words),
        "status": "success",
        "preview": text[:50]
    }
`;

export default function ToolScriptEditor({
  tools,
  onRefreshTools,
  readOnly = false,
}: ToolScriptEditorProps) {
  const [selectedTool, setSelectedTool] = useState<ScriptTool | null>(tools[0] || null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  // Form states
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [code, setCode] = useState(DEFAULT_PYTHON_TEMPLATE);
  const [isPublic, setIsPublic] = useState(false);

  // Test Runner states
  const [testInputJson, setTestInputJson] = useState('{\n  "text": "Hello world from autonomous multi-agent swarm!"\n}');
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [testResult, setTestResult] = useState<{
    status: string;
    result?: unknown;
    stdout?: string;
    duration_ms?: number;
    error?: string;
  } | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const startCreate = () => {
    setIsCreating(true);
    setIsEditing(false);
    setSelectedTool(null);
    setName("custom_text_processor");
    setDescription("Processes input text and returns structured metrics.");
    setCode(DEFAULT_PYTHON_TEMPLATE);
    setIsPublic(false);
    setErrorMessage(null);
    setTestResult(null);
  };

  const startEdit = (tool: ScriptTool) => {
    setSelectedTool(tool);
    setIsEditing(true);
    setIsCreating(false);
    setName(tool.name);
    setDescription(tool.description || "");
    setCode(tool.code);
    setIsPublic(tool.is_public);
    setErrorMessage(null);
    setTestResult(null);
  };

  const handleSave = async () => {
    if (readOnly) return;
    setErrorMessage(null);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    const payload = {
      name,
      description,
      code,
      is_public: isPublic,
      input_schema: {},
      output_schema: {},
    };

    try {
      const url = isCreating
        ? `${apiUrl}/api/workflow-tools`
        : `${apiUrl}/api/workflow-tools/${selectedTool?.id}`;
      const method = isCreating ? "POST" : "PUT";

      const authHeaders = await getAuthHeaders();
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to save tool.");
      }

      setIsEditing(false);
      setIsCreating(false);
      onRefreshTools();
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "An error occurred.");
    }
  };

  const handleDelete = async (toolId: string) => {
    if (readOnly || !confirm("Are you sure you want to delete this script tool?")) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const authHeaders = await getAuthHeaders();
      await fetch(`${apiUrl}/api/workflow-tools/${toolId}`, {
        method: "DELETE",
        headers: authHeaders,
      });
      if (selectedTool?.id === toolId) setSelectedTool(null);
      onRefreshTools();
    } catch (err) {
      console.error("Delete tool error:", err);
    }
  };

  const handleRunTest = async () => {
    if (!selectedTool && !code) return;
    setIsRunningTest(true);
    setTestResult(null);
    setErrorMessage(null);

    let parsedInput = {};
    try {
      parsedInput = JSON.parse(testInputJson);
    } catch {
      setErrorMessage("Invalid test input JSON. Please correct the format.");
      setIsRunningTest(false);
      return;
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      // If tool exists, test via endpoint; if drafting, save temporary or run endpoint
      if (selectedTool?.id) {
        const authHeaders = await getAuthHeaders();
        const res = await fetch(`${apiUrl}/api/workflow-tools/${selectedTool.id}/test`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...authHeaders,
          },
          body: JSON.stringify({ input_data: parsedInput, context: {} }),
        });
        const data = await res.json();
        setTestResult(data);
      } else {
        // Direct test by creating or testing
        setErrorMessage("Please save tool definition first to run sandboxed test.");
      }
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "Execution test failed.");
    } finally {
      setIsRunningTest(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[500px]">
      {/* Left List Column */}
      <div className="lg:col-span-4 space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-border">
          <div className="flex items-center gap-2">
            <Code2 size={16} className="text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Python Script Tools</h3>
          </div>
          {!readOnly && (
            <button
              onClick={startCreate}
              className="px-2.5 py-1 text-xs font-medium bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition flex items-center gap-1 shadow-subtle"
            >
              <Plus size={13} /> New Tool
            </button>
          )}
        </div>

        <div className="space-y-2 max-h-[550px] overflow-y-auto pr-1">
          {tools.length === 0 ? (
            <div className="p-6 text-center border border-dashed border-border rounded-xl bg-card/40">
              <FileCode className="w-8 h-8 text-muted-foreground opacity-50 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">No script tools in library.</p>
            </div>
          ) : (
            tools.map((t) => {
              const isSelected = selectedTool?.id === t.id && !isCreating;
              return (
                <div
                  key={t.id}
                  onClick={() => {
                    setSelectedTool(t);
                    setIsCreating(false);
                    setIsEditing(false);
                    setTestResult(null);
                  }}
                  className={`p-3.5 rounded-xl border text-left cursor-pointer transition ${
                    isSelected
                      ? "bg-primary/10 border-primary/40 shadow-subtle"
                      : "bg-card border-border/70 hover:border-border"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <span className="text-amber-500 font-mono text-sm">⚡</span> {t.name}
                    </span>
                    {t.is_public && (
                      <span className="text-[10px] px-1.5 py-0.2 bg-muted text-muted-foreground rounded">
                        Public
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-muted-foreground line-clamp-2 mt-1">
                    {t.description || "No description provided."}
                  </p>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Detail / Editor Column */}
      <div className="lg:col-span-8 p-5 rounded-2xl bg-card border border-border/80 shadow-subtle space-y-4">
        {isCreating || isEditing ? (
          /* Editor Form */
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h4 className="text-sm font-semibold text-foreground">
                {isCreating ? "Create New Python Tool" : `Edit Tool: ${name}`}
              </h4>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setIsCreating(false);
                    setIsEditing(false);
                  }}
                  className="px-3 py-1 text-xs text-muted-foreground hover:text-foreground"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="px-3.5 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-xl hover:opacity-90 transition flex items-center gap-1.5 shadow-subtle"
                >
                  <Check size={13} /> Save Script Tool
                </button>
              </div>
            </div>

            {errorMessage && (
              <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
                <AlertCircle size={14} className="shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  Tool Function Identifier
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. data_normalizer"
                  className="w-full text-xs font-mono bg-background border border-border rounded-xl px-3 py-2 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  Summary / Description
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What this tool computes or returns"
                  className="w-full text-xs bg-background border border-border rounded-xl px-3 py-2 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            {/* Python Code Editor */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                  <Terminal size={13} className="text-primary" /> Python Source Code (AST Sandboxed)
                </label>
                <span className="text-[11px] text-muted-foreground">
                  Must define: <code className="text-primary">def execute(input_data, context):</code>
                </span>
              </div>
              <textarea
                rows={12}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full text-xs font-mono bg-background border border-border rounded-xl p-3 text-foreground focus:outline-none focus:ring-1 focus:ring-primary leading-relaxed resize-y"
              />
            </div>
          </div>
        ) : selectedTool ? (
          /* View Mode & Live Tester */
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div>
                <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <span className="text-amber-500 font-mono">⚡</span> {selectedTool.name}
                </h4>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {selectedTool.description || "No description provided."}
                </p>
              </div>

              {!readOnly && (
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => startEdit(selectedTool)}
                    className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
                    title="Edit Script"
                  >
                    <Edit2 size={15} />
                  </button>
                  <button
                    onClick={() => handleDelete(selectedTool.id)}
                    className="p-1.5 rounded-lg text-destructive/80 hover:text-destructive hover:bg-destructive/10 transition"
                    title="Delete Script"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              )}
            </div>

            {/* Code Viewer */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  <Shield size={12} className="text-emerald-500" /> Sandboxed Python Code
                </span>
                <span className="text-[10px] text-emerald-500 font-medium">Safe Execution Sandbox Active</span>
              </div>
              <pre className="p-3.5 rounded-xl bg-background border border-border/80 text-xs font-mono text-foreground/90 overflow-x-auto max-h-56 leading-relaxed">
                {selectedTool.code}
              </pre>
            </div>

            {/* Live Test Panel */}
            <div className="pt-3 border-t border-border space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <Play size={13} className="text-primary fill-current" /> Live Sandbox Test Runner
                </span>
                <button
                  disabled={isRunningTest}
                  onClick={handleRunTest}
                  className="px-3 py-1 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:opacity-90 disabled:opacity-50 transition flex items-center gap-1.5 shadow-subtle"
                >
                  {isRunningTest ? "Running..." : "Execute Test"}
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-medium text-muted-foreground block mb-1">
                    Input Arguments (JSON)
                  </label>
                  <textarea
                    rows={4}
                    value={testInputJson}
                    onChange={(e) => setTestInputJson(e.target.value)}
                    className="w-full text-xs font-mono bg-background border border-border rounded-xl p-2.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-medium text-muted-foreground block mb-1">
                    Execution Output / Result
                  </label>
                  <div className="min-h-[92px] p-2.5 rounded-xl bg-background border border-border text-xs font-mono overflow-y-auto">
                    {isRunningTest ? (
                      <span className="text-muted-foreground text-[11px] italic">Executing in isolated thread...</span>
                    ) : testResult ? (
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-[11px]">
                          <span
                            className={`px-1.5 py-0.2 rounded font-semibold ${
                              testResult.status === "success"
                                ? "bg-emerald-500/15 text-emerald-500"
                                : "bg-destructive/15 text-destructive"
                            }`}
                          >
                            {testResult.status}
                          </span>
                          <span className="text-muted-foreground flex items-center gap-1">
                            <Clock size={11} /> {testResult.duration_ms}ms
                          </span>
                        </div>
                        {testResult.error ? (
                          <div className="text-destructive text-[11px]">{testResult.error}</div>
                        ) : (
                          <pre className="text-foreground/90 whitespace-pre-wrap">
                            {JSON.stringify(testResult.result, null, 2)}
                          </pre>
                        )}
                        {testResult.stdout && (
                          <div className="pt-1 border-t border-border text-[10px] text-muted-foreground">
                            stdout: {testResult.stdout}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground text-[11px] italic">
                        Supply input arguments and click Execute Test to inspect output.
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-12 text-center text-muted-foreground">
            <FileCode size={36} className="mx-auto mb-2 opacity-40" />
            <p className="text-xs">Select a tool from the left list or create a new one.</p>
          </div>
        )}
      </div>
    </div>
  );
}
