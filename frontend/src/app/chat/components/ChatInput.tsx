"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import {
  Send,
  Square,
  Layers,
  Bot,
  RotateCcw,
  Sparkles,
  Paperclip,
  Upload,
  FolderArchive,
  X,
  FileText,
  FileSpreadsheet,
  Presentation,
  FileCode,
  FileJson,
  Search,
  Check,
} from "lucide-react";
import { ArtifactTemplate } from "../types";

interface SlashCommand {
  id: string;
  command: string;
  label: string;
  description: string;
  icon: typeof Layers;
}

export interface AttachedArtifact {
  id: string;
  name: string;
  filename: string;
  type: string;
  content: string;
  size_bytes?: number;
  is_base64?: boolean;
}

interface ChatInputProps {
  onSend: (content: string, attachedArtifacts?: AttachedArtifact[], selectedTemplate?: ArtifactTemplate) => void;
  isLoading: boolean;
  onStop?: () => void;
  placeholder?: string;
  onOpenWorkflowPicker?: () => void;
  onClearChat?: () => void;
  onOpenArtifactSelector?: () => void;
  attachedArtifacts?: AttachedArtifact[];
  onRemoveArtifact?: (id: string) => void;
  onUploadFile?: (file: File) => Promise<void>;
}

export const ARTIFACT_TEMPLATES: ArtifactTemplate[] = [
  {
    id: "executive-summary",
    title: "Executive Summary Report",
    badge: "EXECUTIVE",
    description: "High-level overview, key findings, strategic takeaways, and recommended action matrix",
    sections: ["Executive Overview", "Key Findings & Data Points", "Strategic Risk Matrix", "Recommended Action Plan"],
    defaultFormat: "pdf",
  },
  {
    id: "research-report",
    title: "Research & Deep-Dive Synthesis",
    badge: "RESEARCH",
    description: "In-depth analysis, methodology, comparative findings, citations, and comprehensive conclusion",
    sections: ["Abstract & Problem Context", "Methodology & Scope", "Detailed Findings & Analysis", "Comparative Evidence", "Strategic Conclusion"],
    defaultFormat: "pdf",
  },
  {
    id: "tech-spec",
    title: "Technical Specification & Architecture Audit",
    badge: "TECHNICAL",
    description: "System architecture breakdown, data schemas, security posture, and engineering roadmap",
    sections: ["System Overview & Objectives", "Architectural Breakdown", "Security & Compliance Analysis", "Implementation Phasing & Milestones"],
    defaultFormat: "pdf",
  },
  {
    id: "financial-data",
    title: "Financial & Quantitative Data Analysis",
    badge: "FINANCIAL",
    description: "Quantitative metrics, KPI performance, tabular comparisons, and forward projections",
    sections: ["Financial & Operational Highlights", "Quantitative KPI Breakdown", "Tabular Performance Comparison", "Forward Projections & Forecast"],
    defaultFormat: "pdf",
  },
  {
    id: "compliance-review",
    title: "Compliance & Policy Review",
    badge: "AUDIT",
    description: "Regulatory evaluation, policy gap analysis, audit checklist, and remediation timeline",
    sections: ["Scope & Regulatory Baseline", "Audit Checklist & Adherence", "Identified Gaps & Discrepancies", "Remediation & Governance Roadmap"],
    defaultFormat: "pdf",
  },
  {
    id: "meeting-minutes",
    title: "Actionable Meeting & Transcript Minutes",
    badge: "MINUTES",
    description: "Executive discussion points, key decisions adopted, and action item matrix with owners/deadlines",
    sections: ["Agenda & Meeting Context", "Executive Discussion Points", "Key Decisions Adopted", "Action Items Matrix (Owner & Deadline)"],
    defaultFormat: "pdf",
  },
];

