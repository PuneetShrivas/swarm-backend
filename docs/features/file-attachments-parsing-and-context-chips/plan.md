# Feature: File Attachments Parsing Across All Types & User Context UI Highlights

**Datetime:** 2026-10-29T21:33:00+05:30  
**Status:** In progress  

## Goal

1. Eliminate "binary or corrupted file" LLM errors by ensuring that all attached files and accessed artifacts (PDF, DOCX, PPTX, XLSX, CSV, JSON, code, and text) are reliably extracted into clean, human-readable text before being injected into agent system/prompt contexts or workflow steps, strictly preventing raw Base64 or binary data dumps into prompts.
2. Provide a prominent, elegant UI highlight in user message bubbles indicating what file attachments and context artifacts were sent with the message (file name, format badge, size, and preview/download action), as well as grounding badges on assistant responses.

## Scope

### In scope:
- **Universal Multi-Format Document Parsing (`backend/app/agents/file_parser/tools.py`)**:
  - Implement `extract_text_from_artifact(artifact)` and `parse_document_or_artifact(filename, content, content_base64, file_type)` capable of parsing:
    - **PDF (`.pdf`)**: Robust `PdfReader` extraction across all pages with blank-password decryption, formatted with page separators.
    - **Word Documents (`.docx`, `.doc`)**: Extract paragraphs, headings, bullet lists, and table rows with `python-docx`.
    - **PowerPoint (`.pptx`, `.ppt`)**: Extract slide titles, shapes, text frames, tables, and speaker notes with `python-pptx`.
    - **Excel Spreadsheets (`.xlsx`, `.xls`)**: Extract all sheets with `openpyxl`, formatting rows as markdown tables or delimited lines.
    - **Structured Data & Code (`.csv`, `.tsv`, `.json`, `.py`, `.sql`, `.html`, `.xml`, `.yaml`, `.yml`, `.md`, `.txt`)**: Decode UTF-8 (with fallback to Latin-1/CP1252) into formatted text.
  - Robust Base64 cleaner: Strip Data URIs (`data:...;base64,`), replace spaces with `+`, remove line breaks, and ensure proper 4-byte padding.
- **Prompt Context Injection Overhaul (`backend/app/main.py`)**:
  - In `build_artifact_context_block`, call `extract_text_from_artifact` to ensure clean human-readable text is always available.
  - If RAG retrieval returns passages, include them; if generic or empty (e.g. "summarize this document"), inject the full extracted text (up to 8,000 characters) directly so the LLM is never left without content or given binary gibberish.
  - Automatically cache `extracted_text` in the artifact record upon `POST /api/artifacts` upload and retrieval.
- **Workflow Engine Knowledge Base Grounding (`backend/app/workflows/engine.py`)**:
  - In `_execute_agent_turn` / step knowledge injection, resolve attached artifacts and call `extract_text_from_artifact` instead of dumping raw Base64 `content`.
  - Pass `attached_artifacts` from chat into `workflow_engine.execute_workflow` for ephemeral on-the-fly execution.
- **Frontend User Message Context Highlight UI (`frontend/src/app/chat/components/MessageItem.tsx`)**:
  - Render an "Attached Context" section inside the user message bubble whenever `attached_artifacts` are present.
  - Format badges: Red for PDF, green for Excel/CSV, orange for PPTX, blue for Word/DOCX, indigo for code.
  - Display file name, formatted size (e.g. `24 KB`), format badge, and download/preview trigger.
  - Provide a subtle grounded context badge on assistant messages when grounded on attachments.
- **Automated Verification**:
  - Tests 72–74 covering PDF/DOCX/PPTX/XLSX text extraction, prompt context injection without binary corruption, and user message metadata attachment.
  - Next.js production build verification with 0 errors.

### Out of scope:
- Full-page OCR of completely flattened image-only PDFs without any textual characters.
- Modifying permanently archived historical chat sessions that were created without metadata.

## Current behavior

