# Feature: Advanced File Generation (PDF, PPTX, DOCX, XLSX) & Ingestion with RAG Tooling

**Datetime:** 2026-10-29T18:49:15+05:30  
**Feature Slug:** `file-generation-and-rag-parser-tooling`  

## Status
In progress

## Goal
Empower the **File & Document Architect (`file_creator`)** to generate professional binary documents including PDFs, PowerPoint presentations (`.pptx`), Word documents (`.docx`), and Excel workbooks (`.xlsx`), alongside existing code, CSV, and JSON files, as downloadable Base64-encoded artifacts. Simultaneously, equip the **File & Document Ingestion Agent (`file_parser`)** with comprehensive binary parsing tools and a hybrid **RAG (Retrieval-Augmented Generation)** context engine (BM25 + vector cosine similarity) that chunks, indexes, and retrieves relevant contextual snippets across ingested files to pass to other agents in the swarm.

## Scope
- In scope:
  - Binary document generation tools in `backend/app/agents/file_creator/tools.py`:
    - `generate_pdf_document` (ReportLab)
    - `generate_presentation_deck` (python-pptx)
    - `generate_word_document` (python-docx)
    - `generate_spreadsheet_workbook` (openpyxl)
    - Universal `generate_file_artifact` with Base64 encoding support
  - Binary parsing and RAG context tooling in `backend/app/agents/file_parser/tools.py`:
    - `parse_binary_document` (handling PDF via `pypdf`, PPTX via `python-pptx`, DOCX via `python-docx`, XLSX via `openpyxl`)
    - `chunk_document` (heading-aware and sliding window with word overlap)
    - `index_document` (indexes chunks with metadata and builds BM25 + vector inverted index)
    - `query_document_context` (retrieves Top-K relevant chunks with confidence scores and source citations)
    - `generate_rag_context` (formats retrieved chunks into enriched prompt markdown for other swarm agents)
    - `list_indexed_documents` and `clear_indexed_documents`
  - Integration in `backend/app/main.py`:
    - File routing heuristics for PDF, PPT, Word, Excel prompts
    - RAG endpoints: `POST /api/documents/ingest` and `POST /api/documents/rag/query`
    - Tool execution mapping for new agent tools
  - Frontend client enhancements:
    - Base64-to-binary decoding (`Uint8Array` to `Blob`) in `MessageItem.tsx` and `artifacts/page.tsx` for clean OS downloads
    - Visual icons and filter tabs for `pdf`, `pptx`, `docx`, `xlsx`
    - Previews for binary documents showing document stats instead of raw binary strings
  - Automated tests covering generation, parsing, RAG retrieval, and endpoints.
- Out of scope:
  - OCR on scanned handwritten image PDFs (focus is on digital text and structured documents).
  - External paid third-party vector databases (a zero-dependency, serverless-friendly hybrid BM25 + cosine similarity vector store is implemented).

## Current behavior
- `file_creator` tools primarily generate plain text strings (code, markdown, csv, json) without native PDF, Word, PowerPoint, or Excel generation libraries.
- Binary files cannot be created natively or are created as text placeholders.
- `file_parser` tools only analyze line counts, delimiters, and JSON/CSV/AST syntax for plain text.
- There is no document chunking or RAG retrieval capability to search inside uploaded or generated documents and pass contextual snippets to other agents.
- The frontend downloads files as raw text blobs, which corrupts binary files like PDFs and Office OpenXML documents.

## Proposed behavior
- `file_creator` can generate fully formed binary PDFs, PPTX decks, DOCX reports, and XLSX spreadsheets with styling, tables, formulas, and headers.
- All binary artifacts are Base64-encoded with appropriate MIME types and `is_base64: True`.
- `file_parser` can ingest PDF, PPTX, DOCX, XLSX, CSV, JSON, and Markdown files, extract text and structural sections, chunk them into passages, index them, and run hybrid RAG queries.
- Any swarm agent can call `query_document_context` or `generate_rag_context` to pull relevant excerpts from ingested documents into its system prompt or scratchpad.
- Frontend downloads convert Base64 into binary `Uint8Array` blobs so users get native, uncorrupted files that open in Word, PowerPoint, Excel, and Adobe Acrobat.

