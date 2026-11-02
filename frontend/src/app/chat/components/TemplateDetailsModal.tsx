"use client";

import React, { useState } from "react";
import { X, Copy, Check, FileText, Compass, BarChart3, Clock, Sparkles } from "lucide-react";
import { ArtifactTemplate } from "../types";

interface TemplateDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  template: ArtifactTemplate | null;
  onApplyTemplate?: (template: ArtifactTemplate) => void;
}

export default function TemplateDetailsModal({
  isOpen,
  onClose,
  template,
  onApplyTemplate,
}: TemplateDetailsModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !template) return null;

  const handleCopy = () => {
    if (!template.markdownInstructions) return;
    navigator.clipboard.writeText(template.markdownInstructions);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-2xl max-h-[85vh] flex flex-col bg-card border border-border/80 rounded-2xl shadow-card overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-5 py-4 border-b border-border/60 bg-muted/30 flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center text-primary shrink-0">
              <FileText size={18} />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-foreground truncate">
                  {template.title}
                </h3>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-primary/15 text-primary border border-primary/30">
                  {template.badge}
                </span>
                {template.isCustom && (
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-500 border border-amber-500/30">
                    Custom
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground truncate mt-0.5">
                {template.description}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors ml-2 shrink-0"
            title="Close (ESC)"
          >
            <X size={16} />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 no-scrollbar">
          {/* Metadata Parameters Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {template.tone && (
              <div className="p-3 rounded-xl bg-muted/40 border border-border/60">
                <div className="flex items-center gap-1.5 text-xs font-medium text-foreground mb-1">
                  <Compass size={13} className="text-primary" />
                  <span>Tone & Register</span>
                </div>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  {template.tone}
                </p>
              </div>
            )}

            {template.construction && (
              <div className="p-3 rounded-xl bg-muted/40 border border-border/60">
                <div className="flex items-center gap-1.5 text-xs font-medium text-foreground mb-1">
                  <Sparkles size={13} className="text-primary" />
                  <span>Construction Framework</span>
                </div>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  {template.construction}
                </p>
              </div>
            )}

            {template.dataHeaviness && (
              <div className="p-3 rounded-xl bg-muted/40 border border-border/60">
                <div className="flex items-center gap-1.5 text-xs font-medium text-foreground mb-1">
                  <BarChart3 size={13} className="text-primary" />
                  <span>Data Heaviness</span>
                </div>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  {template.dataHeaviness}
                </p>
              </div>
            )}

            {template.targetLength && (
              <div className="p-3 rounded-xl bg-muted/40 border border-border/60">
                <div className="flex items-center gap-1.5 text-xs font-medium text-foreground mb-1">
                  <Clock size={13} className="text-primary" />
                  <span>Target Length & Pacing</span>
                </div>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  {template.targetLength}
                </p>
              </div>
            )}
          </div>

          {/* Blueprint Sections */}
          {template.sections && template.sections.length > 0 && (
            <div className="p-3 rounded-xl bg-muted/20 border border-border/50">
              <span className="text-xs font-semibold text-foreground uppercase tracking-wider block mb-2 font-mono text-[10px]">
                Required Section Blueprint
              </span>
              <div className="flex flex-wrap gap-1.5">
                {template.sections.map((sec, idx) => (
                  <span
                    key={idx}
                    className="text-xs font-mono px-2 py-1 rounded-md bg-background border border-border text-foreground/90"
                  >
                    #{sec}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Markdown Instructions Specification */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground uppercase tracking-wider font-mono text-[10px]">
                Complete Template Instructions (.md)
              </span>
              <button
                type="button"
                onClick={handleCopy}
                className="flex items-center gap-1 px-2.5 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors font-mono text-[11px]"
              >
                {copied ? <Check size={12} className="text-emerald-500" /> : <Copy size={12} />}
                <span>{copied ? "Copied" : "Copy Markdown"}</span>
              </button>
            </div>
            <pre className="p-4 rounded-xl bg-background/80 border border-border text-[11px] font-mono text-muted-foreground leading-relaxed overflow-x-auto max-h-72 whitespace-pre-wrap selection:bg-primary/20">
              {template.markdownInstructions || "No additional markdown instructions specified."}
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-border/60 bg-muted/30 flex items-center justify-between">
          <span className="text-xs font-mono text-muted-foreground">
            Format: {template.defaultFormat.toUpperCase()} &middot; Grounded Swarm Synthesis
          </span>
          <div className="flex items-center gap-2">
            {onApplyTemplate && (
              <button
                type="button"
                onClick={() => {
                  onApplyTemplate(template);
                  onClose();
                }}
                className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:opacity-90 transition-opacity"
              >
                Use Template
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-muted text-foreground hover:bg-muted/80 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
