"use client";

import React, { useState, useEffect } from "react";
import {
  Layers,
  X,
  Play,
  Sparkles,
  Bot,
  Search,
  Loader2,
} from "lucide-react";

interface WorkflowSummary {
  id: string;
  title: string;
  goal: string;
  steps: Array<{ id: string; name: string; agent_id: string }>;
  visibility: string;
}

interface WorkflowPickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRunWorkflow: (workflowId: string, inputs: Record<string, unknown>) => void;
}

export default function WorkflowPickerModal({
  isOpen,
  onClose,
  onRunWorkflow,
}: WorkflowPickerModalProps) {
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowSummary | null>(null);
  const [queryInput, setQueryInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!isOpen) return;
    const fetchWorkflows = async () => {
      setIsLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      try {
        const res = await fetch(`${apiUrl}/api/workflows`);
        if (res.ok) {
          const data: WorkflowSummary[] = await res.json();
          setWorkflows(data);
          if (data.length > 0) setSelectedWorkflow(data[0]);
        }
      } catch (err) {
        console.error("Failed to load workflows for chat picker:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchWorkflows();
  }, [isOpen]);

  if (!isOpen) return null;

  const filtered = workflows.filter(
    (w) =>
      w.title.toLowerCase().includes(search.toLowerCase()) ||
      w.goal.toLowerCase().includes(search.toLowerCase())
  );

  const handleLaunch = () => {
    if (!selectedWorkflow) return;
    onRunWorkflow(selectedWorkflow.id, {
      query: queryInput || selectedWorkflow.goal,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-card border border-border rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary border border-primary/20 flex items-center justify-center">
              <Layers size={16} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground">Launch Autonomous Workflow</h3>
              <p className="text-[11px] text-muted-foreground">
                Select a workflow to execute and stream its step-by-step agent results into this chat.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-muted-foreground hover:text-foreground"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1 text-xs">
          {/* Search Box */}
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter workflows by goal or title..."
              className="w-full text-xs bg-background border border-border rounded-xl pl-9 pr-3 py-2 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {isLoading ? (
            <div className="py-12 flex justify-center">
              <Loader2 size={24} className="animate-spin text-primary" />
            </div>
          ) : workflows.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <p>No workflows created yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-56 overflow-y-auto">
              {filtered.map((wf) => {
                const isSelected = selectedWorkflow?.id === wf.id;
                return (
                  <div
                    key={wf.id}
                    onClick={() => setSelectedWorkflow(wf)}
                    className={`p-3 rounded-xl border cursor-pointer text-left transition ${
                      isSelected
                        ? "bg-primary/10 border-primary shadow-subtle"
                        : "bg-background border-border/70 hover:border-border"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-xs text-foreground truncate max-w-[170px]">
                        {wf.title}
                      </span>
                      <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                        <Bot size={10} /> {wf.steps?.length || 0} steps
                      </span>
                    </div>
                    <p className="text-[11px] text-muted-foreground line-clamp-2">
                      {wf.goal}
                    </p>
                  </div>
                );
              })}
            </div>
          )}

          {/* Selected Workflow Runtime Parameters */}
          {selectedWorkflow && (
            <div className="p-4 rounded-xl bg-background border border-border space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Sparkles size={13} className="text-primary" /> {selectedWorkflow.title}
                </span>
                <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded">
                  {selectedWorkflow.steps?.length || 0} steps in DAG
                </span>
              </div>

              <div>
                <label className="text-[11px] font-medium text-muted-foreground block mb-1">
                  Runtime Input Query (Optional Override)
                </label>
                <input
                  type="text"
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  placeholder={selectedWorkflow.goal}
                  className="w-full text-xs bg-card border border-border rounded-xl px-3 py-2 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border flex items-center justify-end gap-2 bg-card/60">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            Cancel
          </button>
          <button
            disabled={!selectedWorkflow}
            onClick={handleLaunch}
            className="px-4 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-xl hover:opacity-90 disabled:opacity-50 transition flex items-center gap-1.5 shadow-subtle"
          >
            <Play size={13} className="fill-current" /> Launch in Chat
          </button>
        </div>
      </div>
    </div>
  );
}
