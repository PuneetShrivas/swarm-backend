"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  FolderArchive,
  X,
  Search,
  Check,
  FileCode,
  FileText,
  FileSpreadsheet,
  FileJson,
  Presentation,
  Paperclip,
  Loader2,
} from "lucide-react";
import { getAuthHeaders } from "@/lib/supabase";

export interface ArtifactItem {
  id: string;
  name: string;
  filename: string;
  type: string;
  content: string;
  size_bytes?: number;
  created_at?: string;
  origin_agent?: string;
  source_type?: string;
  is_base64?: boolean;
}

interface ArtifactSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectArtifacts: (artifacts: ArtifactItem[]) => void;
  alreadyAttachedIds?: string[];
}

export default function ArtifactSelectorModal({
  isOpen,
  onClose,
  onSelectArtifacts,
  alreadyAttachedIds = [],
}: ArtifactSelectorModalProps) {
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set(alreadyAttachedIds));
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setSelectedIds(new Set(alreadyAttachedIds));

    const loadArtifacts = async () => {
      setIsLoading(true);
      try {
        // Read from local storage
        let localList: ArtifactItem[] = [];
        try {
          const raw = localStorage.getItem("swarm_local_artifacts");
          if (raw) localList = JSON.parse(raw);
        } catch {
          // Ignore
        }

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const authHeaders = await getAuthHeaders();
        const res = await fetch(`${apiUrl}/api/artifacts`, {
          headers: authHeaders,
        }).catch(() => null);

        let backendList: ArtifactItem[] = [];
        if (res && res.ok) {
          backendList = await res.json();
        }

        const map = new Map<string, ArtifactItem>();
        for (const art of localList) {
          if (art?.id) map.set(art.id, art);
        }
        for (const art of backendList) {
          if (art?.id) map.set(art.id, art);
        }

        const combined = Array.from(map.values()).sort((a, b) => {
          const tA = a.created_at ? new Date(a.created_at).getTime() : 0;
          const tB = b.created_at ? new Date(b.created_at).getTime() : 0;
          return tB - tA;
        });

        setArtifacts(combined);
      } catch (err) {
        console.error("Failed to load artifacts for selector:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadArtifacts();
  }, [isOpen, alreadyAttachedIds]);

  const filteredArtifacts = useMemo(() => {
    return artifacts.filter((art) => {
      const fname = (art.filename || art.name || "").toLowerCase();
      const artType = (art.type || fname.split(".").pop() || "").toLowerCase();
      const matchesSearch =
        search === "" ||
        fname.includes(search.toLowerCase()) ||
        artType.includes(search.toLowerCase()) ||
        (art.origin_agent || "").toLowerCase().includes(search.toLowerCase());

      const matchesType = typeFilter === "all" || artType === typeFilter;
      return matchesSearch && matchesType;
    });
  }, [artifacts, search, typeFilter]);

  const toggleSelect = (artId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(artId)) {
        next.delete(artId);
      } else {
        next.add(artId);
      }
      return next;
    });
  };

  const handleConfirm = () => {
    const selected = artifacts.filter((a) => selectedIds.has(a.id));
    onSelectArtifacts(selected);
    onClose();
  };

  const getFileIcon = (type: string) => {
    const t = type.toLowerCase();
    if (t === "pdf") return <FileText size={14} className="text-red-400" />;
    if (t === "pptx" || t === "ppt") return <Presentation size={14} className="text-orange-400" />;
    if (t === "xlsx" || t === "xls" || t === "csv") return <FileSpreadsheet size={14} className="text-emerald-400" />;
    if (t === "docx" || t === "doc") return <FileText size={14} className="text-blue-400" />;
    if (t === "json") return <FileJson size={14} className="text-amber-400" />;
    if (["py", "js", "ts", "html", "css"].includes(t)) return <FileCode size={14} className="text-linear-primary" />;
    return <FileText size={14} className="text-ink-subtle" />;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-surface-1 border border-hairline rounded-xl w-full max-w-xl max-h-[85vh] flex flex-col shadow-card overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-hairline flex items-center justify-between bg-surface-2/40">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-surface-2 border border-hairline flex items-center justify-center text-linear-primary">
              <FolderArchive size={16} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-ink">Attach Artifacts to Chat</h3>
              <p className="text-[11px] text-ink-subtle">
                Select documents from your studio library to ground agent responses
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 border border-hairline transition-colors"
          >
            <X size={14} />
          </button>
        </div>

        {/* Search & Filter Bar */}
        <div className="p-3 border-b border-hairline bg-surface-1 space-y-2.5">
          <div className="relative">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-tertiary" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search artifacts by name, extension, agent..."
              className="w-full text-xs bg-canvas/60 border border-hairline rounded-md pl-8 pr-3 py-1.5 text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-linear-primary"
            />
          </div>

          <div className="flex items-center gap-1 overflow-x-auto no-scrollbar pb-0.5">
            {["all", "pdf", "docx", "pptx", "xlsx", "csv", "json", "py", "md"].map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTypeFilter(t)}
                className={`px-2 py-0.5 text-[10px] font-mono rounded border uppercase transition-colors shrink-0 ${
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

        {/* Artifacts List */}
        <div className="p-3 flex-1 overflow-y-auto space-y-1.5 max-h-[50vh]">
          {isLoading && artifacts.length === 0 ? (
            <div className="p-8 text-center text-xs text-ink-subtle flex items-center justify-center gap-2">
              <Loader2 size={14} className="animate-spin text-linear-primary" />
              <span>Loading artifacts...</span>
            </div>
          ) : filteredArtifacts.length === 0 ? (
            <div className="p-8 text-center space-y-2">
              <FolderArchive size={28} className="mx-auto text-ink-tertiary" />
              <p className="text-xs text-ink-subtle">No artifacts match your filter.</p>
            </div>
          ) : (
            filteredArtifacts.map((art) => {
              const fname = art.filename || art.name || "artifact.txt";
              const ext = (art.type || fname.split(".").pop() || "txt").toLowerCase();
              const isChecked = selectedIds.has(art.id);
              const sizeKb = art.size_bytes
                ? (art.size_bytes / 1024).toFixed(1)
                : ((art.content?.length || 0) / 1024).toFixed(1);

              return (
                <div
                  key={art.id}
                  onClick={() => toggleSelect(art.id)}
                  className={`p-2.5 rounded-lg border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                    isChecked
                      ? "bg-linear-primary/10 border-linear-primary/60"
                      : "bg-surface-1 hover:bg-surface-2 border-hairline"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div
                      className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors ${
                        isChecked
                          ? "bg-linear-primary border-linear-primary text-white"
                          : "border-hairline-strong bg-canvas"
                      }`}
                    >
                      {isChecked && <Check size={10} strokeWidth={3} />}
                    </div>

                    <div className="w-7 h-7 rounded bg-surface-2 border border-hairline flex items-center justify-center shrink-0">
                      {getFileIcon(ext)}
                    </div>

                    <div className="min-w-0">
                      <p className="text-xs font-medium text-ink truncate">{fname}</p>
                      <p className="text-[10px] text-ink-subtle font-mono">
                        {ext.toUpperCase()} &middot; {sizeKb} KB &middot; {art.origin_agent || "User Upload"}
                      </p>
                    </div>
                  </div>

                  <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-surface-2 border border-hairline text-ink-subtle shrink-0">
                    {ext}
                  </span>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-hairline bg-surface-2/40 flex items-center justify-between">
          <span className="text-xs text-ink-subtle font-mono">
            {selectedIds.size} artifact(s) selected
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-ink-subtle hover:text-ink rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              className="px-3.5 py-1.5 text-xs font-medium text-white bg-linear-primary hover:bg-linear-hover rounded-md transition-colors shadow-xs inline-flex items-center gap-1.5"
            >
              <Paperclip size={12} />
              <span>Attach Selected ({selectedIds.size})</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
