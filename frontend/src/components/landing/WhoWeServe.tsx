"use client";

import React from "react";
import { GlareCard } from "@/components/ui/glare-card";
import { Bot, Search, Terminal, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import { Highlight } from "@/components/ui/hero-highlight";

export default function WhoWeServe() {
  const agents = [
    {
      title: "Root Orchestrator",
      role: "Swarm Core Master",
      description:
        "Analyzes natural language intent, decomposes objectives into DAG execution plans, and assigns tasks to specialized agents.",
      icon: <Bot className="w-6 h-6 text-linear-primary" />,
      model: "Gemini 3.8 Flash",
    },
    {
      title: "Deep Researcher",
      role: "Web & Citations Specialist",
      description:
        "Extracts verified external sources, scrapes documentation, and links structured citations with Perplexity Sonar.",
      icon: <Search className="w-6 h-6 text-linear-primary" />,
      model: "Perplexity Sonar",
    },
    {
      title: "Python Specialist",
      role: "Code & Math Engine",
      description:
        "Executes data wrangling, automated testing, and mathematical calculations within an isolated, sandboxed Python runtime.",
      icon: <Terminal className="w-6 h-6 text-linear-primary" />,
      model: "Python 3.11 Runtime",
    },
    {
      title: "Security Auditor",
      role: "Governance & Quality Gate",
      description:
        "Evaluates OWASP compliance, inspects AST condition expressions, and verifies DAG outputs before committing briefings.",
      icon: <ShieldCheck className="w-6 h-6 text-semantic-success" />,
      model: "Gemini 4 Argon",
    },
  ];

  return (
    <div id="agents" className="w-full max-w-5xl mx-auto px-4 sm:px-6 py-16">
      <div className="text-center mb-12">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-2xl sm:text-3xl md:text-4xl font-bold text-ink tracking-headline"
        >
          Specialized Roles in the <Highlight>Agent Swarm</Highlight>
        </motion.h2>
        <p className="text-xs sm:text-sm text-ink-subtle mt-2.5 max-w-lg mx-auto">
          Inspect built-in agent specialists, system prompt roles, and execution models.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {agents.map((agent, idx) => (
          <div key={idx} className="w-full">
            <GlareCard className="p-5 flex flex-col justify-between h-full">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-lg bg-surface-2 border border-hairline flex items-center justify-center">
                    {agent.icon}
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-xs bg-surface-2 text-ink-subtle border border-hairline">
                    {agent.model}
                  </span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-ink tracking-tight">
                    {agent.title}
                  </h3>
                  <p className="text-[11px] font-mono text-linear-primary mt-0.5">
                    {agent.role}
                  </p>
                </div>
                <p className="text-xs text-ink-subtle leading-relaxed">
                  {agent.description}
                </p>
              </div>

              <div className="pt-4 border-t border-hairline/60 flex items-center justify-between text-[10px] font-mono text-ink-tertiary">
                <span>Autonomous</span>
                <span className="text-semantic-success">● Ready</span>
              </div>
            </GlareCard>
          </div>
        ))}
      </div>
    </div>
  );
}
