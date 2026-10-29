"use client";

import React from "react";
import { Timeline } from "@/components/ui/timeline";
import { motion } from "framer-motion";
import { Highlight } from "@/components/ui/hero-highlight";

export default function TimelineSection() {
  const data = [
    {
      title: "01. Objective Ingestion",
      content: (
        <div className="space-y-3 font-sans">
          <p className="text-xs sm:text-sm text-ink-muted leading-relaxed">
            The user provides an objective in natural language or launches a workflow template. The root orchestrator validates input parameters, checks user authentication against Supabase RLS, and initializes an execution context.
          </p>
          <div className="p-3 rounded-lg bg-surface-1 border border-hairline font-mono text-xs text-ink-subtle">
            <span className="text-linear-primary font-medium">orchestrator.parse()</span>
            <div className="text-[11px] text-ink-tertiary mt-1">
              &gt; Context initialized • Session UUID #9a4c53f7 • RLS verified
            </div>
          </div>
        </div>
      ),
    },
    {
      title: "02. DAG Synthesis",
      content: (
        <div className="space-y-3 font-sans">
          <p className="text-xs sm:text-sm text-ink-muted leading-relaxed">
            Using Gemini 3.8 Flash, Swarm decomposes the objective into an optimal directed acyclic graph (DAG) containing agent steps, condition evaluations, python sandboxes, and artifact collectors.
          </p>
          <div className="p-3 rounded-lg bg-surface-1 border border-hairline font-mono text-xs text-ink-subtle">
            <span className="text-linear-primary font-medium">workflow.compile_dag()</span>
            <div className="text-[11px] text-ink-tertiary mt-1">
              &gt; 4 nodes linked • 0 cycles detected • Condition branch targets mapped
            </div>
          </div>
        </div>
      ),
    },
    {
      title: "03. Parallel Delegation",
      content: (
        <div className="space-y-3 font-sans">
          <p className="text-xs sm:text-sm text-ink-muted leading-relaxed">
            Specialized agents execute concurrently. The Deep Researcher gathers external facts with Perplexity Sonar while the Python Specialist executes sandboxed calculations and tests.
          </p>
          <div className="p-3 rounded-lg bg-surface-1 border border-hairline font-mono text-xs text-ink-subtle">
            <span className="text-linear-primary font-medium">agents.dispatch_parallel()</span>
            <div className="text-[11px] text-ink-tertiary mt-1">
              &gt; Researcher dispatched • Python runner active • AST condition gate evaluated True
            </div>
          </div>
        </div>
      ),
    },
    {
      title: "04. Verified Synthesis",
      content: (
        <div className="space-y-3 font-sans">
          <p className="text-xs sm:text-sm text-ink-muted leading-relaxed">
            The quality auditor inspects all intermediate outputs, compiles citations, records token and duration telemetry, and persists the session tree into PostgreSQL.
          </p>
          <div className="p-3 rounded-lg bg-surface-1 border border-hairline font-mono text-xs text-ink-subtle">
            <span className="text-semantic-success font-medium">telemetry.commit()</span>
            <div className="text-[11px] text-ink-tertiary mt-1">
              &gt; 3,420 tokens recorded • 412ms latency • Run state: SUCCESS
            </div>
          </div>
        </div>
      ),
    },
  ];

  return (
    <div id="workflows" className="w-full max-w-5xl mx-auto px-4 sm:px-6 py-16">
      <div className="text-center mb-8">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-2xl sm:text-3xl md:text-4xl font-bold text-ink tracking-headline"
        >
          Lifecycle of an <Highlight>Autonomous Execution</Highlight>
        </motion.h2>
        <p className="text-xs sm:text-sm text-ink-subtle mt-2.5 max-w-lg mx-auto">
          Trace how instructions journey through parsing, DAG compilation, parallel agent delegation, and audited telemetry.
        </p>
      </div>

      <Timeline data={data} />
    </div>
  );
}
