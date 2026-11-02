# Feature: Batch Workflow Execution on Attached Files with Zip Output and Trace Carousel

Created At: 2026-11-02T19:16:00+05:30
Status: Draft

## Status

Draft | Awaiting User Approval

## Goal

Enable users to trigger any existing or default workflow mid-sentence (e.g., `"follow the /workflow ABC and execute it for all attached files"`) with interactive autocomplete/pointing to specific workflows, execute that exact workflow $n$ times across all $n$ attached files in an isolated batch run, package the resulting files and runtime logs into a downloadable `.zip` file artifact, and provide an interactive UI log viewer with `<` and `>` buttons to inspect per-file execution traces directly within the chat turn.

## Scope

- In scope:
  - **Mid-sentence `/workflow` trigger & pointing in ChatInput**:
    - Typing `/workflow`, `/wf`, or selecting from slash command menu dynamically detects mid-sentence position and displays an autocomplete popover listing matching workflows (with title, goal, and step counts).
    - Selecting a workflow replaces the token with `/workflow [Workflow Title]` (or inserts clean identifier) and mounts a workflow badge pill above the input bar with remove (`x`) button.
    - Prevents accidental chat form clearing when typing mid-sentence workflow commands.
  - **Batch Workflow Orchestration Engine (`backend/app/main.py`)**:
    - Mid-sentence workflow name/ID extraction via regex supporting brackets (`/workflow [Title]`) and space-delimited names (`/workflow Title`).
    - Robust lookup against Supabase database, `memory_store`, and default preloaded workflows by ID, title, or share slug.
    - Batch file detection when $n \ge 1$ files are attached and prompt indicates batch execution (e.g. "for all attached files", "each file", "all files") or multiple files are attached.
    - Sequentially or concurrently executes the target workflow for each attached file with isolated inputs (`file`, `filename`, `content`, `attached_artifacts: [f]`).
    - Aggregates per-file results: status, duration, tokens, step runs, and outputs.
  - **Automated In-Memory ZIP Compilation**:
    - Generates a `.zip` archive containing:
      - `outputs/{original_stem}_result.md` (or output artifact).
      - `logs/{original_stem}_execution_log.json` (step breakdown, tool calls, duration, tokens).
      - `batch_execution_summary.md` (root overview table).
    - Encodes zip to base64, attaches as a downloadable file artifact (`batch_results_<timestamp>.zip`, `mime_type: "application/zip"`).
  - **Interactive File Trace Carousel (`frontend/src/app/chat/components/MessageItem.tsx`)**:
    - When `batch_file_runs` is present in message metadata:
      - Renders a batch execution header with total files and workflow name.
      - Carousel controls: `<` (Previous) and `>` (Next) buttons, navigating between files.
      - Displays `File X of N: <filename.ext>` with status badge (`Completed`/`Failed`), duration (ms), and tokens used.
      - Renders the active file's runtime execution trace (`step_runs`, tool calls, outputs).
      - Includes a 1-click **Download All Results (.zip)** card.

- Out of scope:
  - Modifying non-batch DAG editor canvas logic.
  - Changing non-chat batch job scheduling (cron/background daemon workers).

## Current behavior

- Slash commands in [ChatInput.tsx](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/components/ChatInput.tsx) only activate when `input.startsWith("/")`. Mid-sentence `/workflow` is not detected or autocompleted.
- In `ChatInput.tsx`, typing any string starting with `/workflow ` clears the input box entirely and opens `WorkflowPickerModal` instead of submitting the prompt.
- In [backend/app/main.py](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/main.py), workflow invocation only checks `last_user_message.content.strip().startswith("/workflow")` and only takes the first word after `/workflow`.
- If a user attaches multiple files to a workflow invocation, the backend runs the workflow only once with all files grouped into `attached_artifacts`, rather than running the pipeline $n$ times once per file.
- There is no automatic ZIP packaging of multiple execution outputs and logs.
- [MessageItem.tsx](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/components/MessageItem.tsx) only renders a single overall trace, with no `<` `>` carousel to inspect per-file logs.

## Proposed behavior

1. **Mid-Sentence Autocomplete & Pointing**:
   - As the user types in [ChatInput.tsx](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/components/ChatInput.tsx), typing `/workflow` or `/wf` triggers a sleek floating popover listing available workflows loaded from `/api/workflows`.
   - Selecting a workflow inserts `/workflow [Workflow Title]` cleanly into the text and sets a selected workflow pill badge above the input.
   - Form submission preserves the sentence and dispatches it with attached artifacts.
2. **Orchestrator Mid-Sentence Workflow Resolution & Batch Execution**:
   - In `_execute_chat_turn`, regex detects `/workflow [Title]` or `/workflow Title` anywhere in `last_user_message.content`.
   - Resolves workflow by matching ID, slug, or title against database, memory store, and defaults.
   - If attached files are present ($n \ge 1$) and batch intent is detected (e.g. "for all attached files", "all files", "each file", or multiple attachments):
     - Iterates through each file $i \in \{1 \dots n\}$.
     - Invokes `workflow_engine.execute_workflow` for file $i$.
     - Collects execution trace, metrics, and generated content.
3. **ZIP File Packaging**:
   - Assembles an in-memory ZIP package using Python's `zipfile` module:
     - Output files under `outputs/`.
     - JSON execution logs under `logs/`.
     - Summary markdown table `batch_execution_summary.md`.
   - Emits downloadable artifact `file_artifact` with `mime_type: "application/zip"`.
4. **Interactive `< >` File Trace Carousel**:
   - In [MessageItem.tsx](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/components/MessageItem.tsx), a batch execution block renders with:
     - Navigation buttons `<` and `>` with disabled states at edges.
     - `File X of N: <filename>` label, status badge, execution time, tokens.
     - Expandable granular step trace and output preview for the active file.
     - Download card for the generated `.zip` archive.

