"use client";

import React, { useState } from "react";
import { Bot, CheckCircle2, XCircle } from "lucide-react";
import { motion } from "framer-motion";
import { Highlight } from "@/components/ui/hero-highlight";

export default function CompareResponse() {
  const [activeTab, setActiveTab] = useState<"swarm" | "single">("swarm");

  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 py-12 relative z-20">
      <div className="text-center mb-8">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-2xl sm:text-3xl md:text-4xl font-bold text-ink tracking-headline"
        >
          From Monolithic Bottlenecks to{" "}
          <Highlight>Autonomous Swarms</Highlight>
        </motion.h2>
        <p className="text-xs sm:text-sm text-ink-subtle mt-2.5 max-w-xl mx-auto">
          See how hierarchical agent swarms break complex multi-step objectives into verifiable, parallel execution DAGs.
        </p>

        {/* Mobile View Toggle */}
        <div className="inline-flex sm:hidden mt-4 p-1 rounded-md bg-surface-2 border border-hairline">
          <button
            onClick={() => setActiveTab("single")}
            className={`px-3 py-1 text-xs rounded font-medium transition-colors ${
              activeTab === "single"
                ? "bg-surface-3 text-ink"
                : "text-ink-subtle"
            }`}
          >
            Single Agent
          </button>
          <button
            onClick={() => setActiveTab("swarm")}
            className={`px-3 py-1 text-xs rounded font-medium transition-colors ${
              activeTab === "swarm"
                ? "bg-linear-primary text-white"
                : "text-ink-subtle"
            }`}
          >
            Swarm 2.0
          </button>
        </div>
      </div>

      {/* Side-by-Side Comparison Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Left: Single Agent Bottleneck */}
        <div
          className={`flex flex-col rounded-xl border border-hairline bg-surface-1 p-5 ${
            activeTab === "single" ? "block" : "hidden sm:flex"
          }`}
        >
          <div className="flex items-center justify-between pb-3 border-b border-hairline mb-3">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-red-400/80" />
              <span className="text-xs font-semibold text-ink-subtle">
                Standard Single-Agent LLM
              </span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-xs bg-red-950/40 text-red-400 border border-red-900/30">
              Unverified / Hallucination Risk
            </span>
          </div>

          <div className="space-y-3 flex-1 font-mono text-xs text-ink-muted">
            <div className="p-2.5 rounded-md bg-surface-2 border border-hairline">
              <span className="text-[10px] uppercase text-ink-tertiary block mb-1">
                User Objective
              </span>
              <p className="text-ink text-xs">
                &quot;Run memory leak benchmark on port 8000, verify OWASP compliance, and export certified briefing.&quot;
              </p>
            </div>

            <div className="p-3 rounded-md bg-canvas border border-hairline text-ink-subtle space-y-2 text-[11px] font-sans">
              <div className="flex items-start gap-1.5 text-red-400">
                <XCircle size={14} className="shrink-0 mt-0.5" />
                <span>Single context window saturates without specialist routing</span>
              </div>
              <div className="flex items-start gap-1.5 text-red-400">
                <XCircle size={14} className="shrink-0 mt-0.5" />
                <span>Hallucinates benchmark statistics instead of executing sandboxed Python code</span>
              </div>
              <div className="flex items-start gap-1.5 text-red-400">
                <XCircle size={14} className="shrink-0 mt-0.5" />
                <span>Zero telemetry, no state checkpoints, high failure rate on step errors</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Swarm 2.0 Hierarchical Pipeline */}
        <div
          className={`flex flex-col rounded-xl border border-linear-primary/40 bg-surface-1 p-5 shadow-[0_0_24px_rgba(94,106,210,0.12)] ${
            activeTab === "swarm" ? "block" : "hidden sm:flex"
          }`}
        >
          <div className="flex items-center justify-between pb-3 border-b border-hairline mb-3">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-semantic-success" />
              <span className="text-xs font-semibold text-ink flex items-center gap-1.5">
                <Bot size={13} className="text-linear-primary" /> Swarm 2.0 Orchestrator
              </span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-xs bg-linear-primary/20 text-linear-hover border border-linear-primary/30">
              Deterministic DAG
            </span>
          </div>

          <div className="space-y-2.5 flex-1 font-mono text-xs">
            <div className="p-2.5 rounded-md bg-surface-2 border border-hairline">
              <span className="text-[10px] uppercase text-ink-tertiary block mb-1">
                User Objective
              </span>
              <p className="text-ink text-xs">
                &quot;Run memory leak benchmark on port 8000, verify OWASP compliance, and export certified briefing.&quot;
              </p>
            </div>

            <div className="space-y-1.5 font-sans text-[11px]">
              <div className="p-2 rounded-md bg-canvas border border-hairline flex items-center justify-between">
                <span className="text-ink font-medium">1. Intent Decomposed</span>
                <span className="text-[10px] font-mono text-semantic-success">3 Parallel Steps</span>
              </div>
              <div className="p-2 rounded-md bg-canvas border border-hairline flex items-center justify-between">
                <span className="text-ink font-medium">2. Python Sandbox Benchmark</span>
                <span className="text-[10px] font-mono text-linear-primary">2.4ms • 0 Errors</span>
              </div>
              <div className="p-2 rounded-md bg-canvas border border-hairline flex items-center justify-between">
                <span className="text-ink font-medium">3. OWASP Security Audit</span>
                <span className="text-[10px] font-mono text-semantic-success">Passed • 100% Verified</span>
              </div>
            </div>

            <div className="flex items-center gap-1.5 text-semantic-success text-[11px] font-sans pt-1">
              <CheckCircle2 size={13} />
              <span>Full PostgreSQL telemetry recorded with Supabase RLS isolation.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
