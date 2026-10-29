"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  User,
  Copy,
  Check,
  Pencil,
  RotateCcw,
  ThumbsUp,
  ThumbsDown,
  ChevronLeft,
  ChevronRight,
  Wrench,
  ChevronDown,
  ChevronUp,
  Layers,
  Sparkles,
  Zap,
  BookOpen,
  ExternalLink,
} from "lucide-react";
import { ChatNode } from "../types";

interface MessageItemProps {
  node: ChatNode;
  siblingInfo: { index: number; total: number; siblingIds: string[] };
  onSwitchBranch: (targetSiblingId: string) => void;
  onEdit: (nodeId: string, newContent: string) => void;
  onRegenerate: (nodeId: string) => void;
  onRate: (nodeId: string, rating: "up" | "down" | null) => void;
  isGenerating?: boolean;
}

export default function MessageItem({
  node,
  siblingInfo,
  onSwitchBranch,
  onEdit,
  onRegenerate,
  onRate,
  isGenerating = false,
}: MessageItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(node.content);
  const [copied, setCopied] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [showAllCitations, setShowAllCitations] = useState(false);

  // Extract citations from node metadata or from perplexity / search tool calls
  const rawCitations: string[] = (() => {
    if (Array.isArray(node.metadata?.citations) && node.metadata.citations.length > 0) {
      return node.metadata.citations.map((c) => String(c));
    }
    if (node.metadata?.tool_calls) {
      for (const tc of node.metadata.tool_calls) {
        const res = tc.result as Record<string, unknown> | undefined;
        if (res && Array.isArray(res.citations) && res.citations.length > 0) {
          return res.citations.map((c) => String(c));
        }
        if (res && Array.isArray(res.sources) && res.sources.length > 0) {
          return res.sources.map((s) => String(s));
        }
      }
    }
    return [];
  })();

  const citations = rawCitations.filter((c) => typeof c === "string" && c.trim().length > 0);

  const formatCitationUrl = (urlStr: string) => {
    try {
      if (urlStr.startsWith("http://") || urlStr.startsWith("https://")) {
        const parsed = new URL(urlStr);
        const host = parsed.hostname.replace(/^www\./, "");
        const path =
          parsed.pathname.length > 1
            ? parsed.pathname.slice(0, 24) + (parsed.pathname.length > 24 ? "…" : "")
            : "";
        return { host, path, isUrl: true, fullUrl: urlStr };
      }
    } catch {
      // fallback
    }
    return { host: urlStr.slice(0, 32), path: "", isUrl: false, fullUrl: urlStr };
  };

  const isUser = node.role === "user";
  const hasMultipleVersions = siblingInfo.total > 1;
  const hasToolCalls =
    node.metadata?.tool_calls && node.metadata.tool_calls.length > 0;

  const isDelegated =
    !isUser &&
    node.metadata?.agent_id &&
    node.metadata.agent_id !== "orchestrator" &&
    node.metadata?.tool_calls?.some((tc) => tc.tool === "swarm_router");

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(node.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy to clipboard", err);
    }
  };

  const handleSaveEdit = () => {
    if (!editContent.trim()) return;
    onEdit(node.id, editContent);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditContent(node.content);
    setIsEditing(false);
  };

  const handlePrevBranch = () => {
    if (siblingInfo.index > 1) {
      const prevId = siblingInfo.siblingIds[siblingInfo.index - 2];
      onSwitchBranch(prevId);
    }
  };

  const handleNextBranch = () => {
    if (siblingInfo.index < siblingInfo.total) {
      const nextId = siblingInfo.siblingIds[siblingInfo.index];
      onSwitchBranch(nextId);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15 }}
      className={`group flex gap-3 ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar */}
      <div
        className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 border ${
          isUser
            ? "bg-surface-2 border-hairline-strong text-ink"
            : isDelegated
            ? "bg-surface-1 border-hairline text-linear-primary"
            : "bg-surface-1 border-hairline text-ink-subtle"
        }`}
      >
        {isUser ? <User size={13} /> : isDelegated ? <Layers size={13} /> : <Bot size={13} />}
      </div>

      {/* Message Body & Actions Container */}
      <div
        className={`flex flex-col max-w-[85%] md:max-w-2xl ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        {/* Main Content Bubble */}
        <div
          className={`px-4 py-3 rounded-lg text-[14px] leading-relaxed transition-colors relative border ${
            isUser
              ? "bg-surface-2 border-hairline-strong text-ink rounded-tr-xs"
              : "bg-surface-1 border-hairline text-ink rounded-tl-xs"
          }`}
        >
          {/* Autonomous Workflow Progress Banner */}
          {node.metadata?.mode === "workflow_execution" && (
            <div className="mb-3 p-3 rounded-md bg-canvas border border-hairline space-y-2">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="flex items-center gap-1.5 text-linear-primary">
                  <Layers size={13} /> {String(node.metadata.workflow_title || "Autonomous Workflow")}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-pill bg-surface-2 text-semantic-success border border-hairline font-mono">
                  Completed
                </span>
              </div>

              {Boolean(node.metadata.workflow_goal) && (
                <p className="text-[11px] text-ink-subtle line-clamp-2 font-mono">
                  Goal: {String(node.metadata.workflow_goal)}
                </p>
              )}

              {/* Step Badges */}
              {Array.isArray(node.metadata.step_runs) && (node.metadata.step_runs as Array<{ step_id?: string; agent_id?: string; duration_ms?: number }>).length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1.5 border-t border-hairline">
                  {(node.metadata.step_runs as Array<{ step_id?: string; agent_id?: string; duration_ms?: number }>).map((st, sIdx) => (
                    <span
                      key={sIdx}
                      className="px-2 py-0.5 rounded-xs bg-surface-2 border border-hairline text-[10px] text-ink font-mono flex items-center gap-1"
                    >
                      <Bot size={10} className="text-linear-primary" />
                      {st.step_id || `Step ${sIdx + 1}`}: {st.agent_id} ({st.duration_ms}ms)
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Orchestrator Delegation Trace Banner */}
          {isDelegated && (
            <div className="mb-2.5 pb-2 border-b border-hairline flex flex-wrap items-center justify-between gap-2 text-[11px] text-ink-subtle font-mono">
              <div className="flex items-center gap-1.5">
                <Layers size={12} className="text-linear-primary shrink-0" />
                <span>Orchestrator dispatched to</span>
                <span className="font-medium text-ink px-1.5 py-0.5 rounded-xs bg-surface-2 border border-hairline">
                  {node.metadata?.agent_name || node.metadata?.agent_id}
                </span>
              </div>
              {node.metadata?.latency_ms && (
                <span className="text-[10px] text-ink-tertiary">
                  {node.metadata.latency_ms}ms
                </span>
              )}
            </div>
          )}

          {isEditing ? (
            <div className="w-full min-w-[280px] sm:min-w-[420px] text-ink">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={3}
                className="w-full p-2.5 bg-canvas text-ink border border-hairline rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-linear-focus transition-colors font-mono"
                placeholder="Edit your message..."
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Escape") handleCancelEdit();
                  if (e.key === "Enter" && (e.ctrlKey || e.metaKey))
                    handleSaveEdit();
                }}
              />
              <div className="flex justify-end gap-2 mt-2">
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  className="px-2.5 py-1 text-xs text-ink-subtle hover:text-ink bg-surface-2 rounded-md transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveEdit}
                  disabled={!editContent.trim()}
                  className="px-3 py-1 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover disabled:opacity-40 rounded-md transition"
                >
                  Save & Submit
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="prose prose-sm dark:prose-invert max-w-none break-words text-ink">
                <ReactMarkdown
                  components={{
                    pre({ children }) {
                      return (
                        <pre className="not-prose my-2.5 overflow-x-auto rounded-md bg-canvas p-3 text-xs text-ink-muted border border-hairline font-mono">
                          {children}
                        </pre>
                      );
                    },
                    code({ className, children, ...props }) {
                      const isInline = !className;
                      if (isInline) {
                        return (
                          <code
                            className="rounded-xs bg-surface-2 px-1 py-0.5 font-mono text-[12px] text-ink border border-hairline"
                            {...props}
                          >
                            {children}
                          </code>
                        );
                      }
                      return (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                    strong({ children }) {
                      return (
                        <strong className="font-semibold text-ink">
                          {children}
                        </strong>
                      );
                    },
                    b({ children }) {
                      return (
                        <b className="font-semibold text-ink">
                          {children}
                        </b>
                      );
                    },
                    h1({ children }) {
                      return (
                        <h1 className="text-base font-bold text-ink mb-2 mt-3">
                          {children}
                        </h1>
                      );
                    },
                    h2({ children }) {
                      return (
                        <h2 className="text-sm font-semibold text-ink mb-1.5 mt-2.5">
                          {children}
                        </h2>
                      );
                    },
                    h3({ children }) {
                      return (
                        <h3 className="text-xs font-semibold text-ink mb-1 mt-2">
                          {children}
                        </h3>
                      );
                    },
                    a({ href, children }) {
                      return (
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-linear-primary hover:text-linear-hover underline underline-offset-2 transition-colors font-medium"
                        >
                          {children}
                        </a>
                      );
                    },
                  }}
                >
                  {node.content}
                </ReactMarkdown>
              </div>

              {/* Dedicated Sources & Citations Section (e.g. Perplexity Sonar) */}
              {citations.length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-hairline select-none">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5 text-[11px] font-medium text-ink">
                      <BookOpen size={12} className="text-linear-primary" />
                      <span>Sources & Citations</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-surface-2 text-ink-subtle border border-hairline font-mono">
                        {citations.length}
                      </span>
                    </div>
                    {citations.length > 4 && (
                      <button
                        type="button"
                        onClick={() => setShowAllCitations(!showAllCitations)}
                        className="text-[10px] font-mono text-linear-primary hover:text-linear-hover transition-colors"
                      >
                        {showAllCitations ? "Show less" : `+${citations.length - 4} more`}
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                    {(showAllCitations ? citations : citations.slice(0, 4)).map((cite, idx) => {
                      const { host, path, isUrl, fullUrl } = formatCitationUrl(cite);
                      return (
                        <a
                          key={idx}
                          href={isUrl ? fullUrl : undefined}
                          target={isUrl ? "_blank" : undefined}
                          rel={isUrl ? "noopener noreferrer" : undefined}
                          title={fullUrl}
                          className="group/cite flex items-center justify-between gap-2 p-2 rounded-md bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong transition-all text-xs overflow-hidden"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="w-4 h-4 rounded bg-surface-2 group-hover/cite:bg-linear-primary/20 text-[10px] font-mono font-medium text-ink-muted group-hover/cite:text-linear-primary flex items-center justify-center shrink-0 border border-hairline">
                              {idx + 1}
                            </span>
                            <div className="min-w-0">
                              <p className="text-[11px] font-medium text-ink group-hover/cite:text-linear-primary truncate transition-colors">
                                {host}
                              </p>
                              {path && (
                                <p className="text-[9px] font-mono text-ink-tertiary truncate">
                                  {path}
                                </p>
                              )}
                            </div>
                          </div>
                          {isUrl && (
                            <ExternalLink
                              size={11}
                              className="text-ink-tertiary group-hover/cite:text-linear-primary shrink-0 opacity-70 group-hover/cite:opacity-100 transition-opacity"
                            />
                          )}
                        </a>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Tool Calls Accordion */}
              {hasToolCalls && (
                <div className="mt-2.5 pt-2 border-t border-hairline">
                  <button
                    type="button"
                    onClick={() => setShowTools(!showTools)}
                    className="flex items-center gap-1.5 text-[11px] font-mono text-ink-subtle hover:text-ink bg-surface-1 hover:bg-surface-2 px-2.5 py-0.5 rounded-pill border border-hairline transition-colors"
                  >
                    <Wrench size={11} className="text-linear-primary" />
                    <span>
                      {node.metadata?.tool_calls?.length}{" "}
                      {node.metadata?.tool_calls?.length === 1
                        ? "tool execution"
                        : "tool executions"}
                    </span>
                    {showTools ? (
                      <ChevronUp size={11} className="ml-0.5 text-ink-tertiary" />
                    ) : (
                      <ChevronDown size={11} className="ml-0.5 text-ink-tertiary" />
                    )}
                  </button>

                  <AnimatePresence>
                    {showTools && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-2 space-y-2 overflow-hidden text-xs"
                      >
                        {node.metadata?.tool_calls?.map((tc, idx) => {
                          const cleanResult = (() => {
                            if (tc.result && typeof tc.result === "object") {
                              const r = { ...(tc.result as Record<string, unknown>) };
                              if ("citations" in r && citations.length > 0) {
                                delete r.citations;
                                r.citations_displayed = "Viewed in Sources & Citations section above";
                              }
                              return r;
                            }
                            return tc.result;
                          })();
                          return (
                            <div
                              key={idx}
                              className="p-3 rounded-md bg-canvas text-ink-muted font-mono text-[11px] overflow-x-auto border border-hairline"
                            >
                              <div className="flex items-center justify-between mb-1.5">
                                <div className="text-ink font-medium flex items-center gap-1.5">
                                  <Zap size={11} className="text-linear-primary" />
                                  <span>{tc.tool}</span>
                                </div>
                                <span className="text-[9px] px-1.5 py-0.2 rounded-xs bg-surface-2 text-ink-subtle border border-hairline">
                                  Swarm Tool
                                </span>
                              </div>
                              {tc.args && (
                                <div className="text-ink-subtle mt-1">
                                  <span className="text-ink-tertiary">args: </span>
                                  {JSON.stringify(tc.args)}
                                </div>
                              )}
                              {cleanResult !== undefined && (
                                <div className="text-semantic-success mt-1.5 pt-1.5 border-t border-hairline">
                                  <span className="text-ink-tertiary">result: </span>
                                  {JSON.stringify(cleanResult)}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* Agent Execution Metadata Badges */}
              {node.metadata?.agent_state && (
                <div className="mt-2.5 flex flex-wrap items-center gap-1.5 text-xs">
                  <span className="inline-flex items-center gap-1 text-ink-subtle bg-surface-2 px-1.5 py-0.5 rounded-xs border border-hairline text-[10px] font-mono">
                    <span className="w-1.5 h-1.5 rounded-full bg-semantic-success" />
                    State: {String(node.metadata.agent_state)}
                  </span>
                  {node.metadata?.agent_id && (
                    <span className="text-[10px] text-ink-subtle font-mono">
                      via {String(node.metadata.agent_name || node.metadata.agent_id)}
                    </span>
                  )}
                  {/* Skills Invoked Chips */}
                  {node.metadata?.skills_invoked &&
                    Array.isArray(node.metadata.skills_invoked) &&
                    node.metadata.skills_invoked.map((sk: string, i: number) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded-xs bg-surface-2 text-ink-muted border border-hairline"
                      >
                        <Sparkles size={8} className="text-linear-primary" />
                        <span>{sk}</span>
                      </span>
                    ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Message Action Bar & Branch Switcher */}
        {!isEditing && (
          <div
            className={`flex items-center gap-1 mt-1 text-xs text-ink-subtle select-none ${
              isUser ? "flex-row-reverse" : "flex-row"
            }`}
          >
            {/* Sibling Branch Switcher (< 1 / 2 >) */}
            {hasMultipleVersions && (
              <div className="flex items-center bg-surface-1 rounded-md px-1 py-0.5 text-[11px] font-mono text-ink border border-hairline">
                <button
                  type="button"
                  onClick={handlePrevBranch}
                  disabled={siblingInfo.index <= 1}
                  className="p-0.5 hover:text-ink disabled:opacity-30 disabled:cursor-not-allowed transition"
                  title="Previous version"
                  aria-label="Previous version"
                >
                  <ChevronLeft size={12} />
                </button>
                <span className="px-1 text-[10px] text-ink-muted">
                  {siblingInfo.index} / {siblingInfo.total}
                </span>
                <button
                  type="button"
                  onClick={handleNextBranch}
                  disabled={siblingInfo.index >= siblingInfo.total}
                  className="p-0.5 hover:text-ink disabled:opacity-30 disabled:cursor-not-allowed transition"
                  title="Next version"
                  aria-label="Next version"
                >
                  <ChevronRight size={12} />
                </button>
              </div>
            )}

            {/* Copy Button */}
            <button
              type="button"
              onClick={handleCopy}
              className="p-1 hover:text-ink hover:bg-surface-1 rounded-md transition"
              title="Copy message"
              aria-label="Copy message"
            >
              {copied ? (
                <Check size={13} className="text-semantic-success" />
              ) : (
                <Copy size={13} />
              )}
            </button>

            {/* Edit Button (User Only) */}
            {isUser && (
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="p-1 hover:text-ink hover:bg-surface-1 rounded-md transition"
                title="Edit message"
                aria-label="Edit message"
              >
                <Pencil size={13} />
              </button>
            )}

            {/* Actions for Agent Messages */}
            {!isUser && (
              <>
                {/* Regenerate Button */}
                <button
                  type="button"
                  onClick={() => onRegenerate(node.id)}
                  disabled={isGenerating}
                  className="p-1 hover:text-ink hover:bg-surface-1 rounded-md transition disabled:opacity-30"
                  title="Regenerate response"
                  aria-label="Regenerate response"
                >
                  <RotateCcw size={13} />
                </button>

                {/* Thumbs Up Button */}
                <button
                  type="button"
                  onClick={() =>
                    onRate(node.id, node.rating === "up" ? null : "up")
                  }
                  className={`p-1 rounded-md transition ${
                    node.rating === "up"
                      ? "text-semantic-success bg-surface-2"
                      : "hover:text-ink hover:bg-surface-1"
                  }`}
                  title="Helpful / Good response"
                  aria-label="Thumbs up"
                >
                  <ThumbsUp size={13} />
                </button>

                {/* Thumbs Down Button */}
                <button
                  type="button"
                  onClick={() =>
                    onRate(node.id, node.rating === "down" ? null : "down")
                  }
                  className={`p-1 rounded-md transition ${
                    node.rating === "down"
                      ? "text-red-400 bg-surface-2"
                      : "hover:text-ink hover:bg-surface-1"
                  }`}
                  title="Unhelpful / Bad response"
                  aria-label="Thumbs down"
                >
                  <ThumbsDown size={13} />
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
