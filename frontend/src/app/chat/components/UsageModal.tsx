'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, Zap, Activity, Cpu, Bot, RefreshCw } from 'lucide-react';
import { UserUsageSummary } from '../types';

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
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.15 }}
          className="bg-white rounded-2xl shadow-2xl border border-slate-200/80 max-w-lg w-full overflow-hidden flex flex-col max-h-[85vh]"
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-600">
                <Zap size={16} />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800 text-sm">
                  User Usage & Telemetry
                </h3>
                <p className="text-[11px] text-slate-400">
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
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition disabled:opacity-50"
              >
                <RefreshCw size={15} className={isLoading ? 'animate-spin' : ''} />
              </button>
              <button
                type="button"
                onClick={onClose}
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="p-6 overflow-y-auto space-y-5 flex-1">
            {/* Top Metric Cards */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50/40 border border-blue-100">
                <div className="text-[11px] font-medium text-blue-600 uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Zap size={12} /> Total Tokens
                </div>
                <div className="text-2xl font-bold text-slate-900">
                  {totalTokens.toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  Input prompt + output response
                </div>
              </div>

              <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-50 to-teal-50/40 border border-emerald-100">
                <div className="text-[11px] font-medium text-emerald-600 uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Activity size={12} /> Swarm Queries
                </div>
                <div className="text-2xl font-bold text-slate-900">
                  {totalRequests.toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  Completed agent turns
                </div>
              </div>
            </div>

            {/* Tokens by Agent */}
            <div>
              <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                <Bot size={13} className="text-slate-400" />
                Consumption by Agent
              </h4>
              <div className="space-y-1.5">
                {usage?.agents && Object.keys(usage.agents).length > 0 ? (
                  Object.entries(usage.agents).map(([agentId, tokens]) => (
                    <div
                      key={agentId}
                      className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs"
                    >
                      <span className="font-medium text-slate-700 capitalize">
                        {agentId} Agent
                      </span>
                      <span className="font-mono text-slate-600 bg-white px-2 py-0.5 rounded-md border border-slate-200">
                        {tokens.toLocaleString()} tokens
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-slate-400 italic p-2 bg-slate-50 rounded-lg">
                    No agent calls logged yet.
                  </div>
                )}
              </div>
            </div>

            {/* Tokens by Model */}
            <div>
              <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                <Cpu size={13} className="text-slate-400" />
                Models Used
              </h4>
              <div className="space-y-1.5">
                {usage?.models && Object.keys(usage.models).length > 0 ? (
                  Object.entries(usage.models).map(([model, tokens]) => (
                    <div
                      key={model}
                      className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs"
                    >
                      <span className="font-mono text-slate-700 text-[11px]">
                        {model}
                      </span>
                      <span className="font-mono text-slate-600 bg-white px-2 py-0.5 rounded-md border border-slate-200">
                        {tokens.toLocaleString()} tokens
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-slate-400 italic p-2 bg-slate-50 rounded-lg">
                    No models registered yet.
                  </div>
                )}
              </div>
            </div>

            {/* Recent Activity */}
            {usage?.recent_activity && usage.recent_activity.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Activity size={13} className="text-slate-400" />
                  Recent Executions
                </h4>
                <div className="max-h-40 overflow-y-auto space-y-1.5 text-[11px]">
                  {usage.recent_activity.map((item, idx) => (
                    <div
                      key={item.id || idx}
                      className="flex items-center justify-between p-2 rounded-lg bg-slate-50/80 border border-slate-100"
                    >
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="font-medium text-slate-800 capitalize">
                          {item.agent_id}
                        </span>
                        <span className="text-slate-400">·</span>
                        <span className="text-slate-500 font-mono text-[10px]">
                          {item.model}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {item.latency_ms && (
                          <span className="text-[10px] text-slate-400">
                            {item.latency_ms}ms
                          </span>
                        )}
                        <span className="font-mono text-slate-700 font-medium">
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
          <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-medium hover:bg-slate-800 transition"
            >
              Close
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
