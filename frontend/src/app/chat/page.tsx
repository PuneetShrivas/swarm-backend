'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Message {
  role: 'user' | 'agent';
  content: string;
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

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    // Simulate backend response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { role: 'agent', content: 'I have received your message and processing it with the swarm.' }
      ]);
    }, 1000);
  };

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900">
      {/* Sidebar for Agents */}
      <div className="w-64 bg-white border-r border-gray-200 p-4 flex flex-col">
        <h2 className="text-xl font-bold mb-4">Active Swarm</h2>
        <div className="flex-1 overflow-y-auto">
          {agents.length === 0 ? (
            <p className="text-gray-500 text-sm">No active agents.</p>
          ) : (
            <ul className="space-y-2">
              {agents.map((agent) => (
                <li key={agent.id} className="p-3 bg-gray-100 rounded-lg">
                  <div className="font-semibold">{agent.name}</div>
                  <div className="text-xs text-gray-600">{agent.role}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
        <Link href="/" className="mt-4 text-sm text-blue-600 hover:underline">
          &larr; Back to Home
        </Link>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 p-6 overflow-y-auto space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xl p-4 rounded-2xl ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-white border border-gray-200 text-gray-900 rounded-bl-none shadow-sm'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 bg-white border-t border-gray-200">
          <form onSubmit={handleSend} className="flex gap-2">
            <input
              type="text"
              className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button
              type="submit"
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}