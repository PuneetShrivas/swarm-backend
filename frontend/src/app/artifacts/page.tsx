"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import AppNavigationRail from "@/app/components/AppNavigationRail";
import AppUnifiedSidebar from "@/components/AppUnifiedSidebar";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { supabase } from "@/lib/supabase";
import {
  FolderArchive,
  Search,
  Download,
  Copy,
  Check,
  Trash2,
  FileCode,
  FileText,
  FileSpreadsheet,
  FileJson,
  Presentation,
  Plus,
  RefreshCw,
  X,
  Upload,
  MessageSquare,
  FileUp,
} from "lucide-react";

export interface Artifact {
  id: string;
  name: string;
  filename: string;
  type: string;
  content: string;
  size_bytes?: number;
  created_at?: string;
  origin_agent?: string;
  source_type?: string;
  source_title?: string;
  downloadable?: boolean;
  is_base64?: boolean;
  mime_type?: string;
  encoding?: string;
}

export default function ArtifactsStudioPage() {
  const router = useRouter();
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [userEmail, setUserEmail] = useState<string | null>(null);

  // Preview modal state
  const [previewArtifact, setPreviewArtifact] = useState<Artifact | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Upload modal state
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Fetch artifacts from FastAPI backend merged with client localStorage cache
  const fetchArtifacts = useCallback(async () => {
    setIsLoading(true);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (session?.user?.email) {
        setUserEmail(session.user.email);
      }

      // 1. Read from localStorage for instant offline/guest reflection
      let localList: Artifact[] = [];
      try {
        const raw = localStorage.getItem("swarm_local_artifacts");
        if (raw) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed)) {
            localList = parsed;
          }
        }
      } catch {
        // Ignore local parse errors
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers: Record<string, string> = {};
      if (session?.access_token) {
        headers["Authorization"] = `Bearer ${session.access_token}`;
      }

      const res = await fetch(`${apiUrl}/api/artifacts`, { headers }).catch(() => null);
      let backendList: Artifact[] = [];
      if (res && res.ok) {
        backendList = await res.json();
      }

      // Merge backend and local list, deduplicating by unique id
      const combinedMap = new Map<string, Artifact>();
      for (const art of localList) {
        if (art && art.id) combinedMap.set(art.id, art);
      }
      for (const art of backendList) {
        if (art && art.id) combinedMap.set(art.id, art);
      }

      const merged = Array.from(combinedMap.values()).sort((a, b) => {
        const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return dateB - dateA;
      });

      setArtifacts(merged);
    } catch (err) {
      console.warn("Failed to fetch artifacts:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchArtifacts();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(() => {
      fetchArtifacts();
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [fetchArtifacts]);

  // Handle Download File with Binary Base64 decoding support
  const handleDownload = (art: Artifact, e?: React.MouseEvent) => {
    e?.stopPropagation();
    try {
      const fname = art.filename || art.name || "download.txt";
      const ext = (fname.split(".").pop() || art.type || "txt").toLowerCase();
      const isBinary =
        Boolean(art.is_base64) ||
        art.encoding === "base64" ||
        ["pdf", "pptx", "docx", "xlsx", "zip"].includes(ext);

      const mime =
        art.mime_type ||
        (ext === "pdf"
          ? "application/pdf"
          : ext === "pptx"
          ? "application/vnd.openxmlformats-officedocument.presentationml.presentation"
          : ext === "docx"
          ? "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          : ext === "xlsx"
          ? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          : ext === "json"
          ? "application/json"
          : ext === "csv"
          ? "text/csv"
          : "text/plain;charset=utf-8");

      let blob: Blob;
      if (isBinary) {
        const cleanB64 = art.content.replace(/^data:[^;]+;base64,/, "").trim();
        const byteChars = atob(cleanB64);
        const byteNumbers = new Uint8Array(byteChars.length);
        for (let i = 0; i < byteChars.length; i++) {
          byteNumbers[i] = byteChars.charCodeAt(i);
        }
        blob = new Blob([byteNumbers], { type: mime });
      } else {
        blob = new Blob([art.content], { type: mime });
      }

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fname;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download artifact:", err);
    }
  };

  // Handle Copy Content
  const handleCopy = (art: Artifact, e?: React.MouseEvent) => {
    e?.stopPropagation();
    const isBinary =
      Boolean(art.is_base64) ||
      art.encoding === "base64" ||
      ["pdf", "pptx", "docx", "xlsx"].includes((art.type || "").toLowerCase());
    if (isBinary) {
      navigator.clipboard.writeText(`[Binary Document: ${art.filename || art.name} (${art.size_bytes || 0} bytes)]`);
    } else {
      navigator.clipboard.writeText(art.content);
    }
    setCopiedId(art.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Handle Delete Artifact
  const handleDelete = async (artId: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    if (!window.confirm("Delete this artifact permanently?")) return;
    try {
      // 1. Remove from local storage
      try {
        const raw = localStorage.getItem("swarm_local_artifacts");
        if (raw) {
          const list: Artifact[] = JSON.parse(raw);
          localStorage.setItem(
            "swarm_local_artifacts",
            JSON.stringify(list.filter((a) => a.id !== artId))
          );
        }
      } catch {
        // Ignore storage error
      }

      // 2. Remove from state
      setArtifacts((prev) => prev.filter((a) => a.id !== artId));
      if (previewArtifact?.id === artId) {
        setPreviewArtifact(null);
      }

      // 3. Remove from backend
      const {
        data: { session },
      } = await supabase.auth.getSession();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers: Record<string, string> = {};
      if (session?.access_token) {
        headers["Authorization"] = `Bearer ${session.access_token}`;
      }
      await fetch(`${apiUrl}/api/artifacts/${artId}`, {
        method: "DELETE",
        headers,
      }).catch(() => null);
    } catch (err) {
      console.error("Failed to delete artifact:", err);
    }
  };

  // Handle Invoke in Chat
  const handleInvokeInChat = (art: Artifact, e?: React.MouseEvent) => {
    e?.stopPropagation();
    try {
      localStorage.setItem("swarm_invoked_artifact", JSON.stringify(art));
    } catch {
      // Ignore storage error
    }
    router.push(`/chat?artifact_id=${encodeURIComponent(art.id)}`);
  };

  // Handle Upload Artifact Submission
  const handleUploadArtifact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setIsUploading(true);
    setUploadError(null);

    try {
      const ext = (uploadFile.name.split(".").pop() || "txt").toLowerCase();
      const isBinary = ["pdf", "docx", "pptx", "xlsx", "zip"].includes(ext);

      let content = "";
      if (isBinary) {
        const b64DataUrl = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve((reader.result as string) || "");
          reader.onerror = reject;
          reader.readAsDataURL(uploadFile);
        });
        content = b64DataUrl.split(",")[1] || "";
      } else {
        content = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve((reader.result as string) || "");
          reader.onerror = reject;
          reader.readAsText(uploadFile);
        });
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const {
        data: { session },
      } = await supabase.auth.getSession();
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (session?.access_token) {
        headers["Authorization"] = `Bearer ${session.access_token}`;
      }

      const payload: Artifact = {
        id: `art-up-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`,
        name: uploadFile.name,
        filename: uploadFile.name,
        type: ext,
        content,
        size_bytes: uploadFile.size,
        created_at: new Date().toISOString(),
        origin_agent: "user_upload",
        source_type: "upload",
        source_title: "User Upload",
        downloadable: true,
        is_base64: isBinary,
        encoding: isBinary ? "base64" : "utf-8",
      };

      const res = await fetch(`${apiUrl}/api/artifacts`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });

      const saved: Artifact = res.ok ? await res.json() : payload;

      try {
        const raw = localStorage.getItem("swarm_local_artifacts");
        const list = raw ? JSON.parse(raw) : [];
        localStorage.setItem("swarm_local_artifacts", JSON.stringify([saved, ...list].slice(0, 50)));
      } catch {
        // Ignore storage error
      }

      setArtifacts((prev) => [saved, ...prev.filter((a) => a.id !== saved.id)]);
      setIsUploadModalOpen(false);
      setUploadFile(null);
    } catch (err: unknown) {
      setUploadError((err as Error).message || "Failed to upload artifact.");
    } finally {
      setIsUploading(false);
    }
  };

  // Filtered artifacts
  const filteredArtifacts = useMemo(() => {
    return artifacts.filter((art) => {
      const matchesSearch =
        (art.name || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (art.filename || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (art.type || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (art.origin_agent || "").toLowerCase().includes(searchQuery.toLowerCase());

      const matchesType =
        typeFilter === "all" ||
        (art.type || "").toLowerCase() === typeFilter.toLowerCase();

      return matchesSearch && matchesType;
    });
  }, [artifacts, searchQuery, typeFilter]);

  const getFileIcon = (type: string) => {
    const t = type.toLowerCase();
    if (t === "pdf") {
      return <FileText size={18} className="text-red-400" />;
    }
    if (t === "pptx" || t === "ppt") {
      return <Presentation size={18} className="text-orange-400" />;
    }
    if (t === "docx" || t === "doc") {
      return <FileText size={18} className="text-blue-400" />;
    }
    if (t === "xlsx" || t === "xls" || t === "csv" || t === "tsv") {
      return <FileSpreadsheet size={18} className="text-emerald-400" />;
    }
    if (t === "py" || t === "python" || t === "js" || t === "ts" || t === "sql") {
      return <FileCode size={18} className="text-purple-400" />;
    }
    if (t === "json" || t === "yaml" || t === "yml") {
      return <FileJson size={18} className="text-amber-400" />;
    }
    return <FileText size={18} className="text-blue-400" />;
  };

  return (
    <div className="flex flex-col h-screen bg-canvas text-ink font-sans overflow-hidden selection:bg-linear-primary/25 selection:text-ink">
      {/* 1. Global Navigation Rail */}
      <AppNavigationRail
        currentTab="artifacts"
        userEmail={userEmail}
        onSignOut={async () => {
          await supabase.auth.signOut();
          setUserEmail(null);
        }}
      />

      <div className="flex flex-1 overflow-hidden relative">
        {/* Unified Persistent Studio Sidebar */}
        <AppUnifiedSidebar activePage="artifacts" />

        <div className="flex-1 flex flex-col bg-canvas overflow-y-auto h-full">
          {/* Header Banner */}
          <div className="border-b border-hairline bg-surface-1/40 px-4 md:px-8 py-5">
            <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold tracking-tight text-ink flex items-center gap-2">
                    <FolderArchive size={20} className="text-linear-primary" />
                    <span>Artifacts Studio</span>
                  </h1>
                  <span className="text-xs font-mono px-2 py-0.5 rounded-pill bg-surface-2 border border-hairline text-ink-subtle">
                    {artifacts.length} Files
                  </span>
                </div>
                <p className="text-xs text-ink-subtle mt-1 leading-relaxed">
                  Inspect, preview, download, and manage code scripts, analytical datasets, and structured documents generated by autonomous agents and pipelines.
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => setIsUploadModalOpen(true)}
                  className="px-3.5 py-1.5 text-xs font-medium text-ink bg-surface-2 hover:bg-surface-3 border border-hairline rounded-md transition-colors flex items-center gap-1.5 shadow-xs"
                  title="Upload PDF, DOCX, PPTX, XLSX, CSV, JSON, Markdown, or Code artifacts"
                >
                  <Upload size={13} className="text-linear-primary" />
                  <span>Upload Artifact</span>
                </button>
                <button
                  type="button"
                  onClick={() => router.push("/chat")}
                  className="px-3.5 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors flex items-center gap-1.5 shadow-xs"
                >
                  <Plus size={13} />
                  <span>Generate New File</span>
                </button>
                <button
                  type="button"
                  onClick={fetchArtifacts}
                  disabled={isLoading}
                  className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 border border-hairline transition-colors"
                  title="Refresh Artifacts"
                >
                  <RefreshCw size={13} className={isLoading ? "animate-spin" : ""} />
                </button>
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <main className="flex-1 p-4 md:p-8 max-w-6xl w-full mx-auto space-y-6">
            {/* Search & Type Filter Bar */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-2 rounded-lg bg-surface-1 border border-hairline">
              <div className="relative flex-1">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-tertiary" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter artifacts by filename, extension, or agent..."
                  className="w-full text-xs bg-transparent pl-8 pr-3 py-1.5 text-ink placeholder:text-ink-tertiary focus:outline-none"
                />
              </div>

              <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
                {["all", "pdf", "docx", "pptx", "xlsx", "csv", "json", "py", "md"].map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setTypeFilter(t)}
                    className={`px-2.5 py-1 text-[11px] font-mono rounded-md border uppercase transition-colors shrink-0 ${
                      typeFilter === t
                        ? "bg-surface-2 text-ink border-hairline-strong font-semibold"
                        : "text-ink-subtle hover:text-ink border-transparent"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            {/* Artifacts Grid */}
            {isLoading && artifacts.length === 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div
                    key={i}
                    className="p-5 rounded-lg bg-surface-1 border border-hairline animate-pulse flex flex-col justify-between h-44"
                  >
                    <div className="space-y-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-md bg-surface-2 shrink-0" />
                        <div className="h-4 w-36 rounded bg-surface-2" />
                      </div>
                      <div className="h-3 w-4/5 rounded bg-surface-2" />
                    </div>
                    <div className="h-6 w-24 rounded bg-surface-2" />
                  </div>
                ))}
              </div>
            ) : filteredArtifacts.length === 0 ? (
              <div className="p-12 text-center rounded-lg border border-dashed border-hairline bg-surface-1/40 space-y-3 max-w-md mx-auto">
                <FolderArchive size={32} className="mx-auto text-ink-tertiary" />
                <h3 className="text-sm font-semibold text-ink">No artifacts found</h3>
                <p className="text-xs text-ink-subtle">
                  {searchQuery
                    ? `No files match '${searchQuery}'. Try clearing your filter.`
                    : "No files generated yet. Ask the File & Document Architect in chat or run a workflow pipeline to create files."}
                </p>
                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => router.push("/chat")}
                    className="px-3.5 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors"
                  >
                    Go to Chat to Create File
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredArtifacts.map((art) => {
                  const fname = art.filename || art.name || "artifact.txt";
                  const sizeKb = art.size_bytes
                    ? (art.size_bytes / 1024).toFixed(1)
                    : (art.content.length / 1024).toFixed(1);

                  return (
                    <SpotlightCard
                      key={art.id}
                      onClick={() => setPreviewArtifact(art)}
                      className="p-4 flex flex-col justify-between cursor-pointer group select-none h-48"
                    >
                      <div>
                        {/* Card Header */}
                        <div className="flex items-start justify-between gap-2 mb-2 pb-2 border-b border-hairline">
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="w-8 h-8 rounded-md bg-surface-2 border border-hairline flex items-center justify-center shrink-0">
                              {getFileIcon(art.type || fname.split(".").pop() || "txt")}
                            </div>
                            <div className="min-w-0">
                              <h3 className="text-xs font-semibold text-ink truncate group-hover:text-linear-primary transition-colors">
                                {fname}
                              </h3>
                              <p className="text-[10px] text-ink-subtle font-mono truncate">
                                {sizeKb} KB · {art.origin_agent || "Swarm"}
                              </p>
                            </div>
                          </div>

                          <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-surface-2 text-ink-subtle border border-hairline shrink-0">
                            {art.type || "file"}
                          </span>
                        </div>

                        {/* Snippet Preview */}
                        {Boolean(art.is_base64) || ["pdf", "docx", "pptx", "xlsx"].includes((art.type || "").toLowerCase()) ? (
                          <div className="text-[11px] font-mono text-ink-subtle bg-canvas/60 p-2.5 rounded border border-hairline/60 flex items-center gap-2">
                            {getFileIcon(art.type || fname.split(".").pop() || "txt")}
                            <span>Binary {art.type.toUpperCase()} Document ({sizeKb} KB)</span>
                          </div>
                        ) : (
                          <p className="text-[11px] font-mono text-ink-subtle line-clamp-3 leading-relaxed bg-canvas/60 p-2 rounded border border-hairline/60">
                            {art.content.slice(0, 160)}
                          </p>
                        )}
                      </div>

                      {/* Card Actions Footer */}
                      <div
                        className="pt-2 border-t border-hairline flex items-center justify-between"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={(e) => handleDownload(art, e)}
                            className="px-2.5 py-1 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded inline-flex items-center gap-1.5 transition-transform hover:scale-[1.02] shadow-xs"
                          >
                            <Download size={11} />
                            <span>Download</span>
                          </button>
                          <button
                            type="button"
                            onClick={(e) => handleInvokeInChat(art, e)}
                            className="px-2 py-1 text-xs font-medium text-ink bg-surface-2 hover:bg-surface-3 rounded inline-flex items-center gap-1 transition-colors border border-hairline"
                            title="Invoke in Chat for grounded answers"
                          >
                            <MessageSquare size={11} className="text-linear-primary" />
                            <span>Chat</span>
                          </button>
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={(e) => handleCopy(art, e)}
                            className="p-1 rounded text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors border border-hairline"
                            title="Copy file content"
                          >
                            {copiedId === art.id ? (
                              <Check size={11} className="text-semantic-success" />
                            ) : (
                              <Copy size={11} />
                            )}
                          </button>
                          <button
                            type="button"
                            onClick={(e) => handleDelete(art.id, e)}
                            className="p-1 rounded text-ink-subtle hover:text-red-400 hover:bg-surface-2 transition-colors border border-hairline"
                            title="Delete artifact"
                          >
                            <Trash2 size={11} />
                          </button>
                        </div>
                      </div>
                    </SpotlightCard>
                  );
                })}
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Preview File Modal */}
      {previewArtifact && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in font-sans">
          <div className="bg-surface-1 border border-hairline rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-card overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-hairline flex items-center justify-between bg-surface-2/40">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-md bg-surface-2 border border-hairline flex items-center justify-center shrink-0">
                  {getFileIcon(previewArtifact.type || previewArtifact.filename.split(".").pop() || "txt")}
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold text-ink truncate">
                    {previewArtifact.filename || previewArtifact.name}
                  </h3>
                  <p className="text-[10px] text-ink-subtle font-mono">
                    {previewArtifact.origin_agent || "file_creator"} · {previewArtifact.size_bytes || previewArtifact.content.length} bytes
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleInvokeInChat(previewArtifact)}
                  className="px-3 py-1.5 text-xs font-medium text-ink bg-surface-2 hover:bg-surface-3 border border-hairline rounded-md transition-all inline-flex items-center gap-1.5 shadow-xs"
                  title="Invoke in Chat with grounded context"
                >
                  <MessageSquare size={12} className="text-linear-primary" />
                  <span>Invoke in Chat</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleDownload(previewArtifact)}
                  className="px-3 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-all inline-flex items-center gap-1.5 shadow-xs"
                >
                  <Download size={12} />
                  <span>Download</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleCopy(previewArtifact)}
                  className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 border border-hairline transition-colors"
                  title="Copy content"
                >
                  {copiedId === previewArtifact.id ? (
                    <Check size={13} className="text-semantic-success" />
                  ) : (
                    <Copy size={13} />
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewArtifact(null)}
                  className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 border border-hairline transition-colors"
                  title="Close"
                >
                  <X size={14} />
                </button>
              </div>
            </div>

            {/* Modal Body / Preformatted Code Viewer or Binary Card */}
            <div className="p-4 flex-1 overflow-y-auto bg-canvas">
              {Boolean(previewArtifact.is_base64) || ["pdf", "docx", "pptx", "xlsx"].includes((previewArtifact.type || "").toLowerCase()) ? (
                <div className="p-8 text-center space-y-4 rounded-lg bg-surface-1 border border-hairline my-4 max-w-md mx-auto">
                  <div className="w-14 h-14 mx-auto rounded-xl bg-surface-2 border border-hairline flex items-center justify-center">
                    {getFileIcon(previewArtifact.type || previewArtifact.filename.split(".").pop() || "txt")}
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-sm font-semibold text-ink">{previewArtifact.filename || previewArtifact.name}</h4>
                    <p className="text-xs text-ink-subtle">
                      {previewArtifact.type.toUpperCase()} Document &middot; {((previewArtifact.size_bytes || previewArtifact.content.length) / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <p className="text-xs text-ink-tertiary leading-relaxed">
                    This binary document has been synthesized by the Swarm Document Architect. Click Download to open natively in your application.
                  </p>
                  <button
                    type="button"
                    onClick={() => handleDownload(previewArtifact)}
                    className="px-4 py-2 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-all inline-flex items-center gap-2 shadow-xs cursor-pointer"
                  >
                    <Download size={13} />
                    <span>Download {previewArtifact.filename || "File"}</span>
                  </button>
                </div>
              ) : (
                <pre className="font-mono text-xs text-ink whitespace-pre-wrap break-all leading-relaxed p-3 rounded-lg bg-surface-1 border border-hairline">
                  {previewArtifact.content}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Upload Artifact Modal */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in font-sans">
          <div className="bg-surface-1 border border-hairline rounded-xl w-full max-w-lg shadow-card overflow-hidden">
            <div className="p-4 border-b border-hairline flex items-center justify-between bg-surface-2/40">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-md bg-surface-2 border border-hairline flex items-center justify-center text-linear-primary">
                  <Upload size={16} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-ink">Upload Artifact</h3>
                  <p className="text-[11px] text-ink-subtle">
                    Upload documents to index into RAG and use across Swarm agents & workflows
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setIsUploadModalOpen(false);
                  setUploadFile(null);
                  setUploadError(null);
                }}
                className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 border border-hairline transition-colors"
              >
                <X size={14} />
              </button>
            </div>

            <form onSubmit={handleUploadArtifact} className="p-5 space-y-4">
              {uploadError && (
                <div className="p-3 text-xs rounded-md bg-red-500/10 border border-red-500/30 text-red-400">
                  {uploadError}
                </div>
              )}

              {/* Drag and Drop Zone */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    setUploadFile(e.dataTransfer.files[0]);
                  }
                }}
                className={`border-2 border-dashed rounded-xl p-6 text-center transition-all ${
                  uploadFile
                    ? "border-linear-primary bg-linear-primary/5"
                    : "border-hairline hover:border-hairline-strong bg-canvas/40"
                }`}
              >
                {uploadFile ? (
                  <div className="space-y-2">
                    <div className="w-10 h-10 mx-auto rounded-lg bg-surface-2 border border-hairline flex items-center justify-center">
                      {getFileIcon(uploadFile.name.split(".").pop() || "txt")}
                    </div>
                    <p className="text-xs font-semibold text-ink truncate max-w-xs mx-auto">
                      {uploadFile.name}
                    </p>
                    <p className="text-[10px] text-ink-subtle font-mono">
                      {(uploadFile.size / 1024).toFixed(1)} KB &middot; {uploadFile.name.split(".").pop()?.toUpperCase() || "FILE"}
                    </p>
                    <button
                      type="button"
                      onClick={() => setUploadFile(null)}
                      className="text-[11px] text-red-400 hover:underline pt-1"
                    >
                      Remove file
                    </button>
                  </div>
                ) : (
                  <label className="cursor-pointer block space-y-2">
                    <FileUp size={28} className="mx-auto text-ink-tertiary" />
                    <div>
                      <span className="text-xs font-medium text-linear-primary hover:underline">
                        Choose a file
                      </span>
                      <span className="text-xs text-ink-subtle"> or drag and drop</span>
                    </div>
                    <p className="text-[10px] text-ink-tertiary">
                      PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), CSV, JSON, Markdown, Python, TXT (up to 20MB)
                    </p>
                    <input
                      type="file"
                      className="hidden"
                      accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.csv,.json,.py,.md,.txt,.html"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          setUploadFile(e.target.files[0]);
                        }
                      }}
                    />
                  </label>
                )}
              </div>

              {/* Information pill */}
              <div className="text-[11px] text-ink-tertiary bg-surface-2/40 p-2.5 rounded-lg border border-hairline leading-relaxed">
                <span className="font-semibold text-ink">Automatic RAG Integration:</span> This document will be parsed, segmented with sliding-window chunking, and indexed into the hybrid BM25 knowledge engine for instant context retrieval by Swarm agents.
              </div>

              {/* Actions Footer */}
              <div className="pt-2 flex items-center justify-end gap-2 border-t border-hairline">
                <button
                  type="button"
                  onClick={() => {
                    setIsUploadModalOpen(false);
                    setUploadFile(null);
                    setUploadError(null);
                  }}
                  className="px-3 py-1.5 text-xs text-ink-subtle hover:text-ink hover:bg-surface-2 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!uploadFile || isUploading}
                  className="px-4 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-xs inline-flex items-center gap-1.5"
                >
                  {isUploading ? (
                    <>
                      <RefreshCw size={12} className="animate-spin" />
                      <span>Indexing & Uploading...</span>
                    </>
                  ) : (
                    <>
                      <Upload size={12} />
                      <span>Upload & Index</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
