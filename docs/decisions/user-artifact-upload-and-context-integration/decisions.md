# Architectural Decisions: User Artifact Upload & Swarm Context Integration

**Datetime:** 2026-10-29T19:19:15+05:30  
**Status:** In Review (Awaiting User Approval)

## 1. Unified Storage & Automatic RAG Indexing
- **Decision**: Whenever an artifact is created or uploaded via `POST /api/artifacts`, the backend automatically calls `ingest_and_index_document` into `RAGKnowledgeStore`.
- **Rationale**: Keeps artifacts and RAG in lockstep. Agents do not need a separate ingestion step; any artifact created or uploaded by a user is immediately searchable and retrievable via hybrid BM25 + vector similarity across all agent turns.

## 2. Dual-Mode Context Injection (Direct Embedding vs RAG Passages)
- **Decision**:
  - Small text/data artifacts (< 4 KB or ~600 words) are embedded directly in full into the agent's turn context block.
  - Large text or binary artifacts (PDF, DOCX, PPTX, XLSX) are queried against the user's prompt using the RAG knowledge store to retrieve top-3 most relevant grounded passages with confidence scores and citations.
- **Rationale**: Prevents prompt token saturation, reduces LLM latency, and guarantees grounded factual accuracy regardless of document length.

## 3. Client-Side Base64 Encoding for Universal File Ingestion
- **Decision**: The browser reads binary documents (`.pdf`, `.docx`, `.pptx`, `.xlsx`) via `FileReader.readAsDataURL()` and strips the MIME prefix, sending clean Base64 to `POST /api/artifacts`. Text files are read via `FileReader.readAsText()`.
- **Rationale**: Enables zero-dependency, pure JSON REST requests without requiring `multipart/form-data` parsers on serverless lambda boundaries, simplifying error handling and caching.

## 4. Cross-Feature Context Referencing
- **Decision**: Workflow steps and custom agents reference artifacts by ID (`attached_artifact_ids`), pulling from the shared user artifacts repository rather than duplicating files.
- **Rationale**: Ensures single source of truth, avoids storage duplication, and allows users to update or delete an artifact centrally.