const SLASH_COMMANDS: SlashCommand[] = [
  {
    id: "artifact",
    command: "/artifact",
    label: "Artifact Report Template",
    description: "Select an executive report template to synthesize attached PDF / document",
    icon: FileText,
  },
  {
    id: "workflows",
    command: "/workflows",
    label: "Autonomous Workflows",
    description: "Browse, launch, and execute multi-agent pipelines",
    icon: Layers,
  },
  {
    id: "agents",
    command: "/agents",
    label: "Swarm Specialist Agents",
    description: "Inspect tools, skills, and prompts of active agents",
    icon: Bot,
  },
  {
    id: "clear",
    command: "/clear",
    label: "Clear Conversation",
    description: "Reset active branch and start fresh conversation",
    icon: RotateCcw,
  },
];

export default function ChatInput({
  onSend,
  isLoading,
  onStop,
  placeholder = "Message the swarm or type /workflow...",
  onOpenWorkflowPicker,
  onClearChat,
  onOpenArtifactSelector,
  attachedArtifacts = [],
  onRemoveArtifact,
  onUploadFile,
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [isDismissed, setIsDismissed] = useState(false);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [showArtifactTemplatePopup, setShowArtifactTemplatePopup] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<ArtifactTemplate | null>(null);
  const [templateSearch, setTemplateSearch] = useState("");
  const [selectedTemplateIdx, setSelectedTemplateIdx] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 180)}px`;
    }
  }, [input]);

  // Close attachment menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest("#attach-menu-container")) {
        setShowAttachMenu(false);
      }
    };
    if (showAttachMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showAttachMenu]);

  // Close artifact template menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest("#artifact-template-container")) {
        setShowArtifactTemplatePopup(false);
      }
    };
    if (showArtifactTemplatePopup) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showArtifactTemplatePopup]);

  // Filter artifact templates
  const filteredTemplates = useMemo(() => {
    if (!templateSearch.trim()) return ARTIFACT_TEMPLATES;
    const q = templateSearch.toLowerCase().trim();
    return ARTIFACT_TEMPLATES.filter(
      (t) =>
        t.title.toLowerCase().includes(q) ||
        t.badge.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        t.sections.some((s) => s.toLowerCase().includes(q))
    );
  }, [templateSearch]);

  // Handle template selection
  const handleSelectTemplate = (template: ArtifactTemplate) => {
    setSelectedTemplate(template);
    setShowArtifactTemplatePopup(false);
    setTemplateSearch("");

    const trimmed = input.trim();
    if (!trimmed || trimmed === "/artifact" || trimmed === "/template") {
      setInput(`prepare a report according to /artifact [${template.title}]`);
    } else if (trimmed.includes("/artifact") || trimmed.includes("/template")) {
      setInput(
        trimmed
          .replace(/\/artifact(?:\[[^\]]*\])?/gi, `/artifact [${template.title}]`)
          .replace(/\/template(?:\[[^\]]*\])?/gi, `/artifact [${template.title}]`)
      );
    } else {
      setInput(`${trimmed} prepare a report according to /artifact [${template.title}]`);
    }

    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  // Determine active slash command suggestions
  const isSlashActive = input.startsWith("/") && !isDismissed && !showArtifactTemplatePopup;
  const slashQuery = input.startsWith("/") ? input.slice(1).toLowerCase().trim() : "";
  const matchingCommands = SLASH_COMMANDS.filter(
    (c) =>
      c.command.toLowerCase().includes(slashQuery) ||
      c.id.toLowerCase().includes(slashQuery) ||
      c.label.toLowerCase().includes(slashQuery)
  );

  const executeCommand = (cmd: SlashCommand) => {
    setIsDismissed(true);
    if (cmd.id === "artifact" || cmd.command === "/artifact") {
      setShowArtifactTemplatePopup(true);
      return;
    }
    setInput("");
    if (cmd.id === "workflows" || cmd.command === "/workflows" || cmd.command === "/workflow") {
      if (onOpenWorkflowPicker) onOpenWorkflowPicker();
    } else if (cmd.id === "clear") {
      if (onClearChat) onClearChat();
    } else if (cmd.id === "agents") {
      onSend("Show me the active swarm agents and their capabilities.", attachedArtifacts);
    }
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const trimmed = input.trim();
    const lower = trimmed.toLowerCase();

    // Direct slash command intercept
    if (lower === "/workflow" || lower === "/workflows" || lower.startsWith("/workflow ")) {
      setInput("");
      if (onOpenWorkflowPicker) onOpenWorkflowPicker();
      return;
    }

    if (lower === "/clear") {
      setInput("");
      if (onClearChat) onClearChat();
      return;
    }

    if (lower === "/artifact" || lower === "/template") {
      setShowArtifactTemplatePopup(true);
      return;
    }

    onSend(trimmed, attachedArtifacts, selectedTemplate || undefined);
    setInput("");
    setSelectedTemplate(null);
    setIsDismissed(false);
    setShowArtifactTemplatePopup(false);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Keyboard navigation in Artifact Templates popup
    if (showArtifactTemplatePopup && filteredTemplates.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedTemplateIdx((prev) => (prev + 1) % filteredTemplates.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedTemplateIdx((prev) => (prev - 1 + filteredTemplates.length) % filteredTemplates.length);
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        const selected = filteredTemplates[selectedTemplateIdx] || filteredTemplates[0];
        if (selected) {
          handleSelectTemplate(selected);
          return;
        }
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setShowArtifactTemplatePopup(false);
        return;
      }
    }

    // Standard Slash Command keyboard navigation
    if (isSlashActive && matchingCommands.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIdx((prev) => (prev + 1) % matchingCommands.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIdx((prev) => (prev - 1 + matchingCommands.length) % matchingCommands.length);
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        const selected = matchingCommands[selectedIdx] || matchingCommands[0];
        if (selected) {
          executeCommand(selected);
          return;
        }
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setIsDismissed(true);
        return;
      }
    }

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setInput(val);
    setSelectedIdx(0);
    if (isDismissed && val.startsWith("/")) {
      setIsDismissed(false);
    }
    const lower = val.toLowerCase().trim();
    if (lower === "/artifact" || lower === "/template" || lower.startsWith("/artifact ") || lower.startsWith("/template ")) {
      setShowArtifactTemplatePopup(true);
    }
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0] && onUploadFile) {
      await onUploadFile(e.target.files[0]);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0] && onUploadFile) {
      await onUploadFile(e.dataTransfer.files[0]);
    }
  };

  const getFileIcon = (type: string) => {
    const t = (type || "").toLowerCase();
    if (t === "pdf") return <FileText size={12} className="text-red-400" />;
    if (t === "pptx" || t === "ppt") return <Presentation size={12} className="text-orange-400" />;
    if (t === "xlsx" || t === "xls" || t === "csv") return <FileSpreadsheet size={12} className="text-emerald-400" />;
    if (t === "docx" || t === "doc") return <FileText size={12} className="text-blue-400" />;
    if (t === "json") return <FileJson size={12} className="text-amber-400" />;
    if (["py", "js", "ts", "html", "css"].includes(t)) return <FileCode size={12} className="text-primary" />;
    return <FileText size={12} className="text-muted-foreground" />;
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`p-3 md:p-5 bg-card/75 backdrop-blur-xl border-t border-border/70 sticky bottom-0 z-10 transition-colors duration-200 ${
        isDragging ? "ring-2 ring-primary/80 bg-primary/5" : ""
      }`}
    >
      <div className="max-w-4xl mx-auto relative">
        {/* Hidden file input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInputChange}
          accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.csv,.json,.py,.md,.txt,.html"
          className="hidden"
        />

        {/* Attached Artifacts & Selected Template Chips Bar */}
        {(attachedArtifacts.length > 0 || selectedTemplate) && (
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-2.5 animate-fade-in">
            {attachedArtifacts.length > 0 && (
              <span className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider shrink-0 flex items-center gap-1">
                <Paperclip size={11} className="text-primary" /> Context:
              </span>
            )}
            {attachedArtifacts.map((art) => {
              const fname = art.filename || art.name || "artifact";
              const ext = (art.type || fname.split(".").pop() || "txt").toLowerCase();
              return (
                <div
                  key={art.id}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-muted/80 border border-border/80 text-foreground text-xs font-medium animate-fade-in shrink-0 shadow-xs group"
                >
                  {getFileIcon(ext)}
                  <span className="max-w-[150px] truncate text-xs">{fname}</span>
                  <span className="text-[9px] font-mono uppercase text-muted-foreground px-1 py-0.2 rounded bg-background/80">
                    {ext}
                  </span>
                  {onRemoveArtifact && (
                    <button
                      type="button"
                      onClick={() => onRemoveArtifact(art.id)}
                      className="p-0.5 text-muted-foreground hover:text-destructive rounded transition-colors"
                      title="Detach context artifact"
                    >
                      <X size={12} />
                    </button>
                  )}
                </div>
              );
            })}

            {/* Selected Artifact Template Chip */}
            {selectedTemplate && (
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-linear-primary/15 border border-linear-primary/40 text-ink text-xs font-medium animate-fade-in shrink-0 shadow-xs group">
                <FileText size={12} className="text-linear-primary" />
                <span className="text-xs text-ink">{selectedTemplate.title}</span>
                <span className="text-[9px] font-mono uppercase px-1 py-0.2 rounded bg-surface-2 text-linear-primary border border-hairline">
                  {selectedTemplate.badge}
                </span>
                <button
                  type="button"
                  onClick={() => setSelectedTemplate(null)}
                  className="p-0.5 text-ink-subtle hover:text-ink rounded transition-colors ml-0.5"
                  title="Remove template"
                >
                  <X size={12} />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Slash Command Palette Popover */}
        {isSlashActive && matchingCommands.length > 0 && (
          <div className="absolute bottom-full mb-2 left-0 right-0 sm:right-auto sm:min-w-[340px] bg-card border border-border/80 rounded-xl shadow-card overflow-hidden z-20 animate-fade-in backdrop-blur-xl">
            <div className="px-3 py-1.5 border-b border-border/60 bg-muted/30 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Sparkles size={11} className="text-primary" /> Slash Commands
              </span>
              <span>Use ↑ ↓ Enter</span>
            </div>
            <div className="p-1 space-y-0.5">
              {matchingCommands.map((cmd, idx) => {
                const Icon = cmd.icon;
                const isSelected = idx === selectedIdx;
                return (
                  <button
                    key={cmd.id}
                    type="button"
                    onClick={() => executeCommand(cmd)}
                    onMouseEnter={() => setSelectedIdx(idx)}
                    className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition text-xs ${
                      isSelected
                        ? "bg-primary text-primary-foreground font-medium"
                        : "text-foreground hover:bg-muted/60"
                    }`}
                  >
                    <div
                      className={`w-6 h-6 rounded-md flex items-center justify-center shrink-0 border ${
                        isSelected
                          ? "bg-primary-foreground/15 border-primary-foreground/30 text-primary-foreground"
                          : "bg-muted/50 border-border/60 text-primary"
                      }`}
                    >
                      <Icon size={13} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold truncate">{cmd.label}</span>
                        <code
                          className={`text-[10px] font-mono px-1 py-0.5 rounded ${
                            isSelected
                              ? "bg-primary-foreground/20 text-primary-foreground"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {cmd.command}
                        </code>
                      </div>
                      <p
                        className={`text-[11px] truncate ${
                          isSelected ? "text-primary-foreground/80" : "text-muted-foreground"
                        }`}
                      >
                        {cmd.description}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Attachment Menu Popover */}
        {showAttachMenu && (
          <div
            id="attach-menu-container"
            className="absolute bottom-full mb-2 left-2 bg-card border border-border/80 rounded-xl shadow-card overflow-hidden z-30 animate-fade-in p-1 min-w-[220px] backdrop-blur-xl"
          >
            <div className="px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground border-b border-border/50 mb-1">
              Add Context Document
            </div>
            <button
              type="button"
              onClick={() => {
                setShowAttachMenu(false);
                fileInputRef.current?.click();
              }}
              className="w-full flex items-center gap-2.5 px-2.5 py-2 text-xs text-foreground hover:bg-muted/70 rounded-lg text-left transition"
            >
              <Upload size={14} className="text-primary shrink-0" />
              <div>
                <p className="font-medium">Upload File from Device</p>
                <p className="text-[10px] text-muted-foreground">PDF, Word, Excel, PPT, Code, Text</p>
              </div>
            </button>
            {onOpenArtifactSelector && (
              <button
                type="button"
                onClick={() => {
                  setShowAttachMenu(false);
                  onOpenArtifactSelector();
                }}
                className="w-full flex items-center gap-2.5 px-2.5 py-2 text-xs text-foreground hover:bg-muted/70 rounded-lg text-left transition"
              >
                <FolderArchive size={14} className="text-primary shrink-0" />
                <div>
                  <p className="font-medium">Attach from Artifacts Studio</p>
                  <p className="text-[10px] text-muted-foreground">Select previously synthesized files</p>
                </div>
              </button>
            )}

            <button
              type="button"
              onClick={() => {
                setShowAttachMenu(false);
                setShowArtifactTemplatePopup(true);
              }}
              className="w-full flex items-center gap-2.5 px-2.5 py-2 text-xs text-foreground hover:bg-muted/70 rounded-lg text-left transition border-t border-border/50 mt-0.5"
            >
              <FileText size={14} className="text-primary shrink-0" />
              <div>
                <p className="font-medium">Report Template (/artifact)</p>
                <p className="text-[10px] text-muted-foreground">Executive Summary, Tech Spec, Audit, etc.</p>
              </div>
            </button>
          </div>
        )}

        {/* Attached Artifact Template Picker Popover */}
        {showArtifactTemplatePopup && (
          <div
            id="artifact-template-container"
            className="absolute bottom-full mb-2 left-0 right-0 sm:right-auto sm:min-w-[420px] max-w-xl bg-card border border-border/80 rounded-xl shadow-card overflow-hidden z-30 animate-fade-in backdrop-blur-xl"
          >
            {/* Header */}
            <div className="px-3.5 py-2.5 border-b border-border/60 bg-muted/40 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-md bg-primary/10 border border-primary/30 flex items-center justify-center text-primary">
                  <FileText size={12} />
                </div>
                <div>
                  <span className="text-xs font-semibold text-foreground tracking-tight block">
                    Artifact Report Templates
                  </span>
                  <span className="text-[10px] font-mono text-muted-foreground">
                    Command /artifact &middot; Select schema to synthesize document
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowArtifactTemplatePopup(false)}
                className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                title="Close template picker (ESC)"
              >
                <X size={13} />
              </button>
            </div>

            {/* Search Filter */}
            <div className="p-2 border-b border-border/50 bg-card">
              <div className="relative">
                <Search size={13} className="absolute left-2.5 top-2.5 text-muted-foreground" />
                <input
                  type="text"
                  value={templateSearch}
                  onChange={(e) => {
                    setTemplateSearch(e.target.value);
                    setSelectedTemplateIdx(0);
                  }}
                  placeholder="Filter templates (e.g. Executive, Research, Technical)..."
                  className="w-full pl-8 pr-3 py-1.5 text-xs bg-muted/50 border border-border/60 rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary font-sans"
                  autoFocus
                />
              </div>
            </div>

            {/* Templates List */}
            <div className="max-h-72 overflow-y-auto p-1.5 space-y-1 no-scrollbar">
              {filteredTemplates.length === 0 ? (
                <div className="p-4 text-center text-xs text-muted-foreground font-mono">
                  No matching artifact templates found.
                </div>
              ) : (
                filteredTemplates.map((template, idx) => {
                  const isSelected = idx === selectedTemplateIdx;
                  return (
                    <div
                      key={template.id}
                      onClick={() => handleSelectTemplate(template)}
                      onMouseEnter={() => setSelectedTemplateIdx(idx)}
                      className={`p-2.5 rounded-lg border transition-all cursor-pointer text-left ${
                        isSelected
                          ? "bg-primary/10 border-primary/60 shadow-xs"
                          : "bg-card border-border/60 hover:border-border hover:bg-muted/50"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-1 mb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-foreground">
                            {template.title}
                          </span>
                          {selectedTemplate?.id === template.id && (
                            <Check size={12} className="text-primary shrink-0" />
                          )}
                        </div>
                        <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded-xs bg-primary/15 text-primary border border-primary/30">
                          {template.badge}
                        </span>
                      </div>
                      <p className="text-[11px] text-muted-foreground leading-snug mb-1.5">
                        {template.description}
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {template.sections.map((sec, sIdx) => (
                          <span
                            key={sIdx}
                            className="text-[9px] font-mono text-muted-foreground px-1 py-0.2 rounded-xs bg-background/80 border border-border/60"
                          >
                            #{sec}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer with Option to Attach Existing Workspace Artifact */}
            {onOpenArtifactSelector && (
              <div className="p-2 border-t border-border/50 bg-muted/30 flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground font-mono">
                  Want to ground from past outputs?
                </span>
                <button
                  type="button"
                  onClick={() => {
                    setShowArtifactTemplatePopup(false);
                    onOpenArtifactSelector();
                  }}
                  className="text-primary hover:underline font-medium flex items-center gap-1 transition-colors"
                >
                  <FolderArchive size={12} />
                  <span>Attach from Artifacts Studio</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* Textarea Form */}
        <form onSubmit={handleSubmit} className="relative flex items-end">
          {/* Left Attachment Trigger */}
          <div id="attach-menu-container" className="absolute left-2.5 bottom-2.5 flex items-center gap-1 z-10">
            <button
              type="button"
              onClick={() => setShowAttachMenu((prev) => !prev)}
              className="p-2 text-muted-foreground hover:text-primary hover:bg-muted/70 rounded-xl transition"
              title="Attach files or artifacts for context"
              aria-label="Attach context file"
            >
              <Paperclip size={16} />
            </button>
          </div>

          <textarea
            ref={textareaRef}
            rows={1}
            className="w-full pl-12 pr-14 py-3.5 bg-muted/40 border border-border/80 focus:border-primary/60 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm sm:text-[15px] text-foreground placeholder:text-muted-foreground resize-none shadow-subtle leading-relaxed overflow-y-auto no-scrollbar [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden"
            style={{
              scrollbarWidth: "none",
              msOverflowStyle: "none",
            }}
            placeholder={placeholder}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />

          {/* Right Action Buttons */}
          <div className="absolute right-2.5 bottom-2.5 flex items-center gap-1.5">
            {onOpenWorkflowPicker && (
              <button
                type="button"
                onClick={onOpenWorkflowPicker}
                className="p-2 text-muted-foreground hover:text-primary hover:bg-muted/70 rounded-xl transition"
                title="Run Autonomous Workflow (/workflows)"
              >
                <Layers size={16} />
              </button>
            )}

            {isLoading && onStop ? (
              <button
                type="button"
                onClick={onStop}
                className="p-2.5 bg-destructive text-destructive-foreground rounded-xl hover:opacity-90 transition-all shadow-subtle flex items-center justify-center"
                title="Stop generation"
                aria-label="Stop generation"
              >
                <Square size={15} className="fill-current" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="p-2.5 bg-primary text-primary-foreground rounded-xl hover:opacity-90 transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-subtle flex items-center justify-center"
                title="Send message"
                aria-label="Send message"
              >
                <Send size={15} />
              </button>
            )}
          </div>
        </form>

        <div className="flex items-center justify-between mt-2 px-1 text-[11px] text-muted-foreground">
          <span>
            Click <Paperclip size={11} className="inline text-primary" /> to attach files, or drag & drop documents directly into chat.
          </span>
          <span className="hidden sm:inline">
            <kbd className="px-1.5 py-0.5 bg-muted border border-border/70 rounded text-[10px] text-muted-foreground font-mono">
              Enter
            </kbd>{" "}
            to send,{" "}
            <kbd className="px-1.5 py-0.5 bg-muted border border-border/70 rounded text-[10px] text-muted-foreground font-mono">
              Shift + Enter
            </kbd>{" "}
            for newline
          </span>
        </div>
      </div>
    </div>
  );
}
