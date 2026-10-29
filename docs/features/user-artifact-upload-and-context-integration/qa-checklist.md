# QA Checklist: User Artifact Upload & Swarm Context Integration

**Datetime:** 2026-10-29T20:00:00+05:30  
**Status:** Completed & Verified  

## Quality Assurance Checklist

### 1. Artifacts Studio (`/artifacts`)
- [x] User can click "Upload Artifact" and upload `.txt`, `.md`, `.json`, `.csv`, `.py`.
- [x] User can click "Upload Artifact" and upload binary files: `.pdf`, `.docx`, `.pptx`, `.xlsx`.
- [x] Uploaded artifact displays correct format icon, file size, and timestamp.
- [x] Uploaded artifact is automatically indexed in RAG knowledge store.
- [x] "Invoke in Chat" button redirects to `/chat?artifact_id=<id>` with artifact attached.
- [x] Deleting an artifact removes it from studio and unindexes it from RAG store.

### 2. Chat Input & Context Attachment (`/chat`)
- [x] Active attached artifacts display as chips above textarea with filename, type, and dismiss `(x)`.
- [x] User can click attachment button (paperclip) $\to$ "Upload File Context" to upload file directly from device.
- [x] User can click attachment button $\to$ "Attach from Artifacts" to select from previously uploaded artifacts.
- [x] Dragging and dropping a file onto the chat input bar triggers upload and attaches it as context chip.
- [x] When sending a message with attached artifacts, `/api/chat` receives `artifact_ids`.
- [x] Agent response accurately utilizes the content and data from the attached artifacts.

### 3. Workflow Steps Knowledge Integration (`/workflows/[id]`)
- [x] "Attach Knowledge Files" in `StepCardEditor` allows picking existing studio artifacts.
- [x] `KnowledgeBaseManager` supports binary file uploads (PDF, DOCX, PPTX, XLSX) in addition to text.
- [x] Step unit test and pipeline execution inject attached knowledge context into step execution.

### 4. Custom Agents Creation Integration (`/agents`)
- [x] `AgentEditorModal` contains "Attached Knowledge Artifacts" selector.
- [x] User can attach artifacts when creating or editing a custom agent.
- [x] Custom agent playground test and chat routing include the attached artifacts in agent context.

### 5. Regression & Build Validation
- [x] Full backend test suite passes: `backend\venv\Scripts\python backend/test_endpoints.py`.
- [x] Frontend builds with 0 errors: `npm --prefix frontend run build`.
- [x] No regression on existing 60 test cases (64/64 tests pass).
