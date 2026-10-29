"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import AppNavigationRail from "@/app/components/AppNavigationRail";
import AgentCard, { AgentCardData } from "./components/AgentCard";
import AgentEditorModal from "./components/AgentEditorModal";
import AgentPlaygroundModal from "./components/AgentPlaygroundModal";
import AIAgentGeneratorModal from "./components/AIAgentGeneratorModal";
import AgentDetailsModal from "@/app/chat/components/AgentDetailsModal";
import UsageModal from "@/app/chat/components/UsageModal";
import { UserUsageSummary, Agent as ChatAgent } from "@/app/chat/types";
import { supabase, getAuthHeaders } from "@/lib/supabase";
import {
  Plus,
  Sparkles,
  Search,
  X,
  Users,
  RefreshCw,
} from "lucide-react";

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentCardData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<"all" | "core" | "custom">("all");

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<AgentCardData | null>(null);
  const [testingAgent, setTestingAgent] = useState<AgentCardData | null>(null);
  const [isAIGeneratorModalOpen, setIsAIGeneratorModalOpen] = useState(false);
  const [inspectingAgent, setInspectingAgent] = useState<AgentCardData | null>(null);

  // User & Telemetry state
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [usage, setUsage] = useState<UserUsageSummary | null>(null);
  const [isUsageModalOpen, setIsUsageModalOpen] = useState(false);
  const [isLoadingUsage, setIsLoadingUsage] = useState(false);

  // Fetch all agents (Swarm Core + Custom)
  const fetchAllAgents = useCallback(async () => {
    setIsLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const authHeaders = await getAuthHeaders();

      // 1. Fetch built-in Swarm Core agents
      const coreRes = await fetch(`${apiUrl}/api/agents`);
      let coreAgents: AgentCardData[] = [];
      if (coreRes.ok) {
        const coreData = await coreRes.json();
        coreAgents = coreData.map((ag: AgentCardData) => ({
          ...ag,
          is_custom: false,
        }));
      }

      // 2. Fetch custom agents
      let customAgents: AgentCardData[] = [];
      try {
        const customRes = await fetch(`${apiUrl}/api/custom-agents`, {
          headers: authHeaders,
        });
        if (customRes.ok) {
          const customData = await customRes.json();
          customAgents = customData.map((ag: AgentCardData) => ({
            ...ag,
            is_custom: true,
          }));
        }
      } catch (err) {
        console.warn("Could not fetch custom agents:", err);
      }

      // Merge and deduplicate by ID
      const map = new Map<string, AgentCardData>();
      coreAgents.forEach((a) => map.set(a.id.toLowerCase(), a));
      customAgents.forEach((a) => map.set(a.id.toLowerCase(), a));

      setAgents(Array.from(map.values()));
    } catch (err) {
      console.error("Failed to fetch agents roster", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch telemetry usage
  const fetchUsage = useCallback(async (token?: string) => {
    setIsLoadingUsage(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = token ? { Authorization: `Bearer ${token}` } : await getAuthHeaders();
      const res = await fetch(`${apiUrl}/api/usage`, { headers });
      if (res.ok) {
        const data: UserUsageSummary = await res.json();
        setUsage(data);
      }
    } catch (err) {
      console.error("Failed to load usage stats", err);
    } finally {
      setIsLoadingUsage(false);
    }
  }, []);

  // Auth setup
  useEffect(() => {
    const initAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        setUserEmail(session.user.email || null);
        fetchUsage(session.access_token);
      }
    };
    initAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUserEmail(session?.user.email || null);
      if (session) {
        fetchUsage(session.access_token);
      } else {
        setUsage(null);
      }
    });

    fetchAllAgents();

    return () => subscription.unsubscribe();
  }, [fetchAllAgents, fetchUsage]);

  // Handle agent delete
  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm(`Are you sure you want to delete custom agent '${agentId}'?`)) {
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const authHeaders = await getAuthHeaders();

      const res = await fetch(`${apiUrl}/api/custom-agents/${encodeURIComponent(agentId)}`, {
        method: "DELETE",
        headers: authHeaders,
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to delete custom agent.");
      }

      setAgents((prev) => prev.filter((a) => a.id !== agentId));
    } catch (err: unknown) {
      alert((err as Error).message || "Could not delete agent.");
    }
  };

  // Handle agent saved (from Create, Edit, or AI Generator)
  const handleAgentSaved = (savedAgent: AgentCardData) => {
    setAgents((prev) => {
      const exists = prev.some((a) => a.id.toLowerCase() === savedAgent.id.toLowerCase());
      if (exists) {
        return prev.map((a) =>
          a.id.toLowerCase() === savedAgent.id.toLowerCase() ? { ...savedAgent, is_custom: true } : a
        );
      }
      return [{ ...savedAgent, is_custom: true }, ...prev];
    });
  };

  // Filtered and searched agents
  const filteredAgents = useMemo(() => {
    return agents.filter((ag) => {
      // Category filter
      if (categoryFilter === "core" && ag.is_custom) return false;
      if (categoryFilter === "custom" && !ag.is_custom) return false;

      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = ag.name.toLowerCase().includes(q);
        const matchesRole = (ag.role || "").toLowerCase().includes(q);
        const matchesDesc = (ag.description || "").toLowerCase().includes(q);
        const matchesId = ag.id.toLowerCase().includes(q);
        return matchesName || matchesRole || matchesDesc || matchesId;
      }

      return true;
    });
  }, [agents, categoryFilter, searchQuery]);

  const coreCount = agents.filter((a) => !a.is_custom).length;
  const customCount = agents.filter((a) => a.is_custom).length;

  return (
    <div className="min-h-screen bg-canvas text-ink font-sans flex flex-col selection:bg-linear-primary/20">
      {/* 1. App Top Navigation Rail */}
      <AppNavigationRail
        currentTab="agents"
        totalTokensUsed={usage?.total_tokens ?? 0}
        onOpenUsage={() => setIsUsageModalOpen(true)}
        userEmail={userEmail}
        onSignOut={async () => {
          await supabase.auth.signOut();
          setUserEmail(null);
          setUsage(null);
        }}
      />

      {/* 2. Main Studio Body */}
      <main className="flex-1 p-4 md:p-6 max-w-6xl w-full mx-auto space-y-6">
        {/* Header Banner */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-hairline">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-ink">
                Autonomous Agent Roster & Studio
              </h1>
              <span className="text-xs font-mono px-2 py-0.5 rounded-pill bg-surface-2 border border-hairline text-ink-subtle">
                {agents.length} Online
              </span>
            </div>
            <p className="text-xs text-ink-subtle mt-1 leading-relaxed">
              Explore specialized swarm agents, create custom personas, and test them with live inputs in the interactive playground.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => setIsAIGeneratorModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-ink hover:text-white bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong rounded-md transition-colors shadow-card"
              title="Generate a custom agent using natural language with Gemini"
            >
              <Sparkles size={13} className="text-linear-primary" />
              <span>AI Agent Generator</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setEditingAgent(null);
                setIsCreateModalOpen(true);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors shadow-card"
              title="Create a new specialized custom agent"
            >
              <Plus size={13} />
              <span>New Agent</span>
            </button>
          </div>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-2 rounded-lg bg-surface-1 border border-hairline">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search
              size={13}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-tertiary pointer-events-none"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search agents by name, role, or description..."
              className="w-full text-xs bg-canvas border border-hairline hover:border-hairline-strong focus:border-linear-focus rounded-md pl-8 pr-8 py-1.5 text-ink focus:outline-none transition-colors"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-subtle hover:text-ink"
              >
                <X size={12} />
              </button>
            )}
          </div>

          {/* Segmented Filter Pills */}
          <div className="flex items-center gap-1 bg-canvas p-0.5 rounded-md border border-hairline shrink-0">
            <button
              type="button"
              onClick={() => setCategoryFilter("all")}
              className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                categoryFilter === "all"
                  ? "bg-surface-2 text-ink font-semibold"
                  : "text-ink-subtle hover:text-ink"
              }`}
            >
              All ({agents.length})
            </button>
            <button
              type="button"
              onClick={() => setCategoryFilter("core")}
              className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                categoryFilter === "core"
                  ? "bg-surface-2 text-ink font-semibold"
                  : "text-ink-subtle hover:text-ink"
              }`}
            >
              Swarm Core ({coreCount})
            </button>
            <button
              type="button"
              onClick={() => setCategoryFilter("custom")}
              className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                categoryFilter === "custom"
                  ? "bg-surface-2 text-ink font-semibold"
                  : "text-ink-subtle hover:text-ink"
              }`}
            >
              Custom ({customCount})
            </button>
          </div>

          {/* Refresh Button */}
          <button
            type="button"
            onClick={fetchAllAgents}
            disabled={isLoading}
            className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors border border-hairline shrink-0"
            title="Refresh agents roster"
          >
            <RefreshCw size={13} className={isLoading ? "animate-spin" : ""} />
          </button>
        </div>

        {/* Agents Grid */}
        {isLoading && agents.length === 0 ? (
          <div className="p-12 text-center text-ink-subtle font-mono text-xs space-y-2">
            <div className="w-5 h-5 rounded-full border-2 border-linear-primary border-t-transparent animate-spin mx-auto" />
            <p>Loading agent roster...</p>
          </div>
        ) : filteredAgents.length === 0 ? (
          <div className="p-12 text-center rounded-lg border border-dashed border-hairline bg-surface-1/40 space-y-3">
            <Users size={28} className="mx-auto text-ink-tertiary" />
            <h3 className="text-sm font-semibold text-ink">No agents found</h3>
            <p className="text-xs text-ink-subtle max-w-sm mx-auto">
              {searchQuery
                ? `No agents match your search '${searchQuery}'. Try a different term or clear the filter.`
                : "No custom agents in your library yet. Create your first agent or synthesize one with AI."}
            </p>
            <div className="pt-2 flex items-center justify-center gap-2">
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="px-3 py-1.5 text-xs text-ink bg-surface-2 rounded-md border border-hairline hover:bg-surface-3 transition-colors"
                >
                  Clear Search
                </button>
              )}
              <button
                type="button"
                onClick={() => {
                  setEditingAgent(null);
                  setIsCreateModalOpen(true);
                }}
                className="px-3 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors"
              >
                + Create Agent
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAgents.map((ag) => (
              <AgentCard
                key={ag.id}
                agent={ag}
                onTest={(a) => setTestingAgent(a)}
                onEdit={(a) => setEditingAgent(a)}
                onDelete={handleDeleteAgent}
                onInspect={(a) => setInspectingAgent(a)}
              />
            ))}
          </div>
        )}
      </main>

      {/* 3. Modals */}

      {/* Create / Edit Custom Agent Modal */}
      <AgentEditorModal
        isOpen={isCreateModalOpen || editingAgent !== null}
        agent={editingAgent}
        onClose={() => {
          setIsCreateModalOpen(false);
          setEditingAgent(null);
        }}
        onSaved={handleAgentSaved}
      />

      {/* Interactive Testing Playground Modal */}
      <AgentPlaygroundModal
        isOpen={testingAgent !== null}
        agent={testingAgent}
        onClose={() => setTestingAgent(null)}
      />

      {/* Generative AI Agent Architect Modal */}
      <AIAgentGeneratorModal
        isOpen={isAIGeneratorModalOpen}
        onClose={() => setIsAIGeneratorModalOpen(false)}
        onSaved={handleAgentSaved}
        onTestAgent={(generated) => {
          setIsAIGeneratorModalOpen(false);
          setTestingAgent(generated);
        }}
      />

      {/* Deep Inspection Details Modal */}
      {inspectingAgent && (
        <AgentDetailsModal
          isOpen={inspectingAgent !== null}
          agent={inspectingAgent as unknown as ChatAgent}
          onClose={() => setInspectingAgent(null)}
        />
      )}

      {/* Telemetry Usage Modal */}
      <UsageModal
        isOpen={isUsageModalOpen}
        onClose={() => setIsUsageModalOpen(false)}
        usage={usage}
        isLoading={isLoadingUsage}
        onRefresh={() => fetchUsage()}
      />
    </div>
  );
}
