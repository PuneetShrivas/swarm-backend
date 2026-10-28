"use client";

import React, { useState } from "react";
import { KnowledgeFile } from "../types";
import { getAuthHeaders } from "@/lib/supabase";
import {
  FileText,
  Upload,
  Trash2,
  Eye,
  Plus,
  X,
  FileCheck,
  FolderOpen,
} from "lucide-react";

interface KnowledgeBaseManagerProps {
  workflowId: string;
  files: KnowledgeFile[];
  onRefreshFiles: () => void;
  readOnly?: boolean;
}

export default function KnowledgeBaseManager({
  workflowId,
  files,
  onRefreshFiles,
  readOnly = false,
}: KnowledgeBaseManagerProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [previewFile, setPreviewFile] = useState<KnowledgeFile | null>(null);

  // Manual paste / text file upload state
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [fileName, setFileName] = useState("document.md");
  const [contentText, setContentText] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (readOnly || !e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setIsUploading(true);
    setErrorMsg(null);

    const reader = new FileReader();
    reader.onload = async (event) => {
      const text = (event.target?.result as string) || "";
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      try {
        const authHeaders = await getAuthHeaders();
        const res = await fetch(`${apiUrl}/api/workflows/${workflowId}/knowledge/upload`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...authHeaders,
          },
          body: JSON.stringify({
            file_name: file.name,
            content_text: text,
            file_type: file.type || "text/plain",
          }),
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Failed to upload document.");
        }

        onRefreshFiles();
      } catch (err: unknown) {
        setErrorMsg((err as Error).message || "Upload error.");
      } finally {
        setIsUploading(false);
      }
    };
    reader.readAsText(file);
  };

  const handleCreateTextFile = async () => {
    if (readOnly || !fileName || !contentText) return;
    setIsUploading(true);
    setErrorMsg(null);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      const authHeaders = await getAuthHeaders();
      const res = await fetch(`${apiUrl}/api/workflows/${workflowId}/knowledge/upload`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({
          file_name: fileName,
          content_text: contentText,
          file_type: "text/markdown",
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Upload error.");
      }

      setShowPasteModal(false);
      setContentText("");
      setFileName("notes.md");
      onRefreshFiles();
    } catch (err: unknown) {
      setErrorMsg((err as Error).message || "Save document error.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (fileId: string) => {
    if (readOnly || !confirm("Are you sure you want to remove this knowledge document?")) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const authHeaders = await getAuthHeaders();
      await fetch(`${apiUrl}/api/workflows/${workflowId}/knowledge/${fileId}`, {
        method: "DELETE",
        headers: authHeaders,
      });
      onRefreshFiles();
    } catch (err) {
      console.error("Delete knowledge file error:", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Upload Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <FolderOpen size={16} className="text-primary" /> Workflow Knowledge Base
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Documents attached here are automatically ingested and injected into agent instructions.
          </p>
        </div>

        {!readOnly && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowPasteModal(true)}
              className="px-3 py-1.5 text-xs font-medium border border-border bg-card hover:bg-muted text-foreground rounded-xl transition flex items-center gap-1.5"
            >
              <Plus size={13} /> Add Text Doc
            </button>
            <label className="px-3.5 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-xl hover:opacity-90 transition flex items-center gap-1.5 cursor-pointer shadow-subtle">
              <Upload size={13} /> Upload File (.txt, .md, .csv)
              <input
                type="file"
                className="hidden"
                accept=".txt,.md,.markdown,.csv,.json,.py,.yaml,.yml"
                onChange={handleFileUpload}
                disabled={isUploading}
              />
            </label>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs">
          {errorMsg}
        </div>
      )}

      {/* Files Grid */}
      {files.length === 0 ? (
        <div className="p-12 text-center border-2 border-dashed border-border/80 rounded-2xl bg-card/40">
          <FileText className="w-10 h-10 text-muted-foreground opacity-40 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-foreground">No knowledge files attached</h4>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto mt-1 mb-4">
            Upload policies, research papers, schemas, or competitor notes to give agents deep domain context.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {files.map((file) => (
            <div
              key={file.id}
              className="p-4 rounded-xl bg-card border border-border/80 shadow-subtle hover:border-primary/30 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileCheck size={18} className="text-primary shrink-0" />
                    <span className="text-xs font-semibold text-foreground truncate">
                      {file.file_name}
                    </span>
                  </div>
                  <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded shrink-0">
                    {Math.round(file.file_size / 1024) || 1} KB
                  </span>
                </div>
                <p className="text-[11px] font-mono text-muted-foreground line-clamp-3 mt-2 bg-background/50 p-2 rounded-lg border border-border/40">
                  {file.content_text.slice(0, 150)}...
                </p>
              </div>

              <div className="flex items-center justify-end gap-1 mt-3 pt-2 border-t border-border/50">
                <button
                  onClick={() => setPreviewFile(file)}
                  className="px-2 py-1 text-[11px] font-medium text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition flex items-center gap-1"
                >
                  <Eye size={12} /> Preview
                </button>
                {!readOnly && (
                  <button
                    onClick={() => handleDelete(file.id)}
                    className="p-1 text-destructive/80 hover:text-destructive hover:bg-destructive/10 rounded-lg transition"
                    title="Delete document"
                  >
                    <Trash2 size={13} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview File Modal */}
      {previewFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-card border border-border rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <span className="text-sm font-semibold text-foreground flex items-center gap-2">
                <FileText size={16} className="text-primary" /> {previewFile.file_name}
              </span>
              <button
                onClick={() => setPreviewFile(null)}
                className="p-1 text-muted-foreground hover:text-foreground rounded-lg"
              >
                <X size={16} />
              </button>
            </div>
            <div className="p-4 overflow-y-auto flex-1 bg-background font-mono text-xs leading-relaxed text-foreground whitespace-pre-wrap">
              {previewFile.content_text}
            </div>
          </div>
        </div>
      )}

      {/* Create / Paste Document Modal */}
      {showPasteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-card border border-border rounded-2xl w-full max-w-lg p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h4 className="text-sm font-semibold text-foreground">Add Knowledge Document</h4>
              <button
                onClick={() => setShowPasteModal(false)}
                className="p-1 text-muted-foreground hover:text-foreground rounded-lg"
              >
                <X size={16} />
              </button>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">
                Document File Name
              </label>
              <input
                type="text"
                value={fileName}
                onChange={(e) => setFileName(e.target.value)}
                placeholder="e.g. guidelines.md"
                className="w-full text-xs bg-background border border-border rounded-xl px-3 py-2 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">
                Content Text (Markdown, CSV, JSON, or Plain Text)
              </label>
              <textarea
                rows={8}
                value={contentText}
                onChange={(e) => setContentText(e.target.value)}
                placeholder="Paste document reference text here..."
                className="w-full text-xs font-mono bg-background border border-border rounded-xl p-3 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
              <button
                onClick={() => setShowPasteModal(false)}
                className="px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
              >
                Cancel
              </button>
              <button
                disabled={!fileName || !contentText || isUploading}
                onClick={handleCreateTextFile}
                className="px-4 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-xl hover:opacity-90 disabled:opacity-50 transition shadow-subtle"
              >
                {isUploading ? "Saving..." : "Add to Knowledge Base"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
