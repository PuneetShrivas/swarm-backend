"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Zap, Activity, Cpu, Bot, RefreshCw } from "lucide-react";
import { UserUsageSummary } from "../types";

interface UsageModalProps {
  isOpen: boolean;
  onClose: () => void;
  usage: UserUsageSummary | null;
  isLoading: boolean;
  onRefresh: () => void;
}

export default function UsageModal({
  isOpen,
  onClose,
  usage,
  isLoading,
  onRefresh,
}: UsageModalProps) {
  if (!isOpen) return null;

  const totalTokens = usage?.total_tokens ?? 0;
  const totalRequests = usage?.total_requests ?? 0;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.15 }}
          className="bg-card rounded-2xl shadow-card border border-border/80 max-w-lg w-full overflow-hidden flex flex-col max-h-[85vh] text-foreground"
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-border/60 flex items-center justify-between bg-muted/30">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/25 flex items-center justify-center text-amber-500 shadow-subtle">
                <Zap size={16} />
              </div>
              <div>
                <h3 className="font-semibold text-foreground text-sm tracking-tight">
                  User Usage & Telemetry
                </h3>
                <p className="text-[11px] text-muted-foreground">
                  Supabase-tracked tokens & execution stats
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={onRefresh}
                disabled={isLoading}
                title="Refresh usage stats"
                className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition disabled:opacity-40"
              >
                <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
              </button>
              <button
                type="button"
                onClick={onClose}
                className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition"
              >
                <X size={15} />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="p-6 overflow-y-auto space-y-5 flex-1">
            {/* Top Metric Cards */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 rounded-xl bg-primary/10 border border-primary/20">
                <div className="text-[11px] font-medium text-primary uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Zap size={12} /> Total Tokens
                </div>
                <div className="text-2xl font-bold text-foreground">
                  {totalTokens.toLocaleString()}
                </div>
                <div className="text-[10px] text-muted-foreground mt-0.5">
                  Input prompt + output response
                </div>
              </div>

              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <div className="text-[11px] font-medium text-emerald-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Activity size={12} /> Swarm Queries
                </div>
                <div className="text-2xl font-bold text-foreground">
                  {totalRequests.toLocaleString()}
                </div>
                <div className="text-[10px] text-muted-foreground mt-0.5">
                  Completed agent turns
                </div>
              </div>
            </div>

            {/* Tokens by Agent */}
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                <Bot size={13} className="text-muted-foreground" />
                Consumption by Agent
              </h4>
              <div className="space-y-1.5">
                {usage?.agents && Object.keys(usage.agents).length > 0 ? (
                  Object.entries(usage.agents).map(([agentId, tokens]) => (
                    <div
                      key={agentId}
                      className="flex items-center justify-between p-2.5 rounded-xl bg-muted/40 border border-border/60 text-xs"
                    >
                      <span className="font-medium text-foreground capitalize">
                        {agentId} Agent
                      </span>
                      <span className="font-mono text-foreground bg-card px-2 py-0.5 rounded-md border border-border/80 shadow-subtle">
                        {tokens.toLocaleString()} tokens
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-muted-foreground italic p-3 bg-muted/30 rounded-xl text-center">
                    No agent calls logged yet.
                  </div>
                )}
              </div>
            </div>

            {/* Tokens by Model */}
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                <Cpu size={13} className="text-muted-foreground" />
                Models Used
              </h4>
              <div className="space-y-1.5">
                {usage?.models && Object.keys(usage.models).length > 0 ? (
                  Object.entries(usage.models).map(([model, tokens]) => (
                    <div
                      key={model}
                      className="flex items-center justify-between p-2.5 rounded-xl bg-muted/40 border border-border/60 text-xs"
                    >
                      <span className="font-mono text-foreground text-[11px]">
                        {model}
                      </span>
                      <span className="font-mono text-foreground bg-card px-2 py-0.5 rounded-md border border-border/80 shadow-subtle">
                        {tokens.toLocaleString()} tokens
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-muted-foreground italic p-3 bg-muted/30 rounded-xl text-center">
                    No models registered yet.
                  </div>
                )}
              </div>
            </div>

            {/* Recent Activity */}
            {usage?.recent_activity && usage.recent_activity.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Activity size={13} className="text-muted-foreground" />
                  Recent Executions
                </h4>
                <div className="max-h-40 overflow-y-auto space-y-1.5 text-[11px]">
                  {usage.recent_activity.map((item, idx) => (
                    <div
                      key={item.id || idx}
                      className="flex items-center justify-between p-2.5 rounded-xl bg-muted/30 border border-border/50"
                    >
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="font-medium text-foreground capitalize">
                          {item.agent_id}
                        </span>
                        <span className="text-muted-foreground">·</span>
                        <span className="text-muted-foreground font-mono text-[10px]">
                          {item.model}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {item.latency_ms && (
                          <span className="text-[10px] text-muted-foreground">
                            {item.latency_ms}ms
                          </span>
                        )}
                        <span className="font-mono text-foreground font-medium">
                          +{item.total_tokens}t
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-3 bg-muted/30 border-t border-border/60 flex justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 bg-primary text-primary-foreground rounded-lg text-xs font-medium hover:opacity-90 transition shadow-subtle"
            >
              Close
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