## Implementation steps

1. **Backend Batch Workflow Engine & ZIP Packaging (`backend/app/main.py`)**:
   - Add regex helper `extract_workflow_reference(content: str) -> Optional[str]` to extract workflow titles or IDs mid-sentence.
   - Add `resolve_workflow(identifier: str, user_uid: str, token: Optional[str]) -> Optional[Dict[str, Any]]`.
   - Add batch execution loop in `_execute_chat_turn`:
     - If batch conditions match, run workflow per file.
     - Collect `batch_file_runs`.
     - Generate ZIP bytes using `zipfile.ZipFile`.
     - Return assistant message with summary table, `batch_file_runs`, and `file_artifact`.
2. **Frontend Mid-Sentence Workflow Autocomplete & Pill (`frontend/src/app/chat/components/ChatInput.tsx`)**:
   - Load workflows from `/api/workflows` and cache in component.
   - Detect cursor/input matching `/(?:workflow|wf)(?:\s+([^\n]*))?`.
   - Render floating workflow suggestion popover when triggered mid-sentence.
   - When a workflow is clicked, insert `/workflow [Title]` at cursor position.
   - Render active workflow pill above textarea.
   - Update `handleSubmit` so mid-sentence `/workflow` prompts are submitted cleanly.
3. **Frontend `< >` File Trace Carousel & ZIP Download (`frontend/src/app/chat/components/MessageItem.tsx`)**:
   - Define TypeScript interface `BatchFileRun`: `{ file_index, file_name, file_id, status, duration_ms, tokens_used, output_text, step_runs, artifacts }`.
   - Add state `currentBatchFileIdx` in `MessageItem`.
   - Render carousel header with `<` and `>` buttons, file counter, status pill, and timing.
   - Render active file's granular step trace using `GranularStepTrace` and output view.
   - Add `.zip` file download card with `FolderArchive` icon and file size.
4. **Automated Unit & Integration Tests**:
   - Unit tests in `backend/tests/test_batch_workflow_execution.py`:
     - Regex mid-sentence workflow extraction.
     - Batch execution loop across multiple simulated attached files.
     - ZIP file compilation and structure validation (presence of `outputs/`, `logs/`, and `batch_execution_summary.md`).
   - Frontend lint and typecheck (`pnpm run build` / `pnpm run lint`).
5. **Documentation & QA Checklist Updates**:
   - Update `implementation.md`, `verification.md`, and `qa-checklist.md`.
   - Update decisions in `docs/decisions/batch-workflow-execution-zip/decisions.md`.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/main.py` | Add mid-sentence workflow detection, batch execution loop, in-memory ZIP builder | Support `/workflow` anywhere in prompt and orchestrate $n$ runs with ZIP artifact |
| `frontend/src/app/chat/components/ChatInput.tsx` | Add mid-sentence workflow popover, workflow pill badge, submit handling | Enable typing `/workflow` mid-sentence and selecting target workflow |
| `frontend/src/app/chat/components/MessageItem.tsx` | Add `< >` file trace carousel, per-file step runs view, ZIP download banner | Allow user to inspect per-file logs and download ZIP bundle |
| `backend/tests/test_batch_workflow_execution.py` | Create new pytest test suite for batch workflow execution and ZIP packaging | Verify correct orchestration, file isolation, and zip validity |

## Interfaces

### Request / Payload
- Messages containing attached artifacts: `attached_artifacts: [{ id, filename, content, type, ... }]`
- Prompt with inline `/workflow [Title]` or `workflow_id` parameter.

### Response Metadata
```json
{
  "mode": "batch_workflow_execution",
  "is_batch_workflow": true,
  "workflow_id": "wf-123",
  "workflow_title": "Data Extraction Pipeline",
  "total_files": 3,
  "batch_file_runs": [
    {
      "file_index": 0,
      "file_name": "q1_report.pdf",
      "status": "completed",
      "duration_ms": 1450,
      "tokens_used": 720,
      "output_text": "Extracted metrics...",
      "step_runs": [...],
      "granular_trace": [...]
    }
  ],
  "file_artifact": {
    "id": "batch-zip-...",
    "filename": "batch_results_1762089600.zip",
    "name": "batch_results_1762089600.zip",
    "type": "zip",
    "mime_type": "application/zip",
    "is_base64": true,
    "content": "<base64_zip_bytes>",
    "size_bytes": 14250,
    "downloadable": true
  }
}
```

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Workflow title with spaces or punctuation in prompt | Mid-sentence parser might truncate or misidentify workflow title | Use bracketed syntax `/workflow [Title]` from autocomplete, plus fuzzy/substring matching against known workflows |
| Long batch run times with many files | Request timeout during HTTP or SSE stream | Sequential processing with per-step SSE progress events and individual error handling per file so failure in one file doesn't abort others |
| Large files creating oversized ZIP files in memory | Memory spike in backend container | Use in-memory `io.BytesIO` with `ZIP_DEFLATED` compression and cap per-file log size |

## Verification

- Unit tests:
  - `pytest backend/tests/test_batch_workflow_execution.py`
- Integration tests:
  - Run multi-file batch turn via FastAPI TestClient and verify ZIP contents via `zipfile.ZipFile`.
- Manual checks:
  - Type `"follow the /workflow Data Cleaner and execute it for all attached files"` in chat.
  - Attach 3 test files and submit.
  - Verify `< >` carousel scrolls through logs of File 1, 2, 3.
  - Click download ZIP and inspect files inside archive.
- Commands:
  - `pytest backend/tests/`
  - `cd frontend && pnpm run build`

## Rollout

Direct feature deployment behind standard API and UI components; backward compatible with single workflow runs and chat turns.
