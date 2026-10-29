"use client";

import React from "react";
import { Zap, ShieldCheck, Cpu, Activity } from "lucide-react";
import { motion } from "framer-motion";
import { Highlight } from "@/components/ui/hero-highlight";

export default function MetricsSection() {
  const metrics = [
    {
      title: "Sub-Second AST Routing",
      value: "< 120ms",
      description: "Direct expression evaluation for condition blocks with instant branching.",
      icon: <Zap className="w-5 h-5 text-linear-primary" />,
    },
    {
      title: "Core Agent Specialists",
      value: "4 Swarm Roles",
      description: "Orchestrator, Sonar Researcher, Code Specialist, and Quality Auditor.",
      icon: <Cpu className="w-5 h-5 text-linear-primary" />,
    },
    {
      title: "Deterministic Fallbacks",
      value: "100% Uptime",
      description: "Rich fallback pipeline archetypes prevent UI freezes when rate-limited.",
      icon: <Activity className="w-5 h-5 text-semantic-success" />,
    },
    {
      title: "Audited State Security",
      value: "Zero-Trust",
      description: "End-to-end Supabase PostgreSQL session trees protected by strict RLS.",
      icon: <ShieldCheck className="w-5 h-5 text-semantic-success" />,
    },
  ];

  const technologies = [
    { name: "FastAPI", desc: "Stateless HTTP Core" },
    { name: "Gemini 3.8 Flash", desc: "Interactions API" },
    { name: "Perplexity Sonar", desc: "Live Web Citations" },
    { name: "Supabase", desc: "PostgreSQL & Auth" },
    { name: "Next.js 14", desc: "App Router & SSR" },
    { name: "Framer Motion", desc: "Fluid Physics" },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 py-16">
      <div className="text-center mb-12">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-2xl sm:text-3xl md:text-4xl font-bold text-ink tracking-headline"
        >
          North Star Metrics & <Highlight>Production Standards</Highlight>
        </motion.h2>
        <p className="text-xs sm:text-sm text-ink-subtle mt-2.5 max-w-lg mx-auto">
          Every layer is designed for speed, verifiability, and graceful degradation under high traffic.
        </p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        {metrics.map((item, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.35, delay: idx * 0.08 }}
            className="p-5 rounded-xl border border-hairline bg-surface-1 hover:border-hairline-strong hover:bg-surface-2 transition-colors flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="w-8 h-8 rounded-lg bg-surface-2 border border-hairline flex items-center justify-center">
                  {item.icon}
                </div>
                <span className="text-lg font-bold font-mono text-ink">
                  {item.value}
                </span>
              </div>
              <h3 className="text-xs font-semibold text-ink mb-1 tracking-tight">
                {item.title}
              </h3>
              <p className="text-[11px] text-ink-subtle leading-relaxed">
                {item.description}
              </p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Tech Stack Pills */}
      <div className="p-4 rounded-xl border border-hairline bg-surface-1/60">
        <div className="text-[11px] font-mono text-ink-tertiary uppercase tracking-wider text-center mb-3">
          Powered By Enterprise-Grade Open Stack
        </div>
        <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
          {technologies.map((tech, i) => (
            <div
              key={i}
              className="px-3 py-1.5 rounded-lg bg-surface-2 border border-hairline flex items-center gap-2 text-xs"
            >
              <span className="font-medium text-ink">{tech.name}</span>
              <span className="text-[10px] text-ink-tertiary font-mono">
                • {tech.desc}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
