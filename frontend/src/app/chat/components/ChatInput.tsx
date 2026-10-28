'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Square } from 'lucide-react';

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
  placeholder = 'Message the swarm...',
}: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      // Cap at 180px
      textareaRef.current.style.height = `${Math.min(scrollHeight, 180)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    onSend(input.trim());
    setInput('');

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-3 md:p-5 bg-white/85 backdrop-blur-md border-t border-slate-200/70 sticky bottom-0 z-10">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="relative flex items-end">
          <textarea
            ref={textareaRef}
            rows={1}
            className="w-full pl-4 pr-14 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-[15px] resize-none shadow-sm leading-relaxed"
            placeholder={placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />

          <div className="absolute right-2 bottom-2 flex items-center">
            {isLoading && onStop ? (
              <button
                type="button"
                onClick={onStop}
                className="p-2.5 bg-rose-600 text-white rounded-xl hover:bg-rose-700 transition shadow-sm flex items-center justify-center"
                title="Stop generation"
                aria-label="Stop generation"
              >
                <Square size={16} className="fill-current" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition disabled:opacity-40 disabled:cursor-not-allowed shadow-sm flex items-center justify-center"
                title="Send message"
                aria-label="Send message"
              >
                <Send size={16} />
              </button>
            )}
          </div>
        </form>

        <div className="flex items-center justify-between mt-2 px-1 text-[11px] text-slate-400">
          <span>Agent Swarm can make mistakes. Verify important info.</span>
          <span className="hidden sm:inline">
            <kbd className="px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded text-[10px] text-slate-500 font-mono">
              Enter
            </kbd>{' '}
            to send,{' '}
            <kbd className="px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded text-[10px] text-slate-500 font-mono">
              Shift + Enter
            </kbd>{' '}
            for newline
          </span>
        </div>
      </div>
    </div>
  );
}
