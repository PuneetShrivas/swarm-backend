"use client";

import React, { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Navbar,
  NavBody,
  NavItems,
  MobileNav,
  NavbarLogo,
  NavbarButton,
  MobileNavHeader,
  MobileNavToggle,
  MobileNavMenu,
} from "@/components/ui/resizable-navbar";
import { Boxes } from "@/components/ui/background-boxes";
import { ContainerTextFlip } from "@/components/ui/container-text-flip";
import { Highlight } from "@/components/ui/hero-highlight";
import { CardSpotlight } from "@/components/ui/card-spotlight";
import { Button } from "@/components/ui/button";
import CompareResponse from "@/components/landing/CompareResponse";
import IntegrationsBento from "@/components/landing/IntegrationsBento";
import TimelineSection from "@/components/landing/TimelineSection";
import WhoWeServe from "@/components/landing/WhoWeServe";
import MetricsSection from "@/components/landing/MetricsSection";
import TestimonialsSection from "@/components/landing/TestimonialsSection";
import PricingSection from "@/components/landing/PricingSection";
import FinalCTA from "@/components/landing/FinalCTA";
import FooterSection from "@/components/landing/FooterSection";
import {
  Bot,
  Workflow,
  ArrowRight,
  ChevronRight,
  CheckCircle2,
  Sparkles,
} from "lucide-react";

