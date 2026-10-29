"use client";

import React, { useState, useEffect } from "react";
import { getAuthHeaders } from "@/lib/supabase";
import { AgentCardData } from "./AgentCard";
import {
  X,
  Play,
  Bot,
  Zap,
  Clock,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  Code,
  FileText,
  Cpu,
} from "lucide-react";
import ReactMarkdown from "react-markdown";

interface AgentPlaygroundModalProps {
  agent: AgentCardData | null;
  isOpen: boolean;
  onClose: () => void;
}

interface AgentTestResult {
  status: "completed" | "success" | "error";
  agent_id: string;
  response: string;
  tokens_used: number;
  duration_ms: number;
  tool_calls: Array<{
    tool?: string;
    tool_name?: string;
    args?: Record<string, unknown>;
    result?: unknown;
    status?: string;
  }>;
  error?: string | null;
}

const SAMPLE_PROMPTS = [
  "Introduce yourself and explain your domain specialization.",
  "What specific tools and capabilities do you utilize?",
  "Analyze this scenario and provide an actionable strategy.",
];

export default function AgentPlaygroundModal({
  agent,
  isOpen,
  onClose,
}: AgentPlaygroundModalProps) {
  const [testPrompt, setTestPrompt] = useState(SAMPLE_PROMPTS[0]);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<AgentTestResult | null>(null);
  const [activeTab, setActiveTab] = useState<"response" | "tools" | "raw">("response");
  const [copied, setCopied] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setResult(null);
      setErrorMessage(null);
      setTestPrompt(SAMPLE_PROMPTS[0]);
    }
  }, [isOpen, agent?.id]);

  if (!isOpen || !agent) return null;

  const handleRunTest = async () => {
    if (!testPrompt.trim()) return;

    setIsRunning(true);
    setErrorMessage(null);
    setResult(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const authHeaders = await getAuthHeaders();

      const res = await fetch(`${apiUrl}/api/custom-agents/test`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          agent_id: agent.id,
          prompt: testPrompt.trim(),
          input_prompt: testPrompt.trim(),
          system_prompt: agent.system_prompt || undefined,
          model: agent.model || undefined,
          temperature: agent.temperature,
          inputs: {},
          mock_variables: {},
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Agent test failed with status ${res.status}`);
      }

      const rawData = await res.json();
      const normalizedData: AgentTestResult = {
        status: rawData.status === "error" ? "error" : "completed",
        agent_id: rawData.agent_id || agent.id,
        response: rawData.response || rawData.content || "Agent completed without response.",
        tokens_used: rawData.tokens_used || 0,
        duration_ms: rawData.duration_ms || rawData.latency_ms || 0,
        tool_calls: rawData.tool_calls || [],
        error: rawData.error || null,
      };
      setResult(normalizedData);
      setActiveTab("response");
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "Agent test execution error.");
    } finally {
      setIsRunning(false);
    }
  };

  const handleCopy = () => {
    if (!result?.response) return;
    navigator.clipboard.writeText(result.response);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-canvas border border-hairline rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden select-none">
        {/* Header */}
        <div className="h-14 px-5 border-b border-hairline flex items-center justify-between shrink-0 bg-surface-1/50">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md bg-surface-2 border border-hairline text-semantic-success flex items-center justify-center">
              <Play size={12} className="fill-current" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-semibold text-ink tracking-tight">
                  Playground: {agent.name}
                </h3>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-xs bg-surface-2 text-ink-subtle border border-hairline">
                  {agent.id}
                </span>
              </div>
              <p className="text-[10px] text-ink-subtle flex items-center gap-1.5 font-mono">
                <Cpu size={10} className="text-linear-primary" /> Model:{" "}
                <span className="text-ink font-medium">{agent.model || "qwen-3.8"}</span>
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors border border-hairline"
            title="Close playground"
          >
            <X size={14} />
          </button>
        </div>

        {/* Playground Scroll Body */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1 text-xs">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono">
              {errorMessage}
            </div>
          )}

          {/* Prompt Input Section */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-medium text-ink flex items-center gap-1.5">
                <Bot size={12} className="text-linear-primary" /> Test Input Prompt
              </label>

              {/* Sample Quick Prompt Chips */}
              <div className="flex items-center gap-1">
                <span className="text-[10px] text-ink-tertiary hidden sm:inline">Try:</span>
                {SAMPLE_PROMPTS.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setTestPrompt(p)}
                    className="text-[9px] font-mono px-1.5 py-0.5 rounded-xs bg-surface-2 hover:bg-surface-3 text-ink-muted hover:text-ink border border-hairline transition-colors truncate max-w-[120px]"
                    title={p}
                  >
                    Sample #{idx + 1}
                  </button>
                ))}
              </div>
            </div>

            <textarea
              rows={3}
              value={testPrompt}
              onChange={(e) => setTestPrompt(e.target.value)}
              placeholder="Enter a test prompt to evaluate this agent..."
              className="w-full text-xs font-mono bg-canvas border border-hairline hover:border-hairline-strong focus:border-linear-focus rounded-md p-3 text-ink focus:outline-none leading-relaxed resize-y"
            />
          </div>

          {/* Execute Test Button */}
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleRunTest}
              disabled={isRunning || !testPrompt.trim()}
              className="px-4 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors shadow-card flex items-center gap-1.5 disabled:opacity-40"
            >
              {isRunning ? (
                <>
                  <span className="w-3 h-3 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  <span>Executing Turn...</span>
                </>
              ) : (
                <>
                  <Play size={11} className="fill-current" />
                  <span>Execute Playground Test</span>
                </>
              )}
            </button>
          </div>

          {/* Test Execution Result */}
          {result && (
            <div className="p-3.5 rounded-lg bg-surface-1 border border-hairline space-y-3 mt-2 animate-fade-in">
              <div className="flex items-center justify-between pb-2 border-b border-hairline">
                <div className="flex items-center gap-2">
                  {result.status === "completed" || result.status === "success" ? (
                    <CheckCircle2 size={15} className="text-semantic-success" />
                  ) : (
                    <XCircle size={15} className="text-red-400" />
                  )}
                  <span className="font-semibold text-ink text-xs">
                    Outcome: <span className="uppercase font-mono text-[11px] text-semantic-success">{result.status}</span>
                  </span>
                </div>

                <div className="flex items-center gap-3 text-ink-subtle text-[11px] font-mono">
                  <span className="flex items-center gap-1">
                    <Clock size={11} /> {result.duration_ms}ms
                  </span>
                  <span className="flex items-center gap-1">
                    <Zap size={11} className="text-linear-primary" /> {result.tokens_used} tokens
                  </span>
                </div>
              </div>

              {/* Output Tabs */}
              <div className="flex items-center gap-1 border-b border-hairline pb-1 text-[11px]">
                <button
                  type="button"
                  onClick={() => setActiveTab("response")}
                  className={`px-2 py-0.5 rounded-md font-medium transition-colors ${
                    activeTab === "response"
                      ? "bg-surface-2 text-ink border border-hairline"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  <span className="flex items-center gap-1">
                    <FileText size={11} /> Agent Response
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab("tools")}
                  className={`px-2 py-0.5 rounded-md font-medium transition-colors ${
                    activeTab === "tools"
                      ? "bg-surface-2 text-ink border border-hairline"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  <span className="flex items-center gap-1">
                    <Zap size={11} className="text-amber-400" /> Tools ({result.tool_calls?.length || 0})
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab("raw")}
                  className={`px-2 py-0.5 rounded-md font-medium transition-colors ${
                    activeTab === "raw"
                      ? "bg-surface-2 text-ink border border-hairline"
                      : "text-ink-subtle hover:text-ink"
                  }`}
                >
                  <span className="flex items-center gap-1">
                    <Code size={11} /> Raw Payload
                  </span>
                </button>

                <div className="ml-auto">
                  <button
                    type="button"
                    onClick={handleCopy}
                    className="flex items-center gap-1 text-[10px] text-ink-subtle hover:text-ink bg-surface-2 px-1.5 py-0.5 rounded-md border border-hairline transition-colors"
                  >
                    {copied ? <Check size={11} className="text-semantic-success" /> : <Copy size={11} />}
                    <span>{copied ? "Copied" : "Copy"}</span>
                  </button>
                </div>
              </div>

              {/* Response Tab */}
              {activeTab === "response" && (
                <div className="p-3 rounded-md bg-canvas border border-hairline text-ink leading-relaxed font-sans text-xs max-h-64 overflow-y-auto space-y-2">
                  <ReactMarkdown>{result.response}</ReactMarkdown>
                </div>
              )}

              {/* Tools Tab */}
              {activeTab === "tools" && (
                <div className="space-y-2 max-h-64 overflow-y-auto font-mono text-[11px]">
                  {result.tool_calls && result.tool_calls.length > 0 ? (
                    result.tool_calls.map((tc, idx) => (
                      <div key={idx} className="p-2.5 rounded-md bg-canvas border border-hairline">
                        <div className="flex items-center justify-between text-ink font-semibold">
                          <span>{tc.tool_name || tc.tool || "Tool"}</span>
                          <span className="text-[10px] text-ink-subtle">Call #{idx + 1}</span>
                        </div>
                        {Boolean(tc.args) && (
                          <div className="text-ink-subtle mt-1 text-[10px]">
                            <span className="text-ink-tertiary">args: </span>
                            {JSON.stringify(tc.args)}
                          </div>
                        )}
                        {Boolean(tc.result !== undefined) && (
                          <div className="text-semantic-success mt-1 pt-1 border-t border-hairline text-[10px]">
                            <span className="text-ink-tertiary">result: </span>
                            {JSON.stringify(tc.result)}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-[11px] text-ink-subtle py-2 font-mono">
                      No tool calls invoked in this evaluation turn.
                    </p>
                  )}
                </div>
              )}

              {/* Raw JSON Tab */}
              {activeTab === "raw" && (
                <pre className="font-mono text-[11px] text-ink leading-relaxed bg-canvas p-3 rounded-md border border-hairline whitespace-pre-wrap max-h-64 overflow-y-auto">
                  {JSON.stringify(result, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
