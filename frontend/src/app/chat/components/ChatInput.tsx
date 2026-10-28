"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Square } from "lucide-react";

interface ChatInputProps {
  onSend: (content: string) => void;
  isLoading: boolean;
  onStop?: () => void;
  placeholder?: string;
}

export default function ChatInput({
  onSend,
  isLoading,
  onStop,
  placeholder = "Message the swarm...",
}: ChatInputProps) {
  const [input, setInput] = useState("");
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

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    onSend(input.trim());
    setInput("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-3 md:p-5 bg-card/75 backdrop-blur-xl border-t border-border/70 sticky bottom-0 z-10 transition-colors duration-200">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="relative flex items-end">
          <textarea
            ref={textareaRef}
            rows={1}
            className="w-full pl-4 pr-14 py-3.5 bg-muted/40 border border-border/80 focus:border-primary/60 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm sm:text-[15px] text-foreground placeholder:text-muted-foreground resize-none shadow-subtle leading-relaxed"
            placeholder={placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />

          <div className="absolute right-2.5 bottom-2.5 flex items-center">
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
          <span>Swarm intelligence can make mistakes. Verify critical facts.</span>
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
