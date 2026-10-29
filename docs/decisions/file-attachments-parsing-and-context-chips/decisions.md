# Architectural Decisions: File Attachments Parsing & User Context Chips

**Datetime:** 2026-10-29T21:33:00+05:30  
**Status:** Approved  

## Decision 1: Universal Readable Text Extraction Layer
- **Context:** Previously, artifacts were stored with their raw Base64 strings. When passed to the LLM via `build_artifact_context_block` or `workflow_engine.py`, raw Base64 strings or empty RAG status notes were sent, causing models to complain that the file is binary or corrupted.
- **Decision:** Implement a centralized `extract_text_from_artifact` utility in `backend/app/agents/file_parser/tools.py`. Any document—whether PDF, DOCX, PPTX, XLSX, CSV, JSON, code, or text—must be decoded and parsed into clean human-readable text before being injected into system prompts, RAG blocks, or workflow contexts. Raw Base64 data is strictly forbidden from prompt context blocks.

## Decision 2: Fallback from RAG Passages to Full Extracted Excerpt
- **Context:** When users ask general questions like "summarize this file" or "what does this document say?", BM25 keyword matching often returns 0 results because the query has no term overlap with technical content in the document.
- **Decision:** In `build_artifact_context_block`, if RAG query yields no chunks or the document is under 8,000 characters, provide the full structured extracted text with section and page demarcations directly in the context block. Never output placeholder strings like `*Binary document attached...*`.

## Decision 3: User Message Attached Context UI Chips
- **Context:** User messages lacked visual feedback showing what files were attached, leaving users uncertain if their file was uploaded or processed.
- **Decision:** In `MessageItem.tsx`, when `node.role === "user"` and `node.metadata.attached_artifacts` has items, render a distinct "Attached Context" section inside the user bubble. Display format-colored badges (PDF red, Excel green, PowerPoint orange, Word blue, Code indigo), file names, formatted file sizes, and download/preview actions.
