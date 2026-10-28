"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Bot,
  Sparkles,
  ArrowRight,
  GitBranch,
  Activity,
  Layers,
  ShieldCheck,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";

export default function Home() {
  const capabilities = [
    {
      icon: <Layers className="w-5 h-5 text-primary" />,
      title: "Hierarchical Agent Swarm",
      description:
        "Orchestrator dynamically delegates complex multi-step objectives to specialized researcher, coder, and reviewer agents.",
      badge: "Gemini 2.5 Engine",
    },
    {
      icon: <GitBranch className="w-5 h-5 text-primary" />,
      title: "Tree Conversation Branching",
      description:
        "Branch prompts at any node in the dialogue tree. Compare responses side-by-side with full context isolation.",
      badge: "Non-Linear History",
    },
    {
      icon: <Activity className="w-5 h-5 text-primary" />,
      title: "Live Token Telemetry",
      description:
        "Real-time token usage, latency metrics, and agent delegation counters tracked in Supabase with user RLS isolation.",
      badge: "Audited Usage",
    },
    {
      icon: <ShieldCheck className="w-5 h-5 text-primary" />,
      title: "Enterprise Row-Level Security",
      description:
        "Fully authenticated Supabase user sessions with encrypted state persistence and instant session switching.",
      badge: "Zero-Trust Ready",
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col relative overflow-hidden transition-colors duration-300">
      {/* Background Grids & Radial Glow Mesh */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--foreground)/0.03)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--foreground)/0.03)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />
      <div
        className="absolute -top-40 left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full blur-[120px] pointer-events-none opacity-40 transition-colors duration-500"
        style={{
          background: "radial-gradient(circle, var(--glow-color) 0%, transparent 70%)",
        }}
      />

      {/* Top Glass Navbar */}
      <header className="sticky top-0 z-40 w-full glass-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary shadow-subtle group-hover:scale-105 transition-transform">
              <Bot className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-sm tracking-tight text-foreground flex items-center gap-1.5">
                Swarm Intelligence
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-primary/15 text-primary border border-primary/20">
                  v2.0
                </span>
              </span>
              <span className="text-[11px] text-muted-foreground hidden sm:block">
                Autonomous Multi-Agent Architecture
              </span>
            </div>
          </Link>

          {/* Center Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-muted-foreground">
            <a
              href="#architecture"
              className="hover:text-foreground transition-colors"
            >
              Architecture
            </a>
            <a
              href="#capabilities"
              className="hover:text-foreground transition-colors"
            >
              Capabilities
            </a>
            <a
              href="#telemetry"
              className="hover:text-foreground transition-colors"
            >
              Telemetry
            </a>
          </nav>

          {/* Right Header Actions */}
          <div className="flex items-center gap-2.5 sm:gap-3">
            <ThemeSwitcher />
            <Link
              href="/login"
              className="text-xs font-medium text-muted-foreground hover:text-foreground px-3 py-1.5 rounded-lg hover:bg-accent/60 transition-colors hidden sm:block"
            >
              Sign In
            </Link>
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-3.5 py-1.5 rounded-lg bg-primary text-primary-foreground hover:opacity-90 shadow-sm transition-all"
            >
              <span>Launch Swarm</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-20 flex flex-col items-center text-center relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="flex flex-col items-center max-w-3xl"
        >
          {/* Status Pill */}
          <div className="inline-flex items-center gap-2 rounded-full border border-border/80 bg-card/80 px-3.5 py-1 text-xs font-medium text-muted-foreground mb-8 backdrop-blur-md shadow-subtle">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Agent Swarm 2.0 • Gemini 2.5 & Supabase Tree Sessions</span>
            <ChevronRight className="w-3 h-3 text-muted-foreground" />
          </div>

          {/* Main Title */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight mb-6 leading-[1.1]">
            Orchestrate Autonomous{" "}
            <span className="bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
              AI Agent Swarms
            </span>{" "}
            with Precision
          </h1>

          <p className="text-base sm:text-lg text-muted-foreground mb-10 max-w-2xl font-normal leading-relaxed">
            Deploy collaborative AI networks with dynamic supervisor routing, tree-structured
            branching conversation memory, Supabase persistence, and live token usage telemetry.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center gap-3.5 w-full sm:w-auto mb-16">
            <Link
              href="/chat"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:opacity-95 shadow-md shadow-primary/20 transition-all group"
            >
              <span>Open Swarm Workspace</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/login"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-border bg-card/70 hover:bg-accent/70 text-foreground font-medium text-sm transition-all backdrop-blur-sm"
            >
              <Sparkles className="w-4 h-4 text-primary" />
              <span>Connect Supabase Account</span>
            </Link>
          </div>
        </motion.div>

        {/* Live Swarm Dispatch Mock / Blueprint Preview */}
        <motion.div
          id="architecture"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15, ease: "easeOut" }}
          className="w-full max-w-4xl rounded-2xl border border-border/80 bg-card/60 backdrop-blur-xl shadow-card overflow-hidden text-left mb-20"
        >
          {/* Terminal / Workspace Title Bar */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border/60 bg-muted/40">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-destructive/60" />
              <span className="w-3 h-3 rounded-full bg-amber-500/60" />
              <span className="w-3 h-3 rounded-full bg-emerald-500/60" />
              <span className="text-xs font-mono text-muted-foreground ml-2 font-medium">
                swarm-orchestrator :: live-dispatch
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                Auto Routing
              </span>
            </div>
          </div>

          {/* Interactive Agent Routing Flow Diagram Preview */}
          <div className="p-6 sm:p-8 space-y-4 font-mono text-xs">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-lg bg-background/80 border border-border/60">
              <div className="flex items-center gap-3">
                <span className="px-2 py-1 rounded bg-primary/15 text-primary font-semibold">
                  USER_PROMPT
                </span>
                <span className="text-foreground">
                  &quot;Analyze quarterly performance data and generate an executive summary.&quot;
                </span>
              </div>
              <span className="text-muted-foreground text-[11px]">session_018f..</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-3.5 rounded-lg bg-card border border-border/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-primary">1. Orchestrator</span>
                  <span className="text-[10px] text-emerald-500 font-medium">Dispatched</span>
                </div>
                <p className="text-[11px] text-muted-foreground font-sans">
                  Evaluates intent, checks permissions, plans execution DAG.
                </p>
              </div>

              <div className="p-3.5 rounded-lg bg-card border border-border/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-primary">2. Researcher</span>
                  <span className="text-[10px] text-blue-500 font-medium">Active</span>
                </div>
                <p className="text-[11px] text-muted-foreground font-sans">
                  Queries vector stores, synthesizes evidence, verifies facts.
                </p>
              </div>

              <div className="p-3.5 rounded-lg bg-card border border-border/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-primary">3. Synthesizer</span>
                  <span className="text-[10px] text-amber-500 font-medium">Queued</span>
                </div>
                <p className="text-[11px] text-muted-foreground font-sans">
                  Generates markdown report with branching options.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Feature Capabilities Grid */}
        <div id="capabilities" className="w-full max-w-5xl">
          <div className="text-center mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-3">
              Engineered for Autonomous Multi-Agent Operations
            </h2>
            <p className="text-sm text-muted-foreground max-w-xl mx-auto">
              Every component is built around enterprise standards: stateless HTTP APIs,
              persistent PostgreSQL session trees, and live streaming telemetry.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-left">
            {capabilities.map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="p-6 rounded-2xl border border-border/70 bg-card/60 backdrop-blur-md hover:bg-card/90 hover:border-primary/40 hover:shadow-card transition-all group"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/25 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                    {item.icon}
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border/40">
                    {item.badge}
                  </span>
                </div>
                <h3 className="text-base font-semibold text-foreground mb-2">
                  {item.title}
                </h3>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  {item.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-border/60 bg-card/40 backdrop-blur-md py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>All swarm agents operational</span>
            <span className="text-border">|</span>
            <span>FastAPI + Gemini 2.5 + Supabase</span>
          </div>

          <div className="flex items-center gap-6">
            <Link href="/chat" className="hover:text-foreground transition-colors">
              Chat Interface
            </Link>
            <Link href="/login" className="hover:text-foreground transition-colors">
              Authentication
            </Link>
            <a
              href="https://github.com/PuneetShrivas/swarm-backend"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 hover:text-foreground transition-colors"
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
