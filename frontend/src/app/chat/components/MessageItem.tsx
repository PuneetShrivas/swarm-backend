'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot,
  User,
  Copy,
  Check,
  Pencil,
  RotateCcw,
  ThumbsUp,
  ThumbsDown,
  ChevronLeft,
  ChevronRight,
  Wrench,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { ChatNode } from '../types';

interface MessageItemProps {
  node: ChatNode;
  siblingInfo: { index: number; total: number; siblingIds: string[] };
  onSwitchBranch: (targetSiblingId: string) => void;
  onEdit: (nodeId: string, newContent: string) => void;
  onRegenerate: (nodeId: string) => void;
  onRate: (nodeId: string, rating: 'up' | 'down' | null) => void;
  isGenerating?: boolean;
}

export default function MessageItem({
  node,
  siblingInfo,
  onSwitchBranch,
  onEdit,
  onRegenerate,
  onRate,
  isGenerating = false,
}: MessageItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(node.content);
  const [copied, setCopied] = useState(false);
  const [showTools, setShowTools] = useState(false);

  const isUser = node.role === 'user';
  const hasMultipleVersions = siblingInfo.total > 1;
  const hasToolCalls =
    node.metadata?.tool_calls && node.metadata.tool_calls.length > 0;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(node.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard', err);
    }
  };

  const handleSaveEdit = () => {
    if (!editContent.trim()) return;
    onEdit(node.id, editContent);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditContent(node.content);
    setIsEditing(false);
  };

  const handlePrevBranch = () => {
    if (siblingInfo.index > 1) {
      const prevId = siblingInfo.siblingIds[siblingInfo.index - 2];
      onSwitchBranch(prevId);
    }
  };

  const handleNextBranch = () => {
    if (siblingInfo.index < siblingInfo.total) {
      const nextId = siblingInfo.siblingIds[siblingInfo.index];
      onSwitchBranch(nextId);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`group flex gap-3 md:gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm border ${
          isUser
            ? 'bg-blue-600 border-blue-500 text-white'
            : 'bg-white border-slate-200 text-blue-600'
        }`}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Message Body & Actions Container */}
      <div
        className={`flex flex-col max-w-[85%] md:max-w-2xl ${
          isUser ? 'items-end' : 'items-start'
        }`}
      >
        {/* Main Content Bubble */}
        <div
          className={`px-5 py-3.5 rounded-2xl text-[15px] leading-relaxed shadow-sm transition-all relative ${
            isUser
              ? 'bg-blue-600 text-white rounded-tr-sm'
              : 'bg-white border border-slate-200/90 text-slate-800 rounded-tl-sm'
          }`}
        >
          {isEditing ? (
            <div className="w-full min-w-[280px] sm:min-w-[420px] text-slate-900">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={3}
                className="w-full p-2.5 bg-white text-slate-900 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Edit your message..."
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Escape') handleCancelEdit();
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey))
                    handleSaveEdit();
                }}
              />
              <div className="flex justify-end gap-2 mt-2">
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveEdit}
                  disabled={!editContent.trim()}
                  className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg transition shadow-sm"
                >
                  Save & Submit
                </button>
              </div>
            </div>
          ) : (
            <>
              <div
                className={`prose prose-sm max-w-none break-words ${
                  isUser ? 'prose-invert' : 'prose-slate'
                }`}
              >
                <ReactMarkdown>{node.content}</ReactMarkdown>
              </div>

              {/* Tool Calls Accordion */}
              {hasToolCalls && (
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setShowTools(!showTools)}
                    className="flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 bg-slate-50 hover:bg-slate-100 px-2.5 py-1.5 rounded-lg border border-slate-200/80 transition"
                  >
                    <Wrench size={13} className="text-amber-600" />
                    <span>
                      {node.metadata?.tool_calls?.length}{' '}
                      {node.metadata?.tool_calls?.length === 1
                        ? 'tool call'
                        : 'tool calls'}
                    </span>
                    {showTools ? (
                      <ChevronUp size={13} className="ml-0.5 text-slate-400" />
                    ) : (
                      <ChevronDown
                        size={13}
                        className="ml-0.5 text-slate-400"
                      />
                    )}
                  </button>

                  <AnimatePresence>
                    {showTools && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-2 space-y-2 overflow-hidden text-xs"
                      >
                        {node.metadata?.tool_calls?.map((tc, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded-lg bg-slate-900 text-slate-200 font-mono text-[11px] overflow-x-auto"
                          >
                            <div className="text-amber-400 font-semibold mb-1">
                              ⚡ {tc.tool}
                            </div>
                            {tc.args && (
                              <div className="text-slate-400">
                                args: {JSON.stringify(tc.args)}
                              </div>
                            )}
                            {tc.result !== undefined && (
                              <div className="text-emerald-400 mt-1">
                                result: {JSON.stringify(tc.result)}
                              </div>
                            )}
                          </div>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* Agent Execution Metadata Badges */}
              {node.metadata?.agent_state && (
                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                  <span className="inline-flex items-center gap-1.5 text-slate-500 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/70 text-[11px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                    State: {String(node.metadata.agent_state)}
                  </span>
                  {node.metadata?.agent_id && (
                    <span className="text-[11px] text-slate-400">
                      via {String(node.metadata.agent_id)}
                    </span>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Message Action Bar & Branch Switcher */}
        {!isEditing && (
          <div
            className={`flex items-center gap-1.5 mt-1.5 text-xs text-slate-400 select-none ${
              isUser ? 'flex-row-reverse' : 'flex-row'
            }`}
          >
            {/* Sibling Branch Switcher (< 1 / 2 >) */}
            {hasMultipleVersions && (
              <div className="flex items-center bg-slate-100 hover:bg-slate-200/80 rounded-lg px-1.5 py-0.5 text-[11px] font-medium text-slate-600 transition">
                <button
                  type="button"
                  onClick={handlePrevBranch}
                  disabled={siblingInfo.index <= 1}
                  className="p-0.5 hover:text-slate-900 disabled:opacity-30 disabled:cursor-not-allowed transition"
                  title="Previous version"
                  aria-label="Previous version"
                >
                  <ChevronLeft size={13} />
                </button>
                <span className="px-1 text-[11px]">
                  {siblingInfo.index} / {siblingInfo.total}
                </span>
                <button
                  type="button"
                  onClick={handleNextBranch}
                  disabled={siblingInfo.index >= siblingInfo.total}
                  className="p-0.5 hover:text-slate-900 disabled:opacity-30 disabled:cursor-not-allowed transition"
                  title="Next version"
                  aria-label="Next version"
                >
                  <ChevronRight size={13} />
                </button>
              </div>
            )}

            {/* Copy Button */}
            <button
              type="button"
              onClick={handleCopy}
              className="p-1 hover:text-slate-700 hover:bg-slate-100 rounded-md transition"
              title="Copy message"
              aria-label="Copy message"
            >
              {copied ? (
                <Check size={14} className="text-emerald-500" />
              ) : (
                <Copy size={14} />
              )}
            </button>

            {/* Edit Button (User Only) */}
            {isUser && (
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="p-1 hover:text-slate-700 hover:bg-slate-100 rounded-md transition"
                title="Edit message"
                aria-label="Edit message"
              >
                <Pencil size={14} />
              </button>
            )}

            {/* Actions for Agent Messages */}
            {!isUser && (
              <>
                {/* Regenerate Button */}
                <button
                  type="button"
                  onClick={() => onRegenerate(node.id)}
                  disabled={isGenerating}
                  className="p-1 hover:text-slate-700 hover:bg-slate-100 rounded-md transition disabled:opacity-40"
                  title="Regenerate response"
                  aria-label="Regenerate response"
                >
                  <RotateCcw size={14} />
                </button>

                {/* Thumbs Up Button */}
                <button
                  type="button"
                  onClick={() =>
                    onRate(node.id, node.rating === 'up' ? null : 'up')
                  }
                  className={`p-1 rounded-md transition ${
                    node.rating === 'up'
                      ? 'text-emerald-600 bg-emerald-50'
                      : 'hover:text-slate-700 hover:bg-slate-100'
                  }`}
                  title="Helpful / Good response"
                  aria-label="Thumbs up"
                >
                  <ThumbsUp size={14} />
                </button>

                {/* Thumbs Down Button */}
                <button
                  type="button"
                  onClick={() =>
                    onRate(node.id, node.rating === 'down' ? null : 'down')
                  }
                  className={`p-1 rounded-md transition ${
                    node.rating === 'down'
                      ? 'text-rose-600 bg-rose-50'
                      : 'hover:text-slate-700 hover:bg-slate-100'
                  }`}
                  title="Unhelpful / Bad response"
                  aria-label="Thumbs down"
                >
                  <ThumbsDown size={14} />
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
