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
  Server,
  Zap,
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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`group flex gap-3 md:gap-4 ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-subtle border ${
          isUser
            ? "bg-primary border-primary/40 text-primary-foreground"
            : isDelegated
            ? "bg-card border-primary/40 text-primary"
            : "bg-card border-border/80 text-primary"
        }`}
      >
        {isUser ? <User size={15} /> : isDelegated ? <Layers size={15} /> : <Bot size={15} />}
      </div>

      {/* Message Body & Actions Container */}
      <div
        className={`flex flex-col max-w-[85%] md:max-w-2xl ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        {/* Main Content Bubble */}
        <div
          className={`px-5 py-3.5 rounded-2xl text-[15px] leading-relaxed shadow-subtle transition-all relative ${
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm"
              : "bg-card border border-border/80 text-card-foreground rounded-tl-sm"
          }`}
        >
          {/* Autonomous Workflow Progress Banner */}
          {node.metadata?.mode === "workflow_execution" && (
            <div className="mb-3 p-3 rounded-xl bg-background/80 border border-primary/30 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="flex items-center gap-1.5 text-primary">
                  <Layers size={14} /> {String(node.metadata.workflow_title || "Autonomous Workflow")}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-500 border border-emerald-500/30 font-medium">
                  Completed
                </span>
              </div>

              {Boolean(node.metadata.workflow_goal) && (
                <p className="text-[11px] text-muted-foreground line-clamp-2 font-mono">
                  Goal: {String(node.metadata.workflow_goal)}
                </p>
              )}

              {/* Step Badges */}
              {Array.isArray(node.metadata.step_runs) && (node.metadata.step_runs as Array<{ step_id?: string; agent_id?: string; duration_ms?: number }>).length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1.5 border-t border-border/50">
                  {(node.metadata.step_runs as Array<{ step_id?: string; agent_id?: string; duration_ms?: number }>).map((st, sIdx) => (
                    <span
                      key={sIdx}
                      className="px-2 py-0.5 rounded-lg bg-card border border-border text-[10px] text-foreground font-mono flex items-center gap-1"
                    >
                      <Bot size={10} className="text-primary" />
                      {st.step_id || `Step ${sIdx + 1}`}: {st.agent_id} ({st.duration_ms}ms)
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Orchestrator Delegation Trace Banner */}
          {isDelegated && (
            <div className="mb-2.5 pb-2 border-b border-border/50 flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground font-mono">
              <div className="flex items-center gap-1.5">
                <Layers size={13} className="text-primary shrink-0" />
                <span>Orchestrator dispatched to</span>
                <span className="font-semibold text-foreground px-1.5 py-0.5 rounded bg-primary/15 text-primary border border-primary/25">
                  {node.metadata?.agent_name || node.metadata?.agent_id}
                </span>
              </div>
              {node.metadata?.latency_ms && (
                <span className="text-[10px] text-muted-foreground/70">
                  {node.metadata.latency_ms}ms
                </span>
              )}
            </div>
          )}

          {isEditing ? (
            <div className="w-full min-w-[280px] sm:min-w-[420px] text-foreground">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={3}
                className="w-full p-2.5 bg-background text-foreground border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all"
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
                  className="px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground bg-muted hover:bg-muted/80 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveEdit}
                  disabled={!editContent.trim()}
                  className="px-3 py-1.5 text-xs font-medium text-primary-foreground bg-primary hover:opacity-90 disabled:opacity-50 rounded-lg transition shadow-subtle"
                >
                  Save & Submit
                </button>
              </div>
            </div>
          ) : (
            <>
              <div
                className={`prose prose-sm max-w-none break-words ${
                  isUser
                    ? "prose-invert"
                    : "prose-neutral dark:prose-invert"
                }`}
              >
                <ReactMarkdown
                  components={{
                    pre({ children }) {
                      return (
                        <pre className="not-prose my-3 overflow-x-auto rounded-xl bg-zinc-950 p-3 text-xs text-zinc-100 border border-zinc-800 shadow-subtle">
                          {children}
                        </pre>
                      );
                    },
                    code({ className, children, ...props }) {
                      const isInline = !className;
                      if (isInline) {
                        return (
                          <code
                            className="rounded bg-muted px-1.5 py-0.5 font-mono text-[13px] text-foreground border border-border/40"
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
                  }}
                >
                  {node.content}
                </ReactMarkdown>
              </div>

              {/* Tool Calls Accordion */}
              {hasToolCalls && (
                <div className="mt-3 pt-3 border-t border-border/50">
                  <button
                    type="button"
                    onClick={() => setShowTools(!showTools)}
                    className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground bg-muted/60 hover:bg-muted px-2.5 py-1.5 rounded-lg border border-border/70 transition-all"
                  >
                    <Wrench size={13} className="text-amber-500" />
                    <span>
                      {node.metadata?.tool_calls?.length}{" "}
                      {node.metadata?.tool_calls?.length === 1
                        ? "tool execution"
                        : "tool executions"}
                    </span>
                    {showTools ? (
                      <ChevronUp size={13} className="ml-0.5 text-muted-foreground" />
                    ) : (
                      <ChevronDown size={13} className="ml-0.5 text-muted-foreground" />
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
                          const resObj = tc.result as Record<string, unknown> | undefined;
                          const hasMcp = Boolean(resObj?.mcp_servers && Array.isArray(resObj.mcp_servers) && resObj.mcp_servers.length > 0);

                          return (
                            <div
                              key={idx}
                              className="p-3 rounded-xl bg-zinc-950 text-zinc-200 font-mono text-[11px] overflow-x-auto border border-zinc-800 shadow-subtle"
                            >
                              <div className="flex items-center justify-between mb-1.5">
                                <div className="text-amber-400 font-semibold flex items-center gap-1.5">
                                  <Zap size={12} className="text-amber-400" />
                                  <span>{tc.tool}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  {hasMcp ? (
                                    <span className="inline-flex items-center gap-1 text-[9px] px-1.5 py-0.2 rounded bg-violet-500/20 text-violet-400 border border-violet-500/30">
                                      <Server size={10} />
                                      <span>MCP Ready</span>
                                    </span>
                                  ) : (
                                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-400 border border-amber-500/25">
                                      Swarm Tool
                                    </span>
                                  )}
                                </div>
                              </div>
                              {tc.args && (
                                <div className="text-zinc-400 mt-1">
                                  <span className="text-zinc-500">args: </span>
                                  {JSON.stringify(tc.args)}
                                </div>
                              )}
                              {tc.result !== undefined && (
                                <div className="text-emerald-400 mt-1.5 pt-1.5 border-t border-zinc-800">
                                  <span className="text-zinc-500">result: </span>
                                  {JSON.stringify(tc.result)}
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
                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                  <span className="inline-flex items-center gap-1.5 text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-md border border-border/60 text-[11px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                    State: {String(node.metadata.agent_state)}
                  </span>
                  {node.metadata?.agent_id && (
                    <span className="text-[11px] text-muted-foreground">
                      via {String(node.metadata.agent_name || node.metadata.agent_id)}
                    </span>
                  )}
                  {/* Skills Invoked Chips */}
                  {node.metadata?.skills_invoked &&
                    Array.isArray(node.metadata.skills_invoked) &&
                    node.metadata.skills_invoked.map((sk: string, i: number) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20"
                      >
                        <Sparkles size={9} />
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
            className={`flex items-center gap-1.5 mt-1.5 text-xs text-muted-foreground select-none ${
              isUser ? "flex-row-reverse" : "flex-row"
            }`}
          >
            {/* Sibling Branch Switcher (< 1 / 2 >) */}
            {hasMultipleVersions && (
              <div className="flex items-center bg-muted/70 hover:bg-muted rounded-lg px-1.5 py-0.5 text-[11px] font-medium text-foreground border border-border/60 transition-all shadow-subtle">
                <button
                  type="button"
                  onClick={handlePrevBranch}
                  disabled={siblingInfo.index <= 1}
                  className="p-0.5 hover:text-primary disabled:opacity-30 disabled:cursor-not-allowed transition"
                  title="Previous version"
                  aria-label="Previous version"
                >
                  <ChevronLeft size={13} />
                </button>
                <span className="px-1.5 text-[11px] font-mono">
                  {siblingInfo.index} / {siblingInfo.total}
                </span>
                <button
                  type="button"
                  onClick={handleNextBranch}
                  disabled={siblingInfo.index >= siblingInfo.total}
                  className="p-0.5 hover:text-primary disabled:opacity-30 disabled:cursor-not-allowed transition"
                  title="Next version"
                  aria-label="Next version"
                >
                  <ChevronRight size={13} />
                </button>
              </div>
            )}

            {/* Copy Button */}
            <button
              type="button"
              onClick={handleCopy}
              className="p-1 hover:text-foreground hover:bg-muted/80 rounded-md transition"
              title="Copy message"
              aria-label="Copy message"
            >
              {copied ? (
                <Check size={14} className="text-emerald-500" />
              ) : (
                <Copy size={14} />
              )}
            </button>

            {/* Edit Button (User Only) */}
            {isUser && (
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="p-1 hover:text-foreground hover:bg-muted/80 rounded-md transition"
                title="Edit message"
                aria-label="Edit message"
              >
                <Pencil size={14} />
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
                  className="p-1 hover:text-foreground hover:bg-muted/80 rounded-md transition disabled:opacity-30"
                  title="Regenerate response"
                  aria-label="Regenerate response"
                >
                  <RotateCcw size={14} />
                </button>

                {/* Thumbs Up Button */}
                <button
                  type="button"
                  onClick={() =>
                    onRate(node.id, node.rating === "up" ? null : "up")
                  }
                  className={`p-1 rounded-md transition ${
                    node.rating === "up"
                      ? "text-emerald-500 bg-emerald-500/10"
                      : "hover:text-foreground hover:bg-muted/80"
                  }`}
                  title="Helpful / Good response"
                  aria-label="Thumbs up"
                >
                  <ThumbsUp size={14} />
                </button>

                {/* Thumbs Down Button */}
                <button
                  type="button"
                  onClick={() =>
                    onRate(node.id, node.rating === "down" ? null : "down")
                  }
                  className={`p-1 rounded-md transition ${
                    node.rating === "down"
                      ? "text-destructive bg-destructive/10"
                      : "hover:text-foreground hover:bg-muted/80"
                  }`}
                  title="Unhelpful / Bad response"
                  aria-label="Thumbs down"
                >
                  <ThumbsDown size={14} />
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