- When a PDF or binary file is uploaded in `/chat` or invoked from `/artifacts`, its `content` is stored as Base64 encoded string.
- If `rag_store.query_context` returns empty results for a query (e.g. "what is this document about?"), `build_artifact_context_block` appends `*Binary document attached (... bytes). Ready for analysis.*` without any text, or dumps the raw Base64 string if `is_binary` flag is false.
- In `workflow_engine.py` (line 557), step knowledge injection directly takes `art.get("content", "")` (raw Base64) and inserts it into `<KNOWLEDGE_BASE>`, causing the LLM to complain: "Based on the provided PDF content, it appears to be a binary or corrupted file."
- In `MessageItem.tsx`, user message bubbles render only raw prompt text with zero visual indication that files or context chips were attached.

## Proposed behavior

1. Whenever a file is uploaded or accessed from artifacts, `extract_text_from_artifact` reliably extracts clean human-readable text from PDF, DOCX, PPTX, XLSX, CSV, JSON, code, or plain text.
2. In `build_artifact_context_block` and `workflow_engine.py`, the LLM is always provided with formatted, human-readable extracted text (with page numbers, slide titles, or sheet tables). Raw Base64 or binary data is strictly barred from prompt injection.
3. In `MessageItem.tsx`, user messages clearly display an "Attached Context" card with format icons, file names, file sizes, and format tags.

## Implementation steps

1. **Step 1: Universal Document Text Extraction Utility**:
   - Implement `extract_text_from_artifact` and `parse_document_or_artifact` in `backend/app/agents/file_parser/tools.py`.
   - Support PDF, DOCX, PPTX, XLSX, CSV, JSON, and text with robust Base64 decoding and encoding fallbacks.
2. **Step 2: Grounded Prompt Context Injection & Workflow Engine Integration**:
   - Update `build_artifact_context_block` in `backend/app/main.py` to always inject clean extracted text.
   - Update `backend/app/workflows/engine.py` to resolve and extract readable text for `attached_artifact_ids`.
   - Update `POST /api/artifacts` to parse and cache `extracted_text`.
3. **Step 3: Frontend User Message Attached Context Highlight UI**:
   - Update `frontend/src/app/chat/components/MessageItem.tsx` to display attached context chips for user messages.
   - Update `frontend/src/app/chat/page.tsx` `handleSend` to ensure `attached_artifacts` are properly passed and persisted.
4. **Step 4: Automated Testing & Verification**:
   - Add Tests 72–74 in `backend/test_endpoints.py`.
   - Run backend test suite (all 74+ tests pass).
   - Run Next.js production build (`npm --prefix frontend run build`).
   - Deploy backend to Vercel production.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/agents/file_parser/tools.py` | Add `extract_text_from_artifact` and enhance `parse_binary_document` | Universal multi-format extraction for PDF, DOCX, PPTX, XLSX, CSV, text |
| `backend/app/main.py` | Overhaul `build_artifact_context_block` and `POST /api/artifacts` | Guarantee clean readable text in agent prompts; no raw Base64 |
| `backend/app/workflows/engine.py` | Extract readable text for workflow step knowledge injection | Prevent Base64 dump in workflow agent turns |
| `frontend/src/app/chat/components/MessageItem.tsx` | Render attached context chips on user messages | Visual highlight of attached context files |
| `frontend/src/app/chat/page.tsx` | Ensure `attached_artifacts` are bound to message node metadata | Reliable persistence and UI display |
| `backend/test_endpoints.py` | Add Tests 72–74 | Verify parsing of all file types and context injection |

## Interfaces

- **`extract_text_from_artifact(art: Dict[str, Any]) -> str`**:
  Returns human-readable text extracted from any artifact dictionary, decoding Base64 if needed and formatting pages/slides/sheets.
- **Message Metadata Interface (`AttachedArtifact`)**:
  `metadata.attached_artifacts: Array<{ id, name, filename, type, size_bytes, is_base64, content? }>`

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Malformed or corrupted Base64 strings | Decoding crash | Strip data URIs, replace spaces with `+`, sanitize whitespace, pad `=` modulo 4, wrap in try/except |
| Very large documents exceed prompt window | Context overflow | Cap extracted document text to 8,000 characters per document with clear truncation notice |
| Encrypted or password-protected PDF | PyPDF PasswordError | Attempt blank-password decryption; catch exception and report clear notice rather than crash |

## Verification

- Automated tests: Tests 72-74 in `backend/test_endpoints.py`.
- Regression tests: Tests 1-71 continue to pass.
- Build check: Next.js frontend production build succeeds with 0 errors.
