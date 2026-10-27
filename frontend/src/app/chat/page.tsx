'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User, ArrowLeft, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  role: 'user' | 'agent';
  content: string;
  metadata?: Record<string, unknown>;
}

interface Agent {
  id: string;
  name: string;
  role: string;
  status: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'agent', content: 'Hello! I am part of the agent swarm. How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Fetch agents from the backend
    const fetchAgents = async () => {
      try {
        const res = await fetch(process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/agents` : 'http://localhost:8000/api/agents');
        if (res.ok) {
          const data = await res.json();
          setAgents(data);
        }
      } catch (error) {
        console.error("Failed to fetch agents", error);
      }
    };
    fetchAgents();
  }, []);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    const currentMessages = [...messages, userMessage];
    setMessages(currentMessages);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch(process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/chat` : 'http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: currentMessages })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [...prev, data]);
      } else {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      console.error(error);
      setMessages((prev) => [...prev, { role: 'agent', content: 'Sorry, I encountered an error.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar for Agents */}
      <div className="w-72 bg-white border-r border-slate-200 p-6 flex flex-col shadow-sm z-10 hidden md:flex">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
            <Bot size={20} className="text-white" />
          </div>
          <h2 className="text-xl font-bold tracking-tight text-slate-800">Active Swarm</h2>
        </div>

        <div className="flex-1 overflow-y-auto">
          {agents.length === 0 ? (
            <div className="text-center p-4 bg-slate-50 rounded-xl border border-dashed border-slate-300">
              <p className="text-slate-500 text-sm">No active agents online.</p>
            </div>
          ) : (
            <ul className="space-y-3">
              {agents.map((agent) => (
                <li key={agent.id} className="p-3 bg-slate-50 hover:bg-slate-100 border border-slate-100 rounded-xl transition cursor-default">
                  <div className="flex items-center justify-between mb-1">
                    <div className="font-semibold text-slate-800">{agent.name}</div>
                    <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                  </div>
                  <div className="text-xs text-slate-500">{agent.role}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
        <Link href="/" className="mt-6 flex items-center text-sm font-medium text-slate-500 hover:text-slate-800 transition">
          <ArrowLeft size={16} className="mr-2" />
          Back to Home
        </Link>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-white/50 relative">
        <div className="flex-1 p-4 md:p-8 overflow-y-auto space-y-6 scroll-smooth">
          <AnimatePresence initial={false}>
            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${msg.role === 'user' ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-600'}`}>
                  {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>
                <div
                  className={`max-w-2xl px-5 py-3.5 rounded-2xl text-[15px] leading-relaxed shadow-sm ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-tr-sm'
                      : 'bg-white border border-slate-200 text-slate-700 rounded-tl-sm'
                  }`}
                >
                  <div className={`prose prose-sm max-w-none ${msg.role === 'user' ? 'prose-invert' : 'prose-slate'}`}>
                    <ReactMarkdown>
                      {msg.content}
                    </ReactMarkdown>
                  </div>

                  {msg.metadata?.agent_state && typeof msg.metadata.agent_state === 'string' ? (
                     <div className="mt-3 text-xs flex items-center gap-2 text-slate-400 bg-slate-50/50 p-2 rounded-lg border border-slate-100 inline-flex">
                       <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
                       Agent state: {msg.metadata.agent_state}
                     </div>
                  ) : null}
                </div>
              </motion.div>
            ))}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-4 flex-row"
              >
                <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm bg-slate-100 text-slate-600">
                  <Bot size={16} />
                </div>
                <div className="px-5 py-4 rounded-2xl bg-white border border-slate-200 text-slate-700 rounded-tl-sm flex items-center gap-2">
                   <Loader2 size={16} className="animate-spin text-slate-400" />
                   <span className="text-sm text-slate-500">Processing...</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 md:p-6 bg-white/80 backdrop-blur-md border-t border-slate-200/60 sticky bottom-0">
          <div className="max-w-4xl mx-auto">
            <form onSubmit={handleSend} className="relative flex items-center">
              <input
                type="text"
                className="flex-1 pl-5 pr-14 py-4 bg-slate-50 border border-slate-200 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-[15px] shadow-sm"
                placeholder="Message the swarm..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="absolute right-2 p-2.5 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
              >
                <Send size={18} />
              </button>
            </form>
            <div className="text-center mt-3">
              <span className="text-[11px] text-slate-400 font-medium">Agent Swarm can make mistakes. Verify important info.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}