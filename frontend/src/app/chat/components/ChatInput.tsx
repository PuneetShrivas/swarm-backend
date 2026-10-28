"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Square, Layers, Bot, RotateCcw, Sparkles } from "lucide-react";

interface SlashCommand {
  id: string;
  command: string;
  label: string;
  description: string;
  icon: typeof Layers;
}

interface ChatInputProps {
  onSend: (content: string) => void;
  isLoading: boolean;
  onStop?: () => void;
  placeholder?: string;
  onOpenWorkflowPicker?: () => void;
  onClearChat?: () => void;
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
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [isDismissed, setIsDismissed] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const scrollHeight = textareaRef.current.scrollHeight;
      // Cap at 180px
      textareaRef.current.style.height = `${Math.min(scrollHeight, 180)}px`;
    }
  }, [input]);

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
      onSend("Show me the active swarm agents and their capabilities.");
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

    onSend(trimmed);
    setInput("");
    setIsDismissed(false);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // If slash suggestions are open, handle navigation
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

  return (
    <div className="p-3 md:p-5 bg-card/75 backdrop-blur-xl border-t border-border/70 sticky bottom-0 z-10 transition-colors duration-200">
      <div className="max-w-4xl mx-auto relative">
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

        <form onSubmit={handleSubmit} className="relative flex items-end">
          <textarea
            ref={textareaRef}
            rows={1}
            className="w-full pl-4 pr-14 py-3.5 bg-muted/40 border border-border/80 focus:border-primary/60 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm sm:text-[15px] text-foreground placeholder:text-muted-foreground resize-none shadow-subtle leading-relaxed"
            placeholder={placeholder}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />

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
          <span>Type <code className="text-primary font-mono font-semibold">/workflows</code> to launch autonomous pipelines.</span>
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
