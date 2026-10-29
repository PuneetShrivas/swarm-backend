# Feature Implementation: Groq Default Provider, File Generator Agent Fix, and Perplexity Research Workflow

## Status
Complete

## Datetime
2026-10-29T17:23:00+05:30

## Summary of Changes

### 1. File Generator Agent Routing & Artifact Fix
- **Keyword Precedence**: Updated `route_agent` in `backend/app/main.py` so that file creation intents (e.g. `"generate a sample csv file"`, `"create csv"`, `"download file"`, composite verb + file/csv/json noun) are evaluated **before** `data_keywords`. This prevents `data_analyst` from capturing queries containing `"csv"`.
- **Extraction Robustness**: Enhanced `extract_file_artifact_from_turn` with support for:
  - CRLF line endings (`\r\n`) alongside LF.
  - Trailing whitespace after code fences (e.g., ````csv   \n`).
  - Automatic tabular parsing of plain CSV responses when intent is file creation.
  - Automatic MIME type and extension mapping.
- **Artifact Attachment Across All Pipelines**: Connected `extract_file_artifact_from_turn` to Groq, Gemini, Perplexity Sonar, and demo simulation completions.
- **Frontend Download Resilience**: Added client-side fallback detection in `frontend/src/app/chat/components/MessageItem.tsx` so file download cards display reliably regardless of transport metadata.

### 2. Perplexity Sonar in Default Workflow
- Confirmed and verified that in `backend/app/workflows/default_workflows.py`, `step_research` explicitly targets `agent_id: "researcher"`, `model: "sonar"`, and instructions focused on live web search.
- Added `model` property to `WorkflowStep` in `backend/app/workflows/models.py` so step-level model overrides are serialized and persisted properly.

### 3. Groq Model Provider Site-wide Integration
- **Dependency**: Installed `groq` 1.7.0 in `backend/venv` and added `groq>=0.18.0` to `backend/requirements.txt`.
- **Groq Client Module (`backend/app/groq_client.py`)**:
  - `get_groq_client()` retrieves `GROQ_API_KEY`.
  - `DEFAULT_GROQ_MODEL = "qwen-3.8"`.
  - `resolve_groq_model_candidates()` maps `qwen-3.8` to Groq's high-performance Qwen series (`qwen/qwen3.8-27b`, `qwen-2.5-32b`, etc.) with graceful fallback.
  - `execute_groq_chat()` executes chat completions with usage tracking and candidate fallback.
- **Default Site-wide Model**:
  - Updated prebuilt agent configs (`backend/app/agents/*/config.json`) to use `qwen-3.8` (except `researcher` which uses `sonar`).
  - In `backend/app/main.py`, default model fallback is `qwen-3.8`.
  - In `/api/chat`, `test_custom_agent`, and `backend/app/workflows/engine.py`, Groq is the primary default provider when `GROQ_API_KEY` is present.
  - Maintained full secondary support for Google Gemini (`gemini-3.8-flash`, `gemini-4-argon`) and Perplexity (`sonar`).
- **Frontend Model Selectors**:
  - Updated `ChatHeader.tsx`, `AgentCard.tsx`, `AgentEditorModal.tsx`, `AIAgentGeneratorModal.tsx`, `VisualGraphEditor.tsx`, and `StepCardEditor.tsx` to display and default to `qwen-3.8` (Groq).
