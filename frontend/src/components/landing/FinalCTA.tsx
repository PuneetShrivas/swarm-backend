"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { BackgroundBeams } from "@/components/ui/background-beams";
import { ArrowRight, Bot, Workflow } from "lucide-react";
import Link from "next/link";

export default function FinalCTA() {
  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 py-16">
      <div className="relative rounded-2xl border border-hairline bg-surface-1 p-8 sm:p-12 md:p-16 overflow-hidden flex flex-col items-center justify-center text-center shadow-2xl">
        <BackgroundBeams />

        <div className="relative z-10 max-w-2xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-hairline bg-surface-2 px-3 py-1 text-xs text-ink-subtle">
            <span className="w-2 h-2 rounded-full bg-semantic-success animate-pulse" />
            <span>FastAPI + Gemini 3.8 + Supabase Ready</span>
          </div>

          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-ink leading-tight">
            Orchestrate Your First Autonomous Swarm Today
          </h2>

          <p className="text-xs sm:text-sm md:text-base text-ink-subtle max-w-lg mx-auto leading-relaxed">
            Stateless HTTP orchestration, visual DAG workflow studio, non-linear dialogue branching, and real-time execution telemetry.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
            <Link href="/chat" className="w-full sm:w-auto">
              <Button size="lg" className="w-full sm:w-auto gap-2 text-xs sm:text-sm">
                <Bot size={16} />
                <span>Launch Chat Interface</span>
                <ArrowRight size={14} />
              </Button>
            </Link>

            <Link href="/workflows" className="w-full sm:w-auto">
              <Button
                variant="outline"
                size="lg"
                className="w-full sm:w-auto gap-2 text-xs sm:text-sm"
              >
                <Workflow size={16} className="text-linear-primary" />
                <span>Open Workflow Studio</span>
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
