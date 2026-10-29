"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  BookmarkPlus,
  Check,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { supabase } from "@/lib/supabase";
import { WorkflowSpec } from "./GranularStepTrace";

export interface SaveWorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflowSpec: WorkflowSpec | null;
  onSaved?: (savedWorkflow: Record<string, unknown>) => void;
}

export function SaveWorkflowModal({
  isOpen,
  onClose,
  workflowSpec,
  onSaved,
}: SaveWorkflowModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [goal, setGoal] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (workflowSpec) {
      setTitle(workflowSpec.title || "Custom Swarm Workflow");
      setDescription(workflowSpec.description || "Synthesized by Swarm Orchestrator.");
      setGoal(workflowSpec.goal || "");
      setSavedSuccess(false);
      setErrorMessage(null);
    }
  }, [workflowSpec]);

  if (!isOpen || !workflowSpec) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setErrorMessage("Please enter a workflow title.");
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const {
        data: { session },
      } = await supabase.auth.getSession();

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (session?.access_token) {
        headers["Authorization"] = `Bearer ${session.access_token}`;
      }

      const payload = {
        title: title.trim(),
        description: description.trim(),
        goal: goal.trim() || undefined,
        steps: workflowSpec.steps || [],
        edges: workflowSpec.edges || [],
        is_published: false,
      };

      const res = await fetch(`${apiUrl}/api/workflows`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to save workflow (status ${res.status})`);
      }

      const savedWf = await res.json();
      setSavedSuccess(true);
      if (onSaved) {
        onSaved(savedWf);
      }

      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err: unknown) {
      console.error("Save workflow error:", err);
      setErrorMessage((err as { message?: string })?.message || "Failed to save workflow.");
    } finally {
      setIsSaving(false);
    }
  };

  const stepsList = workflowSpec.steps || [];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.15 }}
          className="relative w-full max-w-lg rounded-xl border border-hairline bg-surface-1 shadow-2xl overflow-hidden font-sans"
        >
          {/* Header */}
          <div className="px-5 py-4 bg-surface-2/60 border-b border-hairline flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-linear-primary/10 border border-linear-primary/30 flex items-center justify-center text-linear-primary">
                <BookmarkPlus size={16} />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-ink">Save as Workflow</h3>
                <p className="text-[11px] text-ink-subtle">
                  Persist this synthesized execution pipeline to your workflows library.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-md hover:bg-surface-3 text-ink-subtle hover:text-ink transition-colors"
            >
              <X size={16} />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSave} className="p-5 space-y-4">
            {savedSuccess ? (
              <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center space-y-2">
                <Check size={24} className="mx-auto text-emerald-400" />
                <h4 className="text-sm font-semibold text-emerald-400">
                  Workflow Successfully Saved!
                </h4>
                <p className="text-xs text-ink-subtle">
                  You can now find, edit, and re-run it anytime in the Workflows Studio.
                </p>
              </div>
            ) : (
              <>
                {errorMessage && (
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-xs text-red-400">
                    <AlertCircle size={14} className="shrink-0" />
                    <span>{errorMessage}</span>
                  </div>
                )}

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-ink">Workflow Title</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g., Financial Research & Synthesis Pipeline"
                    className="w-full px-3 py-2 text-xs rounded-lg bg-surface-2 border border-hairline focus:border-linear-primary focus:outline-hidden text-ink placeholder:text-ink-muted transition-colors font-mono"
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-ink">Goal / Primary Objective</label>
                  <input
                    type="text"
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    placeholder="e.g., Gather market data and generate executive brief"
                    className="w-full px-3 py-2 text-xs rounded-lg bg-surface-2 border border-hairline focus:border-linear-primary focus:outline-hidden text-ink placeholder:text-ink-muted transition-colors font-mono"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-ink">Description</label>
                  <textarea
                    rows={2}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief description of the pipeline..."
                    className="w-full px-3 py-2 text-xs rounded-lg bg-surface-2 border border-hairline focus:border-linear-primary focus:outline-hidden text-ink placeholder:text-ink-muted transition-colors resize-none"
                  />
                </div>

                {/* Steps Preview */}
                <div className="space-y-1.5 pt-1">
                  <label className="text-xs font-medium text-ink flex items-center justify-between">
                    <span>Synthesized Steps ({stepsList.length})</span>
                    <span className="text-[10px] text-ink-subtle font-mono">DAG Execution Order</span>
                  </label>
                  <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1">
                    {stepsList.map((step, idx) => (
                      <div
                        key={step.id || idx}
                        className="p-2 rounded-md bg-surface-2/60 border border-hairline flex items-center justify-between text-xs font-mono"
                      >
                        <div className="flex items-center gap-2 truncate">
                          <span className="text-linear-primary text-[10px]">{idx + 1}.</span>
                          <span className="text-ink truncate">{step.name || step.id}</span>
                        </div>
                        {step.agent_id && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-surface-3 text-ink-subtle border border-hairline shrink-0">
                            @{step.agent_id}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Footer Buttons */}
                <div className="pt-3 border-t border-hairline flex items-center justify-end gap-2.5">
                  <button
                    type="button"
                    onClick={onClose}
                    disabled={isSaving}
                    className="px-3.5 py-2 text-xs rounded-lg hover:bg-surface-2 text-ink-subtle hover:text-ink transition-colors font-medium"
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    disabled={isSaving}
                    className="px-4 py-2 text-xs rounded-lg bg-linear-primary hover:bg-linear-hover text-white font-medium inline-flex items-center gap-1.5 transition-all shadow-xs cursor-pointer active:scale-95 disabled:opacity-50"
                  >
                    {isSaving ? (
                      <>
                        <Loader2 size={13} className="animate-spin" />
                        <span>Saving...</span>
                      </>
                    ) : (
                      <>
                        <BookmarkPlus size={13} />
                        <span>Save to Library</span>
                      </>
                    )}
                  </button>
                </div>
              </>
            )}
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
