"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Bot,
  Layers,
  Search,
  Code2,
  ShieldCheck,
  BarChart2,
  FileText,
  Zap,
  Sparkles,
  Server,
  Cpu,
  Thermometer,
  BookOpen,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Agent } from "../types";

interface AgentDetailsModalProps {
  agent: Agent | null;
  isOpen: boolean;
  onClose: () => void;
}

type TabType = "overview" | "tools" | "skills" | "mcp";

export default function AgentDetailsModal({
  agent,
  isOpen,
  onClose,
}: AgentDetailsModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>("overview");

  if (!isOpen || !agent) return null;

  const isOrch = agent.is_orchestrator || agent.id === "orchestrator";

  const getAgentIcon = (id: string) => {
    if (isOrch) return <Layers className="w-5 h-5 text-primary" />;
    switch (id) {
      case "researcher":
        return <Search className="w-5 h-5 text-blue-500" />;
      case "coder":
        return <Code2 className="w-5 h-5 text-emerald-500" />;
      case "reviewer":
        return <ShieldCheck className="w-5 h-5 text-amber-500" />;
      case "data_analyst":
        return <BarChart2 className="w-5 h-5 text-violet-500" />;
      case "synthesizer":
        return <FileText className="w-5 h-5 text-cyan-500" />;
      default:
        return <Bot className="w-5 h-5 text-primary" />;
    }
  };

  const tabs: { id: TabType; label: string; count?: number; icon: React.ReactNode }[] = [
    {
      id: "overview",
      label: "Overview & Prompt",
      icon: <BookOpen className="w-3.5 h-3.5" />,
    },
    {
      id: "tools",
      label: "Tools",
      count: agent.tools?.length || 0,
      icon: <Zap className="w-3.5 h-3.5" />,
    },
    {
      id: "skills",
      label: "Skills",
      count: agent.skills?.length || 0,
      icon: <Sparkles className="w-3.5 h-3.5" />,
    },
    {
      id: "mcp",
      label: "MCP Servers",
      count: agent.mcp_servers?.length || 0,
      icon: <Server className="w-3.5 h-3.5" />,
    },
  ];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 8 }}
          transition={{ duration: 0.16 }}
          className="bg-card rounded-2xl shadow-card border border-border/80 max-w-2xl w-full overflow-hidden flex flex-col max-h-[88vh] text-foreground"
        >
          {/* Header */}
          <div className="p-6 border-b border-border/60 bg-muted/20">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="w-11 h-11 rounded-2xl bg-primary/10 border border-primary/25 flex items-center justify-center shadow-subtle shrink-0">
                  {getAgentIcon(agent.id)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-foreground text-base tracking-tight">
                      {agent.name}
                    </h3>
                    {isOrch && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-primary/20 text-primary border border-primary/30 font-semibold">
                        Orchestrator
                      </span>
                    )}
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-500 border border-emerald-500/20">
                      Active
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                    {agent.role}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={onClose}
                className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition"
                aria-label="Close modal"
              >
                <X size={16} />
              </button>
            </div>

            {/* Quick Metadata Badges */}
            <div className="flex flex-wrap items-center gap-2 mt-4 text-[11px] font-mono">
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-background border border-border/60 text-muted-foreground">
                <Cpu size={12} className="text-primary" />
                <span>{agent.model || "gemini-2.5-flash"}</span>
              </span>
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-background border border-border/60 text-muted-foreground">
                <Thermometer size={12} className="text-amber-500" />
                <span>temp: {agent.temperature ?? 0.3}</span>
              </span>
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-background border border-border/60 text-muted-foreground">
                <Zap size={12} className="text-emerald-500" />
                <span>{agent.tools?.length || 0} tools</span>
              </span>
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-background border border-border/60 text-muted-foreground">
                <Server size={12} className="text-violet-500" />
                <span>{agent.mcp_servers?.length || 0} MCP servers</span>
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center px-6 border-b border-border/60 bg-muted/40 gap-2 overflow-x-auto">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-medium border-b-2 transition-all whitespace-nowrap ${
                    isActive
                      ? "border-primary text-foreground font-semibold"
                      : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                  }`}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                  {tab.count !== undefined && (
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                        isActive
                          ? "bg-primary/20 text-primary font-bold"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {tab.count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Tab Content Body */}
          <div className="p-6 overflow-y-auto space-y-4 flex-1">
            {/* Tab 1: Overview & System Prompt */}
            {activeTab === "overview" && (
              <div className="space-y-4">
                {agent.description && (
                  <div className="p-3.5 rounded-xl bg-muted/40 border border-border/60 text-xs text-foreground leading-relaxed">
                    <span className="font-semibold block mb-1 text-primary">Capabilities Overview</span>
                    {agent.description}
                  </div>
                )}

                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <BookOpen size={13} className="text-primary" />
                    System Persona & Operational Instructions
                  </h4>
                  <div className="p-4 rounded-xl bg-zinc-950 text-zinc-200 border border-zinc-800 font-mono text-xs overflow-x-auto max-h-72 leading-relaxed">
                    <ReactMarkdown>{agent.system_prompt || "No custom instructions specified."}</ReactMarkdown>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Registered Tools */}
            {activeTab === "tools" && (
              <div className="space-y-3">
                {agent.tools && agent.tools.length > 0 ? (
                  agent.tools.map((t, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-muted/30 border border-border/70 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-amber-500 font-mono text-xs">⚡</span>
                          <span className="font-semibold text-xs text-foreground font-mono">
                            {t.name}
                          </span>
                        </div>
                        {t.handler_name && (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border/40">
                            handler: {t.handler_name}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {t.description}
                      </p>
                      {t.parameters && (
                        <div className="mt-2 p-2.5 rounded-lg bg-zinc-950 text-zinc-300 font-mono text-[11px] overflow-x-auto border border-zinc-800">
                          <span className="text-zinc-500 block mb-1">parameters schema:</span>
                          <pre>{JSON.stringify(t.parameters, null, 2)}</pre>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-muted-foreground italic p-6 bg-muted/30 rounded-xl text-center">
                    No specialized tools declared for this agent.
                  </div>
                )}
              </div>
            )}

            {/* Tab 3: Skills */}
            {activeTab === "skills" && (
              <div className="space-y-3">
                {agent.skills && agent.skills.length > 0 ? (
                  agent.skills.map((s, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-muted/30 border border-border/70 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Sparkles size={14} className="text-primary" />
                          <span className="font-semibold text-xs text-foreground">
                            {s.name}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-muted-foreground">
                          id: {s.id}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {s.description}
                      </p>
                      {s.triggers && s.triggers.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 pt-1">
                          <span className="text-[10px] text-muted-foreground font-medium">Triggers:</span>
                          {s.triggers.map((trig, i) => (
                            <span
                              key={i}
                              className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20"
                            >
                              {trig}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-muted-foreground italic p-6 bg-muted/30 rounded-xl text-center">
                    No specialized skills registered for this agent.
                  </div>
                )}
              </div>
            )}

            {/* Tab 4: MCP Servers */}
            {activeTab === "mcp" && (
              <div className="space-y-3">
                {agent.mcp_servers && agent.mcp_servers.length > 0 ? (
                  agent.mcp_servers.map((mcp, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-muted/30 border border-border/70 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Server size={14} className="text-primary" />
                          <span className="font-semibold text-xs text-foreground font-mono">
                            {mcp.name}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border/40 font-bold">
                          {mcp.transport}
                        </span>
                      </div>
                      {mcp.command && (
                        <div className="text-[11px] font-mono text-muted-foreground">
                          <span className="text-muted-foreground/70">command: </span>
                          <span className="text-foreground">{mcp.command} {mcp.args?.join(" ")}</span>
                        </div>
                      )}
                      {mcp.url && (
                        <div className="text-[11px] font-mono text-muted-foreground">
                          <span className="text-muted-foreground/70">endpoint: </span>
                          <span className="text-foreground">{mcp.url}</span>
                        </div>
                      )}
                      {mcp.tools && mcp.tools.length > 0 && (
                        <div className="pt-1.5">
                          <span className="text-[10px] text-muted-foreground font-medium block mb-1.5">
                            Exposed MCP Tools:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {mcp.tools.map((tName, i) => (
                              <span
                                key={i}
                                className="text-[10px] font-mono px-2 py-0.5 rounded bg-card border border-border text-foreground"
                              >
                                🔌 {tName}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-muted-foreground italic p-6 bg-muted/30 rounded-xl text-center">
                    No MCP server connections defined for this agent.
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-3 bg-muted/30 border-t border-border/60 flex justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 bg-primary text-primary-foreground rounded-lg text-xs font-medium hover:opacity-90 transition shadow-subtle"
            >
              Close Profile
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
