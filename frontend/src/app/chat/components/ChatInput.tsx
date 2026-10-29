"use client";

import { useState, useRef, useEffect } from "react";
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
} from "lucide-react";

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
  onSend: (content: string, attachedArtifacts?: AttachedArtifact[]) => void;
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

const SLASH_COMMANDS: SlashCommand[] = [
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

  // Determine active slash command suggestions
  const isSlashActive = input.startsWith("/") && !isDismissed;
  const slashQuery = input.startsWith("/") ? input.slice(1).toLowerCase().trim() : "";
  const matchingCommands = SLASH_COMMANDS.filter(
    (c) =>
      c.command.toLowerCase().includes(slashQuery) ||
      c.id.toLowerCase().includes(slashQuery) ||
      c.label.toLowerCase().includes(slashQuery)
  );

  const executeCommand = (cmd: SlashCommand) => {
    setInput("");
    setIsDismissed(true);
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

    onSend(trimmed, attachedArtifacts);
    setInput("");
    setIsDismissed(false);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
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

        {/* Attached Artifacts Chips Bar */}
        {attachedArtifacts.length > 0 && (
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-2.5 animate-fade-in">
            <span className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider shrink-0 flex items-center gap-1">
              <Paperclip size={11} className="text-primary" /> Context:
            </span>
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
