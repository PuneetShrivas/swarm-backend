# QA Checklist: Groq Default Provider, File Generator Agent Fix, and Perplexity Research Workflow

## Datetime
2026-10-29T17:23:45+05:30

## Acceptance Criteria

- [x] **File Creator Routing**:
  - Prompt `"generate a sample csv file"` targets `file_creator`.
  - Intent matching for file creation takes precedence over `data_analyst`.
- [x] **File Artifact Extraction & UI Rendering**:
  - Code block regex accepts CRLF (`\r\n`) and trailing whitespace after fences.
  - Plain CSV response fallback works for `file_creator`.
  - Chat turn returns `metadata.file_artifact` and `metadata.artifacts`.
  - Frontend `MessageItem.tsx` renders the interactive file download card with filename, size, and one-click download.
- [x] **Perplexity Sonar in Default Workflow**:
  - `default-wf-research-pipeline` step 1 (`step_research`) specifies `model: "sonar"` and `agent_id: "researcher"`.
  - Workflow execution engine invokes Perplexity Sonar when `sonar` is requested.
  - `researcher` agent keeps `model: "sonar"`.
- [x] **Groq Site-wide Addition & Default**:
  - `groq` SDK installed and specified in `backend/requirements.txt`.
  - `DEFAULT_GROQ_MODEL = "qwen-3.8"` configured site-wide.
  - Chat completions, agent test sandbox, and workflow engine check `GROQ_API_KEY` and execute via Groq by default.
  - Model mappings resolve `qwen-3.8` to active Qwen models on Groq.
  - Fallback to Gemini (`gemini-3.8-flash`, `gemini-4-argon`) and Perplexity Sonar intact.
  - Frontend model selectors in Chat, Agents, and Workflows reflect `Qwen 3.8 (Groq Default)`.
- [x] **Automated Tests**:
  - 56/56 backend unit/integration tests passing.
  - Frontend production build passing with 0 errors.
