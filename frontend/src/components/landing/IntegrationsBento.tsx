"use client";

import React from "react";
import { BentoGrid, BentoGridItem } from "@/components/ui/bento-grid";
import {
  Bot,
  Workflow,
  GitBranch,
  Code2,
  Activity,
  Sparkles,
  ShieldCheck,
} from "lucide-react";
import { motion } from "framer-motion";
import { Highlight } from "@/components/ui/hero-highlight";

export default function IntegrationsBento() {
  const items = [
    {
      title: "Hierarchical Agent Swarm Orchestration",
      description:
        "Root orchestrator decomposes natural language instructions into dynamic execution DAGs, routing tasks to deep researchers, coders, and quality reviewers.",
      header: (
        <div className="flex flex-1 w-full h-full min-h-[6rem] rounded-lg bg-gradient-to-br from-surface-2 to-surface-3 border border-hairline p-3 flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-mono text-ink-subtle">
            <span className="flex items-center gap-1.5 text-linear-primary font-medium">
              <Sparkles size={12} /> Live Multi-Agent Swarm
            </span>
            <span className="text-[10px] bg-surface-1 px-2 py-0.5 rounded-xs border border-hairline">
              Gemini 3.8 Flash
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center text-[10px] font-mono">
            <div className="p-2 rounded bg-surface-1 border border-hairline text-ink">
              Orchestrator
            </div>
            <div className="p-2 rounded bg-surface-1 border border-hairline text-ink">
              Sonar Search
            </div>
            <div className="p-2 rounded bg-surface-1 border border-hairline text-ink">
              Python Runner
            </div>
          </div>
        </div>
      ),
      className: "md:col-span-2",
      icon: <Bot className="h-4 w-4 text-linear-primary" />,
    },
    {
      title: "Visual DAG Workflow Studio",
      description:
        "Compose, test, and step-through DAG pipelines with live node graphs, condition branching, and unit-level deterministic mocking.",
      header: (
        <div className="flex flex-1 w-full h-full min-h-[6rem] rounded-lg bg-surface-2 border border-hairline p-3 flex-col items-center justify-center text-center">
          <Workflow className="w-8 h-8 text-linear-primary mb-2 opacity-80" />
          <span className="text-xs font-mono text-ink-muted">
            Drag & Drop Node Canvas
          </span>
        </div>
      ),
      className: "md:col-span-1",
      icon: <Workflow className="h-4 w-4 text-linear-primary" />,
    },
    {
      title: "Non-Linear Tree Dialogue Memory",
      description:
        "Branch conversations at any message node. Fork creative directions and compare agent alternatives without losing session state.",
      header: (
        <div className="flex flex-1 w-full h-full min-h-[6rem] rounded-lg bg-surface-2 border border-hairline p-3 flex-col items-center justify-center text-center">
          <GitBranch className="w-8 h-8 text-linear-primary mb-2 opacity-80" />
          <span className="text-xs font-mono text-ink-muted">
            Non-Destructive Forking
          </span>
        </div>
      ),
      className: "md:col-span-1",
      icon: <GitBranch className="h-4 w-4 text-linear-primary" />,
    },
    {
      title: "Sandboxed Python Code Execution",
      description:
        "Execute automated mathematical scripts, data parsing, and transformation algorithms safely in-process with strict runtime timeouts.",
      header: (
        <div className="flex flex-1 w-full h-full min-h-[6rem] rounded-lg bg-surface-2 border border-hairline p-3 flex-col items-center justify-center text-center">
          <Code2 className="w-8 h-8 text-linear-primary mb-2 opacity-80" />
          <span className="text-xs font-mono text-ink-muted">
            Isolated In-Process Sandbox
          </span>
        </div>
      ),
      className: "md:col-span-1",
      icon: <Code2 className="h-4 w-4 text-linear-primary" />,
    },
    {
      title: "Audited Token & Cost Telemetry",
      description:
        "Every prompt token, latency millisecond, and agent delegation event is securely committed to Supabase with user Row-Level Security.",
      header: (
        <div className="flex flex-1 w-full h-full min-h-[6rem] rounded-lg bg-surface-2 border border-hairline p-3 flex-col items-center justify-center text-center">
          <Activity className="w-8 h-8 text-semantic-success mb-2 opacity-80" />
          <span className="text-xs font-mono text-ink-muted">
            Real-Time Supabase RLS
          </span>
        </div>
      ),
      className: "md:col-span-1",
      icon: <ShieldCheck className="h-4 w-4 text-semantic-success" />,
    },
  ];

  return (
    <div id="architecture" className="w-full max-w-5xl mx-auto px-4 sm:px-6 py-16">
      <div className="text-center mb-10">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-2xl sm:text-3xl md:text-4xl font-bold text-ink tracking-headline"
        >
          Engineered for <Highlight>Multi-Agent Scale</Highlight>
        </motion.h2>
        <p className="text-xs sm:text-sm text-ink-subtle mt-2.5 max-w-lg mx-auto">
          Five cohesive architectural pillars designed for production AI reliability and zero-trust security.
        </p>
      </div>

      <BentoGrid className="max-w-5xl mx-auto">
        {items.map((item, i) => (
          <BentoGridItem
            key={i}
            title={item.title}
            description={item.description}
            header={item.header}
            className={item.className}
            icon={item.icon}
          />
        ))}
      </BentoGrid>
    </div>
  );
}
