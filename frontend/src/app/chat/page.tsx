'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { Bot, ArrowLeft, Loader2, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import {
  Agent,
  ConversationState,
  createInitialState,
  getActivePath,
  getSiblingInfo,
  addMessageNode,
  switchBranch,
  setNodeRating,
  exportToMarkdown,
} from './types';
import MessageItem from './components/MessageItem';
import ChatInput from './components/ChatInput';
import ChatHeader from './components/ChatHeader';

export default function Chat() {
  const [conversation, setConversation] = useState<ConversationState>(() =>
    createInitialState()
  );
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const activePath = getActivePath(
    conversation.nodes,
    conversation.currentLeafId
  );

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [conversation.currentLeafId, activePath.length, scrollToBottom]);

  // Fetch active agents from FastAPI backend
  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${apiUrl}/api/agents`);
        if (res.ok) {
          const data: Agent[] = await res.json();
          setAgents(data);
        }
      } catch (error) {
        console.error('Failed to fetch agents', error);
      }
    };
    fetchAgents();
  }, []);

  // Send request to FastAPI /api/chat
  const requestSwarmResponse = async (
    chatHistory: { role: string; content: string; metadata?: Record<string, unknown> }[],
    parentUserNodeId: string
  ) => {
    setIsLoading(true);
    abortControllerRef.current = new AbortController();

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: chatHistory.map((m) => ({
            role: m.role,
            content: m.content,
            metadata: m.metadata || {},
          })),
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!res.ok) {
        throw new Error(`API responded with status ${res.status}`);
      }

      const data = await res.json();

      setConversation((latestState) => {
        const { newState } = addMessageNode(
          latestState,
          'agent',
          data.content || 'I have completed processing.',
          parentUserNodeId,
          data.metadata || { agent_state: 'completed' }
        );
        return newState;
      });
    } catch (error: unknown) {
      if ((error as { name?: string })?.name === 'AbortError') {
        console.log('Chat generation aborted by user.');
        return;
      }
      console.error('Error invoking swarm chat API:', error);
      setConversation((latestState) => {
        const { newState } = addMessageNode(
          latestState,
          'agent',
          'Sorry, I encountered an error communicating with the agent swarm. Please try again.',
          parentUserNodeId,
          { agent_state: 'error' }
        );
        return newState;
      });
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  // Handle standard user prompt submission
  const handleSend = (content: string) => {
    if (isLoading) return;

    const { newState, newNodeId } = addMessageNode(
      conversation,
      'user',
      content,
      conversation.currentLeafId,
      selectedAgentId ? { target_agent_id: selectedAgentId } : undefined
    );

    setConversation(newState);

    const updatedPath = getActivePath(newState.nodes, newNodeId);
    requestSwarmResponse(updatedPath, newNodeId);
  };

  // Handle editing an existing user prompt (creates a sibling branch)
  const handleEdit = (nodeId: string, newContent: string) => {
    if (isLoading) return;

    const targetNode = conversation.nodes[nodeId];
    if (!targetNode) return;

    // Sibling of targetNode gets same parentId
    const { newState, newNodeId } = addMessageNode(
      conversation,
      'user',
      newContent,
      targetNode.parentId,
      selectedAgentId ? { target_agent_id: selectedAgentId } : undefined
    );

    setConversation(newState);

    const updatedPath = getActivePath(newState.nodes, newNodeId);
    requestSwarmResponse(updatedPath, newNodeId);
  };

  // Handle regenerating an agent response (creates a sibling agent variant)
  const handleRegenerate = (agentNodeId: string) => {
    if (isLoading) return;

    const agentNode = conversation.nodes[agentNodeId];
    if (!agentNode || !agentNode.parentId) return;

    const userParentNode = conversation.nodes[agentNode.parentId];
    if (!userParentNode) return;

    const pathUpToUser = getActivePath(conversation.nodes, userParentNode.id);
    requestSwarmResponse(pathUpToUser, userParentNode.id);
  };

  // Handle branch navigation (< 1 / 2 >)
  const handleSwitchBranch = (targetSiblingId: string) => {
    setConversation((prev) => switchBranch(prev, targetSiblingId));
  };

  // Handle rating feedback
  const handleRate = (nodeId: string, rating: 'up' | 'down' | null) => {
    setConversation((prev) => setNodeRating(prev, nodeId, rating));
  };

  // Handle stopping in-progress generation
  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  };

  // Clear conversation
  const handleClearChat = () => {
    if (
      activePath.length <= 1 ||
      window.confirm('Are you sure you want to clear the conversation?')
    ) {
      setConversation(createInitialState());
    }
  };

  // Export conversation to Markdown
  const handleExportChat = () => {
    const md = exportToMarkdown(activePath);
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `swarm-conversation-${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar for Agents */}
      <aside className="w-72 bg-white border-r border-slate-200 p-6 flex flex-col shadow-sm z-10 hidden md:flex">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-xs">
            <Bot size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold tracking-tight text-slate-800">
              Active Swarm
            </h2>
            <div className="text-[11px] text-slate-400">Agent Roster</div>
          </div>
        </div>

        {/* Swarm Roster */}
        <div className="flex-1 overflow-y-auto space-y-2">
          {agents.length === 0 ? (
            <div className="text-center p-4 bg-slate-50 rounded-xl border border-dashed border-slate-200">
              <p className="text-slate-500 text-xs">No active agents online.</p>
              <span className="text-[10px] text-slate-400 mt-1 block">
                Backend API: /api/agents
              </span>
            </div>
          ) : (
            <ul className="space-y-2">
              {agents.map((agent) => {
                const isSelected = selectedAgentId === agent.id;
                return (
                  <li
                    key={agent.id}
                    onClick={() =>
                      setSelectedAgentId(isSelected ? null : agent.id)
                    }
                    className={`p-3 border rounded-xl transition cursor-pointer ${
                      isSelected
                        ? 'bg-blue-50/70 border-blue-200 text-blue-900 shadow-xs'
                        : 'bg-slate-50 hover:bg-slate-100 border-slate-100 text-slate-800'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="font-medium text-xs text-slate-800 flex items-center gap-1.5">
                        <Sparkles
                          size={12}
                          className={isSelected ? 'text-blue-600' : 'text-slate-400'}
                        />
                        {agent.name}
                      </div>
                      <div
                        className={`w-2 h-2 rounded-full ${
                          agent.status === 'active'
                            ? 'bg-emerald-500'
                            : 'bg-amber-400'
                        }`}
                      />
                    </div>
                    <div className="text-[11px] text-slate-500">{agent.role}</div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <Link
          href="/"
          className="mt-6 flex items-center text-xs font-medium text-slate-500 hover:text-slate-800 transition pt-4 border-t border-slate-100"
        >
          <ArrowLeft size={14} className="mr-2" />
          Back to Overview
        </Link>
      </aside>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white/60 relative overflow-hidden">
        {/* Top Header */}
        <ChatHeader
          agents={agents}
          selectedAgentId={selectedAgentId}
          onSelectAgent={setSelectedAgentId}
          onClearChat={handleClearChat}
          onExportChat={handleExportChat}
          activePathCount={activePath.length}
        />

        {/* Message Feed */}
        <main className="flex-1 p-4 md:p-8 overflow-y-auto space-y-6 scroll-smooth">
          <AnimatePresence initial={false}>
            {activePath.map((node) => {
              const siblingInfo = getSiblingInfo(
                conversation.nodes,
                node.id
              );

              return (
                <MessageItem
                  key={node.id}
                  node={node}
                  siblingInfo={siblingInfo}
                  onSwitchBranch={handleSwitchBranch}
                  onEdit={handleEdit}
                  onRegenerate={handleRegenerate}
                  onRate={handleRate}
                  isGenerating={isLoading}
                />
              );
            })}

            {/* In-flight Processing Bubble */}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 5 }}
                className="flex gap-3 md:gap-4 flex-row"
              >
                <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm bg-white border border-slate-200 text-blue-600">
                  <Bot size={16} />
                </div>
                <div className="px-5 py-4 rounded-2xl bg-white border border-slate-200 text-slate-700 rounded-tl-sm flex items-center gap-2 shadow-xs">
                  <Loader2 size={16} className="animate-spin text-blue-600" />
                  <span className="text-xs font-medium text-slate-600">
                    Swarm agent reasoning...
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </main>

        {/* Bottom Input Area */}
        <ChatInput
          onSend={handleSend}
          isLoading={isLoading}
          onStop={handleStop}
        />
      </div>
    </div>
  );
}
