# Architectural Decisions: Advanced File Generation (PDF, PPTX, DOCX, XLSX) & Ingestion with RAG Tooling

**Datetime:** 2026-10-29T19:07:30+05:30  
**Slug:** `file-generation-and-rag-parser-tooling`  

## Context
1. **File Generation Capabilities**:
   Previously, the `file_creator` agent was restricted to plain-text code snippets and simple CSV/JSON text files. Enterprise users and autonomous workflows require rich document deliverables including PDFs with typography and tables, PowerPoint presentation decks for pitch meetings, Word documents for proposals, and formatted Excel workbooks with automated sum formulas.
2. **File Ingestion & Context Passing**:
   The `file_parser` agent only performed basic syntax validation and delimiter sniffing on text payloads. There was no mechanism to parse binary files (PDF, PPTX, DOCX, XLSX) or break documents into semantic passages for Retrieval-Augmented Generation (RAG) so other agents (like the Researcher, Coder, or Orchestrator) could query document facts.
3. **Binary Artifact Handling in Web Browsers**:
   Standard string blobs in browser downloads corrupt binary files. Binary artifacts need Base64 encoding from the backend and client-side `Uint8Array` conversion to ensure files open properly in desktop tools like Adobe Acrobat, Microsoft Word, PowerPoint, and Excel.

## Decision 1: Pure-Python Engine Selection for Zero-Config Serverless Compatibility
- **PDF**: Selected `reportlab` (Platypus flowables, document templates, table styles) for lightweight, high-performance vector rendering without external C-binary system dependencies (e.g. wkhtmltopdf or LibreOffice).
- **Presentation**: Selected `python-pptx` for generating native OpenXML 16:9 widescreen presentation slide decks with text boxes and table shapes.
- **Word**: Selected `python-docx` for structured `.docx` document generation.
- **Excel**: Selected `openpyxl` for multi-sheet workbooks with cell styling, headers, and formulas.
- **PDF Parsing**: Selected `pypdf` for fast text and metadata extraction from digital PDFs.

## Decision 2: Hybrid BM25 & Vector Similarity RAG Knowledge Store
- Implemented `RAGKnowledgeStore` (`backend/app/rag/store.py`) providing:
  - Heading-aware section splitting and configurable sliding-window word chunking (default 150 words with 30-word overlap).
  - Hybrid scoring: BM25 term saturation and inverse document frequency combined with Jaccard/cosine term similarity.
  - Zero-dependency design that operates 100% in-memory with optional Supabase/SQLite persistence, ensuring instant execution in local tests and Vercel serverless environments without requiring expensive external vector database services.
  - Context generation tool `generate_rag_context` formatting Top-K chunks into structured Markdown blocks with source citations and confidence metrics.

## Decision 3: Client-Side Base64 Binary Blob Decoding
- Updated `frontend/src/app/artifacts/page.tsx` and `frontend/src/app/chat/components/MessageItem.tsx` to detect binary file types (`pdf`, `pptx`, `docx`, `xlsx`) or `is_base64: true`.
- Converts clean Base64 strings to `Uint8Array` using `atob`, creating an authentic binary `Blob` with the exact MIME type. This guarantees that downloaded files open cleanly in native desktop software without corruption.
