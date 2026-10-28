"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { Bot, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import {
  Agent,
  ConversationState,
  ChatSession,
  UserUsageSummary,
  createInitialState,
  getActivePath,
  getSiblingInfo,
  addMessageNode,
  switchBranch,
  setNodeRating,
  exportToMarkdown,
  reconstructTreeFromMessages,
} from "./types";
import MessageItem from "./components/MessageItem";
import ChatInput from "./components/ChatInput";
import ChatHeader from "./components/ChatHeader";
import SessionSidebar from "./components/SessionSidebar";
import UsageModal from "./components/UsageModal";
import AgentDetailsModal from "./components/AgentDetailsModal";
import WorkflowPickerModal from "./components/WorkflowPickerModal";

export default function Chat() {
  const [conversation, setConversation] = useState<ConversationState>(() =>
    createInitialState()
  );
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Authentication & Sessions State
  const [session, setSession] = useState<Session | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);

  // Usage Telemetry State
  const [usage, setUsage] = useState<UserUsageSummary | null>(null);
  const [isUsageModalOpen, setIsUsageModalOpen] = useState(false);
  const [isLoadingUsage, setIsLoadingUsage] = useState(false);

  // Agent Inspection Modal State
  const [inspectingAgent, setInspectingAgent] = useState<Agent | null>(null);
  const [isAgentDetailsOpen, setIsAgentDetailsOpen] = useState(false);

  // Workflow Launcher State
  const [isWorkflowPickerOpen, setIsWorkflowPickerOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const activePath = getActivePath(
    conversation.nodes,
    conversation.currentLeafId
  );

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [conversation.currentLeafId, activePath.length, scrollToBottom]);

  // Load single session message tree
  const loadSessionMessages = useCallback(
    async (sessionId: string, token: string) => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/sessions/${sessionId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          const reconstructed = reconstructTreeFromMessages(data.messages);
          setConversation(reconstructed);
        }
      } catch (err) {
        console.error("Failed to load session messages", err);
      }
    },
    []
  );

  // Fetch user usage summary
  const fetchUsage = useCallback(async (token: string) => {
    setIsLoadingUsage(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/usage`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data: UserUsageSummary = await res.json();
        setUsage(data);
      }
    } catch (err) {
      console.error("Failed to load usage stats", err);
    } finally {
      setIsLoadingUsage(false);
    }
  }, []);

  // Fetch all chat sessions for the authenticated user
  const fetchSessions = useCallback(
    async (token: string) => {
      setIsLoadingSessions(true);
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/sessions`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data: ChatSession[] = await res.json();
          setSessions(data);
          if (data.length > 0 && !activeSessionId) {
            setActiveSessionId(data[0].id);
            await loadSessionMessages(data[0].id, token);
          }
        }
      } catch (error) {
        console.error("Failed to fetch sessions", error);
      } finally {
        setIsLoadingSessions(false);
      }
    },
    [activeSessionId, loadSessionMessages]
  );

  // Initialize Supabase Auth & Session Listeners
  useEffect(() => {
    const initAuth = async () => {
      try {
        const {
          data: { session: initialSession },
        } = await supabase.auth.getSession();
        if (initialSession) {
          setSession(initialSession);
          setUserEmail(initialSession.user.email || null);
          fetchSessions(initialSession.access_token);
          fetchUsage(initialSession.access_token);
        }
      } catch (err) {
        console.warn("Supabase auth getSession notice:", err);
      }
    };

    initAuth();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      setSession(currentSession);
      setUserEmail(currentSession?.user.email || null);
      if (currentSession) {
        fetchSessions(currentSession.access_token);
        fetchUsage(currentSession.access_token);
      } else {
        setSessions([]);
        setActiveSessionId(null);
        setUsage(null);
      }
    });

    return () => subscription.unsubscribe();
  }, [fetchSessions, fetchUsage]);

  // Fetch active agents from FastAPI backend
  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/agents`);
        if (res.ok) {
          const data: Agent[] = await res.json();
          setAgents(data);
        }
      } catch (error) {
        console.error("Failed to fetch agents", error);
      }
    };
    fetchAgents();
  }, []);

  // Send request to FastAPI /api/chat with session linking
  const requestSwarmResponse = async (
    chatHistory: { role: string; content: string; metadata?: Record<string, unknown> }[],
    userMessageNodeId: string,
    targetSessionId?: string | null,
    userParentNodeId?: string | null,
    workflowId?: string,
    workflowInputs?: Record<string, unknown>
  ) => {
    setIsLoading(true);
    abortControllerRef.current = new AbortController();

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (session?.access_token) {
        headers["Authorization"] = `Bearer ${session.access_token}`;
      }

      // Sanitize user parent: root-greeting is a client placeholder, not a DB record
      const cleanUserParentId =
        userParentNodeId && userParentNodeId !== "root-greeting"
          ? userParentNodeId
          : null;

      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          messages: chatHistory.map((m) => ({
            role: m.role,
            content: m.content,
            metadata: m.metadata || {},
          })),
          session_id: targetSessionId || activeSessionId || null,
          user_message_id: userMessageNodeId,
          parent_message_id: cleanUserParentId,
          workflow_id: workflowId || null,
          workflow_inputs: workflowInputs || {},
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
          "agent",
          data.content || "I have completed processing.",
          userMessageNodeId,
          data.metadata || { agent_state: "completed" }
        );
        return newState;
      });

      // Refresh usage summary after successful turn
      if (session?.access_token) {
        fetchUsage(session.access_token);
      }
    } catch (error: unknown) {
      if ((error as { name?: string })?.name === "AbortError") {
        console.log("Chat generation aborted by user.");
        return;
      }
      console.error("Error invoking swarm chat API:", error);
      setConversation((latestState) => {
        const { newState } = addMessageNode(
          latestState,
          "agent",
          "Sorry, I encountered an error communicating with the agent swarm. Please try again.",
          userMessageNodeId,
          { agent_state: "error" }
        );
        return newState;
      });
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  // Switch active session
  const handleSelectSession = (sessionId: string) => {
    if (sessionId === activeSessionId) return;
    setActiveSessionId(sessionId);
    if (session?.access_token) {
      loadSessionMessages(sessionId, session.access_token);
    }
  };

  // Create new session
  const handleCreateSession = async () => {
    if (!session?.access_token) {
      setActiveSessionId(null);
      setConversation(createInitialState());
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/sessions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ title: "New Conversation" }),
      });
      if (res.ok) {
        const newSession: ChatSession = await res.json();
        setSessions((prev) => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
        setConversation(createInitialState());
      }
    } catch (err) {
      console.error("Failed to create session", err);
    }
  };

  // Delete session
  const handleDeleteSession = async (sessionId: string) => {
    if (!session?.access_token) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/sessions/${sessionId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        if (activeSessionId === sessionId) {
          const remaining = sessions.filter((s) => s.id !== sessionId);
          if (remaining.length > 0) {
            setActiveSessionId(remaining[0].id);
            loadSessionMessages(remaining[0].id, session.access_token);
          } else {
            setActiveSessionId(null);
            setConversation(createInitialState());
          }
        }
      }
    } catch (err) {
      console.error("Failed to delete session", err);
    }
  };

  // Rename session
  const handleRenameSession = async (sessionId: string, newTitle: string) => {
    if (!session?.access_token) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/sessions/${sessionId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ title: newTitle }),
      });
      if (res.ok) {
        setSessions((prev) =>
          prev.map((s) => (s.id === sessionId ? { ...s, title: newTitle } : s))
        );
      }
    } catch (err) {
      console.error("Failed to rename session", err);
    }
  };

  // Handle standard user prompt submission (with auto-session creation)
  const handleSend = async (content: string) => {
    if (isLoading) return;

    let targetSessionId = activeSessionId;

    // Auto-create session if authenticated user is on a new unsaved chat
    if (session?.access_token && !targetSessionId) {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const cleanTitle =
          content.trim().slice(0, 32) + (content.length > 32 ? "..." : "");
        const res = await fetch(`${apiUrl}/api/sessions`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({ title: cleanTitle }),
        });
        if (res.ok) {
          const newSession: ChatSession = await res.json();
          setSessions((prev) => [newSession, ...prev]);
          setActiveSessionId(newSession.id);
          targetSessionId = newSession.id;
        }
      } catch (err) {
        console.error("Auto session creation error:", err);
      }
    }

    const userParent = conversation.currentLeafId;
    const { newState, newNodeId } = addMessageNode(
      conversation,
      "user",
      content,
      conversation.currentLeafId,
      selectedAgentId ? { target_agent_id: selectedAgentId } : undefined
    );

    setConversation(newState);
    const updatedPath = getActivePath(newState.nodes, newNodeId);
    requestSwarmResponse(updatedPath, newNodeId, targetSessionId, userParent);
  };

  // Handle invoking an autonomous workflow inside chat
  const handleRunWorkflow = async (
    workflowId: string,
    inputs: Record<string, unknown>
  ) => {
    let targetSessionId = activeSessionId;
    if (!targetSessionId && session?.access_token) {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/sessions`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({ title: `Workflow Run: ${workflowId.slice(0, 8)}` }),
        });
        if (res.ok) {
          const newSession = await res.json();
          setSessions((prev) => [newSession, ...prev]);
          setActiveSessionId(newSession.id);
          targetSessionId = newSession.id;
        }
      } catch (err) {
        console.error("Auto session creation error for workflow:", err);
      }
    }

    const userParent = conversation.currentLeafId;
    const promptText = `/workflow ${workflowId}`;
    const { newState, newNodeId } = addMessageNode(
      conversation,
      "user",
      promptText,
      conversation.currentLeafId,
      { workflow_id: workflowId, workflow_inputs: inputs }
    );

    setConversation(newState);
    const updatedPath = getActivePath(newState.nodes, newNodeId);
    requestSwarmResponse(updatedPath, newNodeId, targetSessionId, userParent, workflowId, inputs);
  };

  // Handle editing an existing user prompt (creates a sibling branch)
  const handleEdit = (nodeId: string, newContent: string) => {
    if (isLoading) return;

    const targetNode = conversation.nodes[nodeId];
    if (!targetNode) return;
    const userParent = targetNode.parentId;

    const { newState, newNodeId } = addMessageNode(
      conversation,
      "user",
      newContent,
      targetNode.parentId,
      selectedAgentId ? { target_agent_id: selectedAgentId } : undefined
    );

    setConversation(newState);
    const updatedPath = getActivePath(newState.nodes, newNodeId);
    requestSwarmResponse(updatedPath, newNodeId, activeSessionId, userParent);
  };

  // Handle regenerating an agent response (creates a sibling agent variant)
  const handleRegenerate = (agentNodeId: string) => {
    if (isLoading) return;

    const agentNode = conversation.nodes[agentNodeId];
    if (!agentNode || !agentNode.parentId) return;

    const userParentNode = conversation.nodes[agentNode.parentId];
    if (!userParentNode) return;

    const pathUpToUser = getActivePath(conversation.nodes, userParentNode.id);
    requestSwarmResponse(
      pathUpToUser,
      userParentNode.id,
      activeSessionId,
      userParentNode.parentId
    );
  };

  // Handle branch navigation (< 1 / 2 >)
  const handleSwitchBranch = (targetSiblingId: string) => {
    setConversation((prev) => switchBranch(prev, targetSiblingId));
  };

  // Handle rating feedback
  const handleRate = (nodeId: string, rating: "up" | "down" | null) => {
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
      window.confirm("Are you sure you want to clear the conversation?")
    ) {
      setConversation(createInitialState());
    }
  };

  // Sign out handler
  const handleSignOut = async () => {
    await supabase.auth.signOut();
    setSession(null);
    setUserEmail(null);
    setSessions([]);
    setActiveSessionId(null);
    setUsage(null);
    setConversation(createInitialState());
  };

  // Export conversation to Markdown
  const handleExportChat = () => {
    const md = exportToMarkdown(activePath);
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `swarm-conversation-${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const currentSessionObj = sessions.find((s) => s.id === activeSessionId);

  return (
    <div className="flex h-screen bg-background text-foreground font-sans overflow-hidden transition-colors duration-200">
      {/* Session History & Swarm Sidebar */}
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
        onRenameSession={handleRenameSession}
        userEmail={userEmail}
        onSignOut={handleSignOut}
        onOpenUsage={() => setIsUsageModalOpen(true)}
        totalTokensUsed={usage?.total_tokens ?? 0}
        agents={agents}
        selectedAgentId={selectedAgentId}
        onSelectAgent={setSelectedAgentId}
        isLoadingSessions={isLoadingSessions}
        onInspectAgent={(ag) => {
          setInspectingAgent(ag);
          setIsAgentDetailsOpen(true);
        }}
      />

      {/* Main Chat Feed Area */}
      <div className="flex-1 flex flex-col bg-background relative overflow-hidden h-full">
        {/* Top Header */}
        <ChatHeader
          agents={agents}
          selectedAgentId={selectedAgentId}
          onSelectAgent={setSelectedAgentId}
          onClearChat={handleClearChat}
          onExportChat={handleExportChat}
          activePathCount={activePath.length}
          sessionTitle={currentSessionObj?.title}
          totalTokensUsed={usage?.total_tokens}
          onOpenUsage={() => setIsUsageModalOpen(true)}
          onInspectAgent={(ag) => {
            setInspectingAgent(ag);
            setIsAgentDetailsOpen(true);
          }}
        />

        {/* Message Feed */}
        <main className="flex-1 p-4 md:p-8 overflow-y-auto space-y-6 scroll-smooth bg-background">
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
                <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-subtle bg-card border border-border text-primary">
                  <Bot size={15} />
                </div>
                <div className="px-5 py-4 rounded-2xl bg-card border border-border/80 text-foreground rounded-tl-sm flex items-center gap-2.5 shadow-subtle">
                  <Loader2 size={16} className="animate-spin text-primary" />
                  <span className="text-xs font-medium text-muted-foreground">
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
          onOpenWorkflowPicker={() => setIsWorkflowPickerOpen(true)}
        />
      </div>

      {/* Usage Telemetry Modal */}
      <UsageModal
        isOpen={isUsageModalOpen}
        onClose={() => setIsUsageModalOpen(false)}
        usage={usage}
        isLoading={isLoadingUsage}
        onRefresh={() => session?.access_token && fetchUsage(session.access_token)}
      />

      {/* Agent Inspector Modal */}
      <AgentDetailsModal
        agent={inspectingAgent}
        isOpen={isAgentDetailsOpen}
        onClose={() => setIsAgentDetailsOpen(false)}
      />

      {/* Workflow Launcher Modal */}
      <WorkflowPickerModal
        isOpen={isWorkflowPickerOpen}
        onClose={() => setIsWorkflowPickerOpen(false)}
        onRunWorkflow={handleRunWorkflow}
      />
    </div>
  );
}