## Implementation steps
1. **Dependency Installation**: Install and register `reportlab`, `pypdf`, `python-docx`, `python-pptx`, and `openpyxl` in `backend/requirements.txt`.
2. **File Creator Tooling**: Implement `generate_pdf_document`, `generate_presentation_deck`, `generate_word_document`, `generate_spreadsheet_workbook`, and update `file_creator/tools.py`, `prompt.md`, `skills.json`, `config.json`.
3. **File Parser Ingestion & RAG Tooling**: Implement `parse_binary_document`, `chunk_document`, `index_document`, `query_document_context`, `generate_rag_context`, and update `file_parser/tools.py`, `prompt.md`, `skills.json`, `config.json`.
4. **Backend Integration & Routing**: Update `backend/app/main.py` routing, tool dispatching, and RAG context endpoints (`/api/documents/ingest`, `/api/documents/rag/query`).
5. **Frontend Binary Artifact Handling**: Update `MessageItem.tsx` and `artifacts/page.tsx` to decode Base64 into binary Blobs, add type badges, and display binary document metadata.
6. **Automated Testing & Verification**: Write unit tests in `backend/test_endpoints.py` for all 4 generators, 4 parsers, and RAG search. Verify full test suite passes.
7. **Documentation, Changelog & Git Push**: Update feature docs, architectural decisions, `CHANGELOG.md`, and deploy to production.

## Files to change
| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/requirements.txt` | Add document generation and parsing libraries | Support PDF, PPTX, DOCX, XLSX generation and parsing |
| `backend/app/agents/file_creator/tools.py` | Add PDF, PPTX, DOCX, XLSX generator tools | Enable binary document creation |
| `backend/app/agents/file_creator/prompt.md` | Update agent system prompt | Guide agent on binary document synthesis |
| `backend/app/agents/file_creator/skills.json` | Register new document skills | Declare agent capabilities to swarm orchestrator |
| `backend/app/agents/file_parser/tools.py` | Add binary parsers, chunking, and RAG indexing/retrieval tools | Ingestion and RAG capabilities |
| `backend/app/agents/file_parser/prompt.md` | Update parser agent prompt | Guide agent on RAG context extraction |
| `backend/app/agents/file_parser/skills.json` | Register RAG & binary parsing skills | Expose RAG search skills to swarm |
| `backend/app/main.py` | Update intent routing, tool execution, and RAG endpoints | Handle document queries and RAG retrieval |
| `frontend/src/app/chat/components/MessageItem.tsx` | Base64 binary decoding on download | Prevent file corruption for PDF/Office files |
| `frontend/src/app/artifacts/page.tsx` | Base64 download decoding, filter tabs, icons | Rich Artifacts Studio experience |
| `backend/test_endpoints.py` | Add unit tests for generation, ingestion, and RAG | Verify correctness and prevent regressions |
| `CHANGELOG.md` | Record feature updates | Maintain change history |

## Interfaces
- `POST /api/agents/file_creator/tools/{tool_name}/execute`
- `POST /api/agents/file_parser/tools/{tool_name}/execute`
- `POST /api/documents/ingest`
- `POST /api/documents/rag/query`
- Artifact payload interface with `is_base64: boolean` and `mime_type: string`.

## Risks and mitigations
| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Serverless timeout or memory spike during heavy PDF/presentation generation | Function timeout | Limit default slide/page bounds and generate clean vector elements in-memory using BytesIO buffers |
| Corrupt binary file download in browser | Unopenable file in Word/PowerPoint/Acrobat | Implement Base64-to-Uint8Array binary Blob conversion on client side with exact MIME types |
| Ingestion of malformed or password-protected PDFs | Exception during parsing | Graceful try/except fallback extracting raw stream text and returning informative error status |
| RAG retrieval latency on large files | Slow context generation | In-memory token-indexed inverted index and BM25 scoring with fast numpy/pure Python cosine similarity |

## Verification
- Unit tests: Test PDF, PPTX, DOCX, XLSX generation, extraction, chunking, and RAG search.
- Integration tests: End-to-end tool execution and RAG query endpoints.
- Commands: `backend\venv\Scripts\python backend\test_endpoints.py`, `npm --prefix frontend run build`.