export default function Home() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { name: "Architecture", link: "#architecture" },
    { name: "Workflows", link: "#workflows" },
    { name: "Agents", link: "#agents" },
    { name: "Pricing", link: "#pricing" },
  ];

  return (
    <div className="min-h-screen bg-canvas text-ink flex flex-col font-sans selection:bg-linear-primary/25 selection:text-ink overflow-x-hidden">
      {/* Floating Dynamic Resizable Navbar */}
      <Navbar>
        <NavBody>
          <NavbarLogo />
          <NavItems items={navItems} />
          <div className="flex items-center gap-2">
            <Link href="/login" className="hidden sm:inline-block">
              <NavbarButton variant="outline">Sign In</NavbarButton>
            </Link>
            <Link href="/chat">
              <NavbarButton variant="primary">Launch Swarm</NavbarButton>
            </Link>
          </div>
        </NavBody>

        <MobileNav>
          <MobileNavHeader>
            <NavbarLogo />
            <MobileNavToggle
              isOpen={isMobileMenuOpen}
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            />
          </MobileNavHeader>

          <MobileNavMenu
            isOpen={isMobileMenuOpen}
            onClose={() => setIsMobileMenuOpen(false)}
          >
            {navItems.map((item, idx) => (
              <a
                key={`mobile-nav-${idx}`}
                href={item.link}
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-sm font-medium text-ink-subtle hover:text-ink transition-colors"
              >
                {item.name}
              </a>
            ))}
            <div className="flex flex-col gap-2 w-full pt-2 border-t border-hairline">
              <Link
                href="/login"
                onClick={() => setIsMobileMenuOpen(false)}
                className="w-full text-center py-2 text-xs font-medium text-ink bg-surface-2 rounded-md border border-hairline"
              >
                Sign In
              </Link>
              <Link
                href="/chat"
                onClick={() => setIsMobileMenuOpen(false)}
                className="w-full text-center py-2 text-xs font-medium text-white bg-linear-primary rounded-md"
              >
                Launch Swarm
              </Link>
            </div>
          </MobileNavMenu>
        </MobileNav>
      </Navbar>

      {/* Hero Section with Interactive Background Boxes */}
      <section className="relative w-full min-h-[580px] sm:min-h-[640px] flex flex-col items-center justify-center text-center px-4 sm:px-6 overflow-hidden pt-8 pb-16">
        <Boxes />
        <div className="pointer-events-none absolute inset-0 bg-canvas [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black_75%)]" />

        <div className="relative z-20 max-w-4xl mx-auto flex flex-col items-center">
          {/* Status Badge */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="inline-flex items-center gap-2 rounded-full border border-hairline bg-surface-1/90 px-3.5 py-1 text-xs text-ink-subtle backdrop-blur-sm mb-6"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-semantic-success animate-pulse" />
            <span>Swarm 2.0 • Autonomous Multi-Agent Pipelines & Visual Studio</span>
            <ChevronRight size={12} className="text-ink-tertiary" />
          </motion.div>

          {/* Display Heading with Highlight */}
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-3xl sm:text-5xl md:text-6xl font-bold tracking-tight text-ink leading-[1.1] mb-6"
          >
            Linear Intelligence for <br className="hidden sm:block" />
            <Highlight>Multi-Agent Swarms</Highlight>
          </motion.h1>

          {/* Model Flipper Line */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="flex flex-wrap items-center justify-center gap-2 text-xs sm:text-sm text-ink-subtle mb-6"
          >
            <span>Orchestrating top models:</span>
            <ContainerTextFlip
              words={[
                "Gemini 3.8 Flash",
                "Gemini 4 Argon",
                "Sonar Deep Research",
                "Claude 3.7 Sonnet",
                "GPT-4o",
              ]}
              interval={2500}
            />
          </motion.div>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.25 }}
            className="text-xs sm:text-base text-ink-muted max-w-xl mx-auto mb-8 leading-relaxed font-sans"
          >
            Stateless HTTP orchestration, visual DAG workflow pipelines, tree-structured
            branching conversation memory, and audited Supabase telemetry.
          </motion.p>

          {/* Hero CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto"
          >
            <Link href="/chat" className="w-full sm:w-auto">
              <Button size="lg" className="w-full sm:w-auto gap-2 text-xs sm:text-sm">
                <Bot size={15} />
                <span>Open Chat Interface</span>
                <ArrowRight size={14} />
              </Button>
            </Link>

            <Link href="/workflows" className="w-full sm:w-auto">
              <Button
                variant="outline"
                size="lg"
                className="w-full sm:w-auto gap-2 text-xs sm:text-sm"
              >
                <Workflow size={15} className="text-linear-primary" />
                <span>Workflow Studio</span>
              </Button>
            </Link>

            <Link href="/agents" className="w-full sm:w-auto">
              <Button
                variant="secondary"
                size="lg"
                className="w-full sm:w-auto gap-2 text-xs sm:text-sm"
              >
                <Sparkles size={14} className="text-linear-primary" />
                <span>Agent Roster</span>
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Interactive Terminal Comparison */}
      <CompareResponse />

      {/* Dual Engine Spotlight Section */}
      <section className="w-full max-w-5xl mx-auto px-4 sm:px-6 py-16 relative z-20">
        <div className="text-center mb-10">
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
            className="text-2xl sm:text-3xl md:text-4xl font-bold text-ink tracking-headline"
          >
            Two Unified Engines. <Highlight>One Autonomous Platform.</Highlight>
          </motion.h2>
          <p className="text-xs sm:text-sm text-ink-subtle mt-2.5 max-w-lg mx-auto">
            Seamlessly transition between interactive conversational chat and production visual DAG pipeline automation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <CardSpotlight className="h-full flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-10 h-10 rounded-lg bg-surface-2 border border-hairline flex items-center justify-center text-linear-primary">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-linear-primary font-semibold">
                  Engine 01
                </span>
                <h3 className="text-base sm:text-lg font-bold text-ink mt-0.5">
                  Hierarchical Swarm Orchestrator
                </h3>
              </div>
              <p className="text-xs text-ink-subtle leading-relaxed">
                Decompose complex prompts dynamically into sub-tasks. Direct intent through specialized agents with Perplexity Sonar citations and non-linear branching memory.
              </p>
              <ul className="space-y-2 text-xs text-ink-muted pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 size={13} className="text-linear-primary shrink-0" />
                  <span>Stateless FastAPI HTTP REST orchestration</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 size={13} className="text-linear-primary shrink-0" />
                  <span>Perplexity Sonar citations and web discovery</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 size={13} className="text-linear-primary shrink-0" />
                  <span>Dialogue tree conversation branching & checkpoints</span>
                </li>
              </ul>
            </div>
            <div className="pt-6">
              <Link href="/chat">
                <Button variant="outline" className="w-full text-xs gap-1.5">
                  <span>Explore Chat Orchestrator</span>
                  <ArrowRight size={13} />
                </Button>
              </Link>
            </div>
          </CardSpotlight>

          <CardSpotlight className="h-full flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-10 h-10 rounded-lg bg-surface-2 border border-hairline flex items-center justify-center text-linear-primary">
                <Workflow className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-linear-primary font-semibold">
                  Engine 02
                </span>
                <h3 className="text-base sm:text-lg font-bold text-ink mt-0.5">
                  Visual DAG Workflow Studio
                </h3>
              </div>
              <p className="text-xs text-ink-subtle leading-relaxed">
                Build and monitor deterministic pipelines visually with React Flow nodes, AST condition branching, sandboxed Python code execution, and step-level unit test suites.
              </p>
              <ul className="space-y-2 text-xs text-ink-muted pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 size={13} className="text-linear-primary shrink-0" />
                  <span>5 Advanced block types: Agent, Condition, Python, Loop, Artifact</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 size={13} className="text-linear-primary shrink-0" />
                  <span>Natural-language AI Workflow Architect mode</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 size={13} className="text-linear-primary shrink-0" />
                  <span>Audited Supabase telemetry & public share slugs</span>
                </li>
              </ul>
            </div>
            <div className="pt-6">
              <Link href="/workflows">
                <Button variant="default" className="w-full text-xs gap-1.5">
                  <span>Launch Workflow Studio</span>
                  <ArrowRight size={13} />
                </Button>
              </Link>
            </div>
          </CardSpotlight>
        </div>
      </section>

      {/* Bento Grid Architecture Pillars */}
      <IntegrationsBento />

      {/* 4-Stage Execution Timeline */}
      <TimelineSection />

      {/* Specialized Agent Personas with 3D Glare Cards */}
      <WhoWeServe />

      {/* Production Metrics & Tech Stack */}
      <MetricsSection />

      {/* 3D Stacked Testimonials Carousel */}
      <TestimonialsSection />

      {/* Transparent Developer-First Pricing */}
      <PricingSection />

      {/* Final Call To Action with Background Beams */}
      <FinalCTA />

      {/* Multi-Column Comprehensive Footer */}
      <FooterSection />
    </div>
  );
}
