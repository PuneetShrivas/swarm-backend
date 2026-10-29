"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { Bot, Loader2, Workflow, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import AppNavigationRail from "../components/AppNavigationRail";
import BrandLogo from "@/components/BrandLogo";

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
import ChatInput, { AttachedArtifact } from "./components/ChatInput";
import ChatHeader from "./components/ChatHeader";
import AppUnifiedSidebar from "@/components/AppUnifiedSidebar";
import UsageModal from "./components/UsageModal";
import AgentDetailsModal from "./components/AgentDetailsModal";
import WorkflowPickerModal from "./components/WorkflowPickerModal";
import ArtifactSelectorModal, { ArtifactItem } from "./components/ArtifactSelectorModal";

function ChatContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlSessionId = searchParams?.get("session");
  const [conversation, setConversation] = useState<ConversationState>(() =>
    createInitialState()
  );
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  // Authentication & Sessions State
  const [session, setSession] = useState<Session | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);

  // Usage Telemetry State
  const [usage, setUsage] = useState<UserUsageSummary | null>(null);
  const [isUsageModalOpen, setIsUsageModalOpen] = useState(false);
  const [isLoadingUsage, setIsLoadingUsage] = useState(false);

  // Agent Inspection Modal State
  const [inspectingAgent, setInspectingAgent] = useState<Agent | null>(null);
  const [isAgentDetailsOpen, setIsAgentDetailsOpen] = useState(false);

  // Workflow Launcher State
  const [isWorkflowPickerOpen, setIsWorkflowPickerOpen] = useState(false);

  // Attached Context Artifacts State
  const [attachedArtifacts, setAttachedArtifacts] = useState<AttachedArtifact[]>([]);
  const [isArtifactSelectorOpen, setIsArtifactSelectorOpen] = useState(false);

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
      setIsLoadingMessages(true);
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
      } finally {
        setIsLoadingMessages(false);
      }
    },
    []
  );

  // Auto-select session when navigated via URL search param ?session=<id>
  useEffect(() => {
    if (urlSessionId && session?.access_token && urlSessionId !== activeSessionId) {
      setActiveSessionId(urlSessionId);
      loadSessionMessages(urlSessionId, session.access_token);
    }
  }, [urlSessionId, session?.access_token, activeSessionId, loadSessionMessages]);

  // Auto-attach invoked artifact from Artifacts Studio ?artifact_id=<id>
  const urlArtifactId = searchParams?.get("artifact_id");
  useEffect(() => {
    if (urlArtifactId) {
      try {
        const raw = localStorage.getItem("swarm_invoked_artifact");
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed && (parsed.id === urlArtifactId || !urlArtifactId)) {
            setAttachedArtifacts((prev) => {
              if (prev.some((a) => a.id === parsed.id)) return prev;
              return [...prev, parsed];
            });
            localStorage.removeItem("swarm_invoked_artifact");
          }
        }
      } catch {
        // Ignore parsing error
      }
    }
  }, [urlArtifactId]);

  // Handle uploading context files directly from chat input screen
  const handleUploadChatFile = async (file: File) => {
    try {
      const ext = (file.name.split(".").pop() || "txt").toLowerCase();
      const isBinary = ["pdf", "docx", "pptx", "xlsx", "zip"].includes(ext);

      let content = "";
      if (isBinary) {
        const b64DataUrl = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve((reader.result as string) || "");
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
        content = b64DataUrl.split(",")[1] || "";
      } else {
        content = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve((reader.result as string) || "");
          reader.onerror = reject;
          reader.readAsText(file);
        });
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (session?.access_token) {
        headers["Authorization"] = `Bearer ${session.access_token}`;
      }

      const payload = {
        id: `art-chat-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`,
        name: file.name,
        filename: file.name,
        type: ext,
        content,
        size_bytes: file.size,
        created_at: new Date().toISOString(),
        origin_agent: "chat_upload",
        source_type: "chat_upload",
        source_title: "Chat Context Upload",
        downloadable: true,
        is_base64: isBinary,
        encoding: isBinary ? "base64" : "utf-8",
      };

      const res = await fetch(`${apiUrl}/api/artifacts`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });

      const saved: AttachedArtifact = res.ok ? await res.json() : payload;

      try {
        const rawLocal = localStorage.getItem("swarm_local_artifacts");
        const list = rawLocal ? JSON.parse(rawLocal) : [];
        localStorage.setItem("swarm_local_artifacts", JSON.stringify([saved, ...list].slice(0, 50)));
      } catch {
        // Ignore cache error
      }

      setAttachedArtifacts((prev) => {
        if (prev.some((a) => a.id === saved.id)) return prev;
        return [...prev, saved];
      });
    } catch (err) {
      console.error("Failed to upload context file in chat:", err);
    }
  };

  const handleRemoveArtifact = (id: string) => {
    setAttachedArtifacts((prev) => prev.filter((a) => a.id !== id));
  };

  const handleSelectArtifacts = (selected: ArtifactItem[]) => {
    setAttachedArtifacts(selected);
  };

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
          // Default remains new chat view (activeSessionId = null) without auto-selecting previous session
        }
      } catch (error) {
        console.error("Failed to fetch sessions", error);
      } finally {
        setIsLoadingSessions(false);
      }
    },
    []
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
    workflowInputs?: Record<string, unknown>,
    artsToSend?: AttachedArtifact[]
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

      const activeArts = artsToSend || attachedArtifacts;

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
          model: selectedModel || undefined,
          artifact_ids: activeArts.map((a) => a.id),
          attached_artifacts: activeArts,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!res.ok) {
        throw new Error(`API responded with status ${res.status}`);
      }

      const data = await res.json();

      // If backend updated or derived session title, update sessions list
      if (data.metadata?.session_title && targetSessionId) {
        const renamedTitle = data.metadata.session_title;
        setSessions((prev) =>
          prev.map((s) => (s.id === targetSessionId ? { ...s, title: renamedTitle } : s))
        );
      }

      // Sync generated file artifacts to localStorage and backend /api/artifacts
      const artifactsToSync: Record<string, unknown>[] = [];
      if (data.metadata?.file_artifact && typeof data.metadata.file_artifact === "object") {
        artifactsToSync.push(data.metadata.file_artifact as Record<string, unknown>);
      }
      if (Array.isArray(data.metadata?.artifacts)) {
        for (const art of data.metadata.artifacts) {
          if (art && typeof art === "object" && !artifactsToSync.some((a) => a.id === art.id)) {
            artifactsToSync.push(art as Record<string, unknown>);
          }
        }
      }

      if (artifactsToSync.length > 0) {
        try {
          const rawLocal = localStorage.getItem("swarm_local_artifacts");
          const existingLocal: Record<string, unknown>[] = rawLocal ? JSON.parse(rawLocal) : [];
          const syncedIds = new Set(artifactsToSync.map((a) => String(a.id)));
          const updated = [
            ...artifactsToSync,
            ...existingLocal.filter((a: Record<string, unknown>) => !syncedIds.has(String(a.id))),
          ];
          localStorage.setItem(
            "swarm_local_artifacts",
            JSON.stringify(updated.slice(0, 50))
          );

          // Dispatch to backend /api/artifacts so it persists across DB and memory
          for (const art of artifactsToSync) {
            fetch(`${apiUrl}/api/artifacts`, {
              method: "POST",
              headers,
              body: JSON.stringify({
                ...art,
                session_id: targetSessionId || activeSessionId,
              }),
            }).catch(() => null);
          }
        } catch (e) {
          console.warn("Artifact caching notice:", e);
        }
      }

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
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", `/chat?session=${sessionId}`);
    }
    if (session?.access_token) {
      loadSessionMessages(sessionId, session.access_token);
    }
  };

  // Create new session (Lazy: resets state to clean new chat view without inserting a blank row in sidebar)
  const handleCreateSession = () => {
    setActiveSessionId(null);
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", "/chat");
    }
    setConversation(createInitialState());
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

  // Handle standard user prompt submission (with lazy contextual session creation)
  const handleSend = async (content: string) => {
    if (isLoading) return;

    const trimmed = content.trim();
    if (trimmed.toLowerCase() === "/workflows" || trimmed.toLowerCase() === "/workflow") {
      setIsWorkflowPickerOpen(true);
      return;
    }
    if (trimmed.toLowerCase() === "/clear") {
      handleClearChat();
      return;
    }

    let targetSessionId = activeSessionId;

    // Lazy session creation: create session with contextual auto-titling when the first message is sent
    if (session?.access_token && !targetSessionId) {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/sessions`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({ prompt: content }),
        });
        if (res.ok) {
          const newSession: ChatSession = await res.json();
          setSessions((prev) => [newSession, ...prev]);
          setActiveSessionId(newSession.id);
          targetSessionId = newSession.id;
        }
      } catch (err) {
        console.error("Lazy session creation error:", err);
      }
    }

    const userParent = conversation.currentLeafId;
    const currentArtifacts = [...attachedArtifacts];
    const { newState, newNodeId } = addMessageNode(
      conversation,
      "user",
      content,
      conversation.currentLeafId,
      {
        ...(selectedAgentId ? { target_agent_id: selectedAgentId } : {}),
        ...(currentArtifacts.length > 0 ? { attached_artifacts: currentArtifacts } : {}),
      }
    );

    setConversation(newState);
    setAttachedArtifacts([]);
    const updatedPath = getActivePath(newState.nodes, newNodeId);
    requestSwarmResponse(updatedPath, newNodeId, targetSessionId, userParent, undefined, undefined, currentArtifacts);
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
          body: JSON.stringify({ prompt: `Workflow: ${workflowId}` }),
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
    <div className="flex flex-col h-screen bg-canvas text-ink font-sans overflow-hidden">
      {/* Unified 3-Pillar Navigation Bar */}
      <AppNavigationRail
        currentTab="chat"
        totalTokensUsed={usage?.total_tokens ?? 0}
        onOpenUsage={() => setIsUsageModalOpen(true)}
        userEmail={userEmail}
        onSignOut={handleSignOut}
      />

      <div className="flex flex-1 overflow-hidden relative">
        {/* Unified Persistent Studio Sidebar */}
        <AppUnifiedSidebar
          activePage="chat"
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={handleSelectSession}
          onCreateSession={handleCreateSession}
          onDeleteSession={handleDeleteSession}
          onRenameSession={handleRenameSession}
          isLoadingSessions={isLoadingSessions}
          onCreateWorkflow={() => router.push("/workflows")}
          onCreateAgent={() => router.push("/agents")}
        />

        {/* Main Chat Feed Area */}
        <div className="flex-1 flex flex-col bg-canvas relative overflow-hidden h-full">
          {/* Top Header */}
          <ChatHeader
            agents={agents}
            selectedAgentId={selectedAgentId}
            onSelectAgent={setSelectedAgentId}
            selectedModel={selectedModel}
            onSelectModel={setSelectedModel}
            onClearChat={handleClearChat}
            onExportChat={handleExportChat}
            activePathCount={activePath.length}
            sessionTitle={currentSessionObj?.title}
            totalTokensUsed={usage?.total_tokens}
            onOpenUsage={() => setIsUsageModalOpen(true)}
            onOpenWorkflowPicker={() => setIsWorkflowPickerOpen(true)}
            onInspectAgent={(ag) => {
              setInspectingAgent(ag);
              setIsAgentDetailsOpen(true);
            }}
          />

          {/* Message Feed */}
          <main className="flex-1 p-4 md:p-8 overflow-y-auto space-y-6 scroll-smooth bg-canvas">
            <AnimatePresence initial={false}>
              {isLoadingMessages ? (
                <div className="space-y-5 py-4 max-w-2xl">
                  {/* User message skeleton */}
                  <div className="flex gap-3 justify-end animate-pulse">
                    <div className="h-12 w-64 rounded-lg bg-surface-2 border border-hairline-strong rounded-tr-xs" />
                    <div className="w-7 h-7 rounded-md bg-surface-2 shrink-0 border border-hairline" />
                  </div>
                  {/* Agent message skeleton */}
                  <div className="flex gap-3 animate-pulse">
                    <div className="w-7 h-7 rounded-md bg-surface-1 shrink-0 border border-hairline overflow-hidden flex items-center justify-center">
                      <BrandLogo size={20} />
                    </div>
                    <div className="p-4 rounded-lg bg-surface-1 border border-hairline rounded-tl-xs space-y-2 flex-1 max-w-lg">
                      <div className="h-3.5 w-3/4 rounded bg-surface-2" />
                      <div className="h-3.5 w-5/6 rounded bg-surface-2" />
                      <div className="h-3.5 w-2/3 rounded bg-surface-2" />
                      <div className="h-3.5 w-1/2 rounded bg-surface-2" />
                    </div>
                  </div>
                </div>
              ) : (
                activePath.map((node) => {
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
                })
              )}

              {/* Inspiration Chips when only root greeting exists */}
              {!isLoadingMessages && activePath.length <= 1 && (
                <div className="pt-2 grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl">
                  <button
                    type="button"
                    onClick={() =>
                      handleSend(
                        "Explain the swarm routing architecture: how the orchestrator delegates tasks to specialized agents and executes Python tools."
                      )
                    }
                    className="p-3.5 rounded-lg bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong text-left transition-colors group cursor-pointer"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-medium text-ink group-hover:text-linear-primary transition-colors">
                      <Sparkles size={13} className="text-linear-primary" />
                      <span>Swarm Architecture</span>
                    </div>
                    <p className="text-[11px] text-ink-subtle mt-1 line-clamp-2">
                      Stateless routing, tool definitions, and Supabase execution traces.
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setIsWorkflowPickerOpen(true)}
                    className="p-3.5 rounded-lg bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong text-left transition-colors group cursor-pointer"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-medium text-ink group-hover:text-linear-primary transition-colors">
                      <Workflow size={13} className="text-linear-primary" />
                      <span>Run Workflow</span>
                    </div>
                    <p className="text-[11px] text-ink-subtle mt-1 line-clamp-2">
                      Execute a multi-step DAG pipeline with condition gates and Python blocks.
                    </p>
                  </button>

                  <a
                    href="/agents"
                    className="p-3.5 rounded-lg bg-surface-1 hover:bg-surface-2 border border-hairline hover:border-hairline-strong text-left transition-colors group block cursor-pointer"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-medium text-ink group-hover:text-linear-primary transition-colors">
                      <Bot size={13} className="text-linear-primary" />
                      <span>Agents Studio</span>
                    </div>
                    <p className="text-[11px] text-ink-subtle mt-1 line-clamp-2">
                      Inspect built-in agents, configure system prompts, and test in playground.
                    </p>
                  </a>
                </div>
              )}

              {/* In-flight Processing Bubble */}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 5 }}
                  className="flex gap-3 md:gap-4 flex-row"
                >
                  <div className="w-7 h-7 rounded-md flex items-center justify-center shrink-0 bg-surface-1 border border-hairline text-linear-primary overflow-hidden">
                    <BrandLogo size={20} />
                  </div>
                  <div className="px-4 py-3 rounded-lg bg-surface-1 border border-hairline text-ink rounded-tl-xs flex items-center gap-2.5">
                    <Loader2 size={14} className="animate-spin text-linear-primary" />
                    <span className="text-xs font-medium text-ink-subtle font-mono">
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
            onSend={(content) => handleSend(content)}
            isLoading={isLoading}
            onStop={handleStop}
            onOpenWorkflowPicker={() => setIsWorkflowPickerOpen(true)}
            onClearChat={handleClearChat}
            onOpenArtifactSelector={() => setIsArtifactSelectorOpen(true)}
            attachedArtifacts={attachedArtifacts}
            onRemoveArtifact={handleRemoveArtifact}
            onUploadFile={handleUploadChatFile}
          />
        </div>
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

      {/* Artifact Selector Modal */}
      <ArtifactSelectorModal
        isOpen={isArtifactSelectorOpen}
        onClose={() => setIsArtifactSelectorOpen(false)}
        onSelectArtifacts={handleSelectArtifacts}
        alreadyAttachedIds={attachedArtifacts.map((a) => a.id)}
      />
    </div>
  );
}

export default function Chat() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen w-screen items-center justify-center bg-canvas">
          <Loader2 className="h-8 w-8 animate-spin text-linear-primary" />
        </div>
      }
    >
      <ChatContent />
    </Suspense>
  );
}
