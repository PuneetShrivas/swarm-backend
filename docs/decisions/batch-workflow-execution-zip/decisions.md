# Architecture Decision Record: Batch Workflow Execution, Mid-Sentence Autocomplete, and Zip Compilation

Created At: 2026-11-02T19:16:30+05:30
Status: Accepted

## Context

Users want to run established multi-agent workflows against batches of documents (e.g., $n$ spreadsheets, PDFs, or code files) by issuing natural language commands such as `"follow the /workflow ABC and execute it for all attached files"`.
Previously:
1. `/workflow` was only recognized if placed at the absolute start of the prompt.
2. Typing `/workflow` in the input bar instantly cleared the input and opened a full modal, preventing natural language instructions around it.
3. Multiple attached files were passed en masse into a single workflow invocation instead of iterating $n$ times per file.
4. There was no aggregate ZIP artifact bundling output files and execution traces.
5. The chat UI had no mechanism to navigate through individual per-file execution logs and step runs.

## Decisions

### 1. Mid-Sentence Autocomplete and Workflow Pointing
- In `ChatInput.tsx`, active cursor text matching `/(?:workflow|wf)(?:\s+([^\n]*))?` triggers an inline floating popover displaying available workflows loaded from `/api/workflows`.
- Selecting a workflow replaces the matching text with `/workflow [Workflow Title]` (or inserts it cleanly) and attaches a workflow pill badge above the input bar.
- Direct form submission is preserved: if the prompt contains mid-sentence instructions alongside `/workflow`, the message is transmitted normally to the backend instead of being intercepted and cleared.

### 2. Robust Multi-Stage Workflow Resolution in Backend
- In `_execute_chat_turn`, the backend uses regex to extract workflow candidates:
  - Bracketed: `/workflow\s+\[([^\]]+)\]`
  - Space-delimited: `/workflow\s+([a-zA-Z0-9_\-\.]+)(?:\s|$|,)`
- Candidates are matched against the user's Supabase workflows, `memory_store` workflows, and default workflows using ID, title (case-insensitive and substring), and share slug.

### 3. Batch Multi-File Isolation
- When attached files $n \ge 1$ are present and either the prompt indicates batch intent ("all attached files", "each file", "all files") or multiple attachments are provided with a workflow command:
  - The orchestrator executes the workflow $n$ times.
  - In each iteration $i$, inputs are scoped to that specific file (`file: file_i, attached_artifacts: [file_i]`).
  - Errors in one file execution are caught, logged, and isolated without failing the remaining batch.

### 4. In-Memory ZIP Compilation and File Artifact Generation
- Standard Python `zipfile.ZipFile` with `ZIP_DEFLATED` is used to create a ZIP bundle in memory (`io.BytesIO`):
  - `outputs/{stem}_result.md` (or generated file artifact)
  - `logs/{stem}_execution_log.json` (step runs, timings, token counts, tool calls)
  - `batch_execution_summary.md` (overview markdown table)
- The resulting archive is base64 encoded and attached to the chat turn as a standard downloadable file artifact (`type: "zip"`, `mime_type: "application/zip"`).

### 5. Interactive `< >` File Trace Carousel in UI
- In `MessageItem.tsx`, when `metadata.batch_file_runs` is present, a carousel navigation bar is rendered:
  - `<` (Previous) and `>` (Next) buttons, navigating between file runs with disabled boundary checks.
  - Indicator: `File X of N: filename.ext`
  - Per-file status badge (`Completed`/`Failed`), duration, and tokens.
  - Per-file runtime execution trace using `GranularStepTrace`.
  - Prominent **Download All Results (.zip)** card.

## Consequences

- Positive:
  - Users can write natural sentences referencing workflows mid-sentence.
  - True batch processing of files without requiring manual repetitive runs.
  - Instant 1-click download of all results and execution logs in a clean ZIP bundle.
  - Clear, navigable UI for inspecting step-by-step logs for each processed file.
- Trade-offs:
  - Batch execution time scales with the number of attached files; SSE streaming progress events ensure transparent real-time feedback during processing.
