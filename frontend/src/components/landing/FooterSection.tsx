"use client";

import React from "react";
import Link from "next/link";
import { Bot, ExternalLink } from "lucide-react";
import { IconBrandGithub } from "@tabler/icons-react";

export default function FooterSection() {
  const sections = [
    {
      title: "Product",
      links: [
        { label: "Chat Interface", href: "/chat" },
        { label: "Workflow Studio", href: "/workflows" },
        { label: "Agents Studio", href: "/agents" },
        { label: "Pricing & Plans", href: "#pricing" },
      ],
    },
    {
      title: "Architecture",
      links: [
        { label: "Hierarchical Swarm", href: "#architecture" },
        { label: "DAG Execution Engine", href: "#workflows" },
        { label: "Sandboxed Python Tools", href: "#architecture" },
        { label: "Row-Level Security", href: "#architecture" },
      ],
    },
    {
      title: "Supported Models",
      links: [
        { label: "Google Gemini 3.8 Flash", href: "https://ai.google.dev" },
        { label: "Gemini 4 Argon", href: "https://ai.google.dev" },
        { label: "Perplexity Sonar", href: "https://perplexity.ai" },
        { label: "Claude 3.7 & GPT-4o", href: "#" },
      ],
    },
    {
      title: "Resources",
      links: [
        { label: "Documentation", href: "#" },
        { label: "API Reference", href: "http://localhost:8000/docs" },
        {
          label: "GitHub Repository",
          href: "https://github.com/PuneetShrivas/swarm-backend",
        },
        { label: "Changelog", href: "#" },
      ],
    },
  ];

  return (
    <footer className="w-full border-t border-hairline bg-surface-1/40 py-12 px-4 sm:px-6">
      <div className="max-w-5xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 pb-12 border-b border-hairline">
          {/* Brand Column */}
          <div className="col-span-2 space-y-3">
            <Link href="/" className="flex items-center gap-2 group w-fit">
              <div className="w-7 h-7 rounded-md bg-surface-2 border border-hairline flex items-center justify-center text-linear-primary group-hover:border-hairline-strong transition-colors">
                <Bot className="w-4 h-4" />
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-sm tracking-tight text-ink">
                  Swarm
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-xs bg-surface-2 text-ink-subtle border border-hairline">
                  v2.0
                </span>
              </div>
            </Link>
            <p className="text-xs text-ink-subtle max-w-xs leading-relaxed">
              Open-source autonomous multi-agent orchestration, visual DAG pipeline studio, and audited PostgreSQL session trees.
            </p>
            <div className="flex items-center gap-2 pt-1 text-xs text-semantic-success font-medium">
              <span className="w-2 h-2 rounded-full bg-semantic-success animate-pulse" />
              <span>All Swarm Agents Operational</span>
            </div>
          </div>

          {/* Nav Columns */}
          {sections.map((col, idx) => (
            <div key={idx} className="space-y-3">
              <h4 className="text-xs font-semibold text-ink uppercase tracking-wider font-mono">
                {col.title}
              </h4>
              <ul className="space-y-2 text-xs">
                {col.links.map((link, lIdx) => (
                  <li key={lIdx}>
                    {link.href.startsWith("http") ? (
                      <a
                        href={link.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-ink-subtle hover:text-ink transition-colors flex items-center gap-1"
                      >
                        <span>{link.label}</span>
                        <ExternalLink size={10} className="opacity-60" />
                      </a>
                    ) : (
                      <Link
                        href={link.href}
                        className="text-ink-subtle hover:text-ink transition-colors"
                      >
                        {link.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-ink-tertiary">
          <div>
            © {new Date().getFullYear()} Swarm Platform. Released under MIT License.
          </div>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/PuneetShrivas/swarm-backend"
              target="_blank"
              rel="noopener noreferrer"
              className="text-ink-subtle hover:text-ink transition-colors flex items-center gap-1.5"
            >
              <IconBrandGithub size={14} />
              <span>GitHub</span>
            </a>
            <span>•</span>
            <Link href="/login" className="text-ink-subtle hover:text-ink transition-colors">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
