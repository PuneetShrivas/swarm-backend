"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Bot,
  ArrowRight,
  GitBranch,
  Activity,
  Layers,
  ShieldCheck,
  ChevronRight,
  ExternalLink,
  Workflow,
} from "lucide-react";

export default function Home() {
  const capabilities = [
    {
      icon: <Layers className="w-4 h-4 text-linear-primary" />,
      title: "Hierarchical Agent Swarm",
      description:
        "Orchestrator dynamically delegates complex multi-step objectives to specialized researcher, coder, and reviewer agents.",
      badge: "Gemini 2.5 Engine",
    },
    {
      icon: <Workflow className="w-4 h-4 text-linear-primary" />,
      title: "Autonomous Workflow Studio",
      description:
        "Build, test, and visually compose multi-step agent pipelines with DAG visualization, python tools, and isolated runs.",
      badge: "Visual DAG Editor",
    },
    {
      icon: <GitBranch className="w-4 h-4 text-linear-primary" />,
      title: "Tree Conversation Branching",
      description:
        "Branch prompts at any node in the dialogue tree. Compare responses side-by-side with full context isolation.",
      badge: "Non-Linear History",
    },
    {
      icon: <Activity className="w-4 h-4 text-linear-primary" />,
      title: "Live Token Telemetry",
      description:
        "Real-time token usage, latency metrics, and agent delegation counters tracked in Supabase with user RLS isolation.",
      badge: "Audited Usage",
    },
    {
      icon: <ShieldCheck className="w-4 h-4 text-linear-primary" />,
      title: "Enterprise Row-Level Security",
      description:
        "Fully authenticated Supabase user sessions with encrypted state persistence and instant session switching.",
      badge: "Zero-Trust Ready",
    },
  ];

  return (
    <div className="min-h-screen bg-canvas text-ink flex flex-col font-sans selection:bg-linear-primary/25 selection:text-ink">
      {/* Top Linear Nav */}
      <header className="sticky top-0 z-40 w-full bg-canvas/90 backdrop-blur-md border-b border-hairline h-14">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-full flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-7 h-7 rounded-md bg-surface-1 border border-hairline flex items-center justify-center text-linear-primary group-hover:border-hairline-strong transition-colors">
              <Bot className="w-4 h-4" />
            </div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-sm tracking-tight text-ink">
                Swarm
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-sm bg-surface-2 text-ink-subtle border border-hairline">
                v2.0
              </span>
            </div>
          </Link>

          {/* Center Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-ink-subtle">
            <a
              href="#architecture"
              className="hover:text-ink transition-colors"
            >
              Architecture
            </a>
            <a
              href="#capabilities"
              className="hover:text-ink transition-colors"
            >
              Capabilities
            </a>
            <Link
              href="/workflows"
              className="hover:text-ink transition-colors"
            >
              Workflows
            </Link>
          </nav>

          {/* Right Header Actions */}
          <div className="flex items-center gap-2.5 sm:gap-3">
            <Link
              href="/login"
              className="text-xs font-medium text-ink-subtle hover:text-ink px-3 py-1.5 rounded-md hover:bg-surface-1 transition-colors hidden sm:block"
            >
              Sign In
            </Link>
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 text-xs font-medium px-3.5 py-1.5 rounded-md bg-linear-primary hover:bg-linear-hover text-white transition-colors"
            >
              <span>Launch Chat</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-6xl mx-auto px-4 sm:px-6 pt-16 pb-24 flex flex-col items-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="flex flex-col items-center max-w-3xl"
        >
          {/* Linear Status Pill */}
          <div className="inline-flex items-center gap-2 rounded-pill border border-hairline bg-surface-1 px-3 py-1 text-xs font-normal text-ink-muted mb-8">
            <span className="h-1.5 w-1.5 rounded-full bg-semantic-success" />
            <span>Swarm 2.0 • Autonomous Multi-Agent Pipelines & Visual Studio</span>
            <ChevronRight className="w-3 h-3 text-ink-tertiary" />
          </div>

          {/* Main Title with Linear Display Tracking */}
          <h1 className="text-4xl sm:text-6xl font-semibold tracking-display-lg sm:tracking-display-xl mb-6 leading-[1.08] text-ink">
            Linear Intelligence for Multi-Agent Swarms
          </h1>

          <p className="text-base sm:text-lg text-ink-muted mb-10 max-w-2xl font-normal tracking-subhead leading-relaxed">
            Stateless HTTP orchestration, visual DAG workflow pipelines, tree-structured
            branching conversation memory, and audited Supabase telemetry.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto mb-16">
            <Link
              href="/chat"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-linear-primary hover:bg-linear-hover text-white font-medium text-sm transition-colors group"
            >
              <span>Open Chat Interface</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>

            <Link
              href="/workflows"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md border border-hairline bg-surface-1 hover:bg-surface-2 hover:border-hairline-strong text-ink font-medium text-sm transition-colors"
            >
              <Workflow className="w-4 h-4 text-linear-primary" />
              <span>Workflow Studio</span>
            </Link>

            <Link
              href="/login"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md border border-hairline bg-canvas hover:bg-surface-1 text-ink-muted hover:text-ink font-medium text-sm transition-colors"
            >
              <span>Sign In / Account</span>
            </Link>
          </div>
        </motion.div>

        {/* Linear Product Screenshot Frame */}
        <motion.div
          id="architecture"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
          className="w-full rounded-xl border border-hairline bg-surface-1 shadow-card overflow-hidden text-left mb-24"
        >
          {/* Surface Bar */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-hairline bg-surface-2">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-hairline-strong" />
              <span className="w-2.5 h-2.5 rounded-full bg-hairline-strong" />
              <span className="w-2.5 h-2.5 rounded-full bg-hairline-strong" />
              <span className="text-xs font-mono text-ink-subtle ml-2">
                swarm-orchestrator :: live-dag-pipeline
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-xs bg-surface-1 text-ink-muted border border-hairline">
                HTTP REST • GEMINI 2.5
              </span>
            </div>
          </div>

          {/* Clean Technical Terminal Mock */}
          <div className="p-6 sm:p-8 space-y-4 font-mono text-xs">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-md bg-canvas border border-hairline">
              <div className="flex items-center gap-3">
                <span className="px-2 py-0.5 rounded-xs bg-surface-2 text-linear-primary font-medium text-[11px] border border-hairline">
                  OBJECTIVE
                </span>
                <span className="text-ink">
                  &quot;Synthesize latest technical spec, execute python tool test, and output verified briefing.&quot;
                </span>
              </div>
              <span className="text-ink-tertiary text-[11px]">workflow_019a..</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-3.5 rounded-md bg-surface-2 border border-hairline">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-ink">1. Orchestrator</span>
                  <span className="text-[10px] text-semantic-success font-medium">Dispatched</span>
                </div>
                <p className="text-[11px] text-ink-subtle font-sans">
                  Evaluates intent, validates step inputs, resolves dependency DAG.
                </p>
              </div>

              <div className="p-3.5 rounded-md bg-surface-2 border border-hairline">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-ink">2. Python Tool</span>
                  <span className="text-[10px] text-linear-primary font-medium">Executing</span>
                </div>
                <p className="text-[11px] text-ink-subtle font-sans">
                  Sandboxed mathematical computation with strict JSON input/output schema.
                </p>
              </div>

              <div className="p-3.5 rounded-md bg-surface-2 border border-hairline">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-ink">3. Synthesizer</span>
                  <span className="text-[10px] text-ink-subtle font-medium">Queued</span>
                </div>
                <p className="text-[11px] text-ink-subtle font-sans">
                  Compiles verified briefing and records execution metrics into Supabase.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Feature Grid */}
        <div id="capabilities" className="w-full">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-semibold tracking-headline text-ink mb-3">
              Engineered for Autonomous Multi-Agent Operations
            </h2>
            <p className="text-sm text-ink-subtle max-w-xl mx-auto tracking-body">
              Every component is built around enterprise standards: stateless HTTP APIs,
              persistent PostgreSQL session trees, and live streaming telemetry.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-left">
            {capabilities.map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.35, delay: index * 0.06 }}
                className="p-5 rounded-lg border border-hairline bg-surface-1 hover:bg-surface-2 hover:border-hairline-strong transition-colors"
              >
                <div className="flex items-center justify-between mb-3.5">
                  <div className="w-8 h-8 rounded-md bg-surface-2 border border-hairline flex items-center justify-center text-linear-primary">
                    {item.icon}
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-xs bg-surface-2 text-ink-muted border border-hairline">
                    {item.badge}
                  </span>
                </div>
                <h3 className="text-sm font-medium text-ink mb-1.5 tracking-card-title">
                  {item.title}
                </h3>
                <p className="text-xs text-ink-subtle leading-relaxed tracking-body">
                  {item.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </main>

      {/* Linear Footer */}
      <footer className="w-full border-t border-hairline bg-canvas py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-ink-subtle">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-semantic-success" />
            <span className="text-ink-muted">All swarm agents operational</span>
            <span className="text-hairline">|</span>
            <span>FastAPI + Gemini 2.5 + Supabase</span>
          </div>

          <div className="flex items-center gap-6">
            <Link href="/chat" className="hover:text-ink transition-colors">
              Chat Interface
            </Link>
            <Link href="/workflows" className="hover:text-ink transition-colors">
              Workflows
            </Link>
            <Link href="/login" className="hover:text-ink transition-colors">
              Authentication
            </Link>
            <a
              href="https://github.com/PuneetShrivas/swarm-backend"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 hover:text-ink transition-colors"
            >
              <span>GitHub</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
