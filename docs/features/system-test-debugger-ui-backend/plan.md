# Feature: System Test Process UI and Backend Debugger in Workflow Creation

## Status

Draft

## Goal

Provide a robust, end-to-end testing and real-time debugging experience in the workflow creation environment (`WorkflowSystemTestModal`). Enable users to attach test files (from device upload or Artifact Studio), monitor live pipeline progress as each step runs with visual indicators and progress bars, view real-time streaming debug logs via Server-Sent Events, and deeply inspect what each step is doing (rendered prompts, tool invocations, injected resources, and outputs).

## Scope

- In scope:
  - File attachments in `WorkflowSystemTestModal.tsx`: Local device upload (PDF, Excel, CSV, Word, TXT, JSON, MD) and workspace Artifact Studio selection.
  - Backend schema update: Add `attached_artifacts` to `WorkflowRunRequest` in `backend/app/workflows/models.py`.
  - Backend execution injection: Ensure test `attached_artifacts` are parsed and injected into `relevant_files` in `execute_single_step` and made accessible in `inputs`.
  - Real-time SSE streaming endpoint `POST /api/workflows/{workflow_id}/run-stream` in `backend/app/main.py`.
  - Live execution progress bar, step status indicators (pending, running, completed, failed), and live timer in `WorkflowSystemTestModal.tsx`.
  - Real-time Debug Console tab streaming timestamped execution logs with auto-scroll and copy.
  - Detailed Step Inspector showing rendered prompts, injected knowledge, tool calls with args/results, and formatted output previews.
  - Comprehensive unit and integration tests for backend streaming, file attachment ingestion, and frontend typecheck/build.
- Out of scope:
  - Replacing the visual graph editor with a different canvas framework.
  - Modifying other unrelated workflow modalities.

## Current behavior

1. **File Attachments**:
   - `WorkflowSystemTestModal.tsx` only allows text input key/value strings or a JSON textarea.
   - There is no file upload input and no artifact studio picker.
   - `WorkflowRunRequest` in `backend/app/workflows/models.py` only accepts `inputs: Dict[str, Any]` and `session_id: Optional[str]`.
   - `execute_single_step` in `backend/app/workflows/engine.py` only looks up `attached_artifact_ids` if already configured on the step, ignoring ad-hoc test attachments.

2. **Progress & Debugging Visibility**:
   - Running a system test performs a single synchronous blocking `POST /api/workflows/${workflowId}/run`.
   - While running (which can take 10s - 60s), the modal shows a static pulsing text `"Pipeline executing in swarm backend..."`.
   - There is no step-by-step progress bar, no indication of which step is executing, no live timer, and no streaming log.
   - After the run finishes, the step trace tab only renders a basic JSON view of `activeStepRun.output_data`, without prompt rendering, injected knowledge context, tool arguments, or diagnostic error traces.

## Proposed behavior

1. **Test File Attachment System**:
   - In `WorkflowSystemTestModal.tsx`, provide an "Attached Test Files & Datasets" section supporting:
     - Local file upload (drag & drop or file picker for PDF, XLSX, CSV, DOCX, TXT, MD, JSON).
     - "Attach from Artifacts Studio" button allowing users to pick existing workspace artifacts.
     - Each attachment shows a file icon, filename, size, role badge (`template`, `source`, `reference`), and remove button.
   - Sent to the backend as `attached_artifacts` in the run request.
   - The engine automatically extracts and parses attached artifacts and injects them into `relevant_files` for steps requiring knowledge or files.

2. **Real-time SSE Streaming Backend**:
   - `POST /api/workflows/{workflow_id}/run-stream` accepts `WorkflowRunRequest` and streams `text/event-stream` events:
     - `pipeline_start`: total steps, ordered steps sequence, input summary.
     - `step_start`: step index, step ID, step name, agent ID, model, timestamp.
     - `step_progress`: tool calls initiated, intermediate progress.
     - `step_completed`: duration ms, tokens, tool calls with results, output preview.
     - `step_failed`: error message, step ID, failure trace.
     - `pipeline_complete`: full final `WorkflowRun` object.
     - `error`: general runtime error.

3. **Live Progress & Debugging UI**:
   - **Progress Bar & Header**:
     - Visual animated progress bar: `(completed_steps / total_steps) * 100%`.
     - Live ticker: `Step 2 of 4: Financial Data Analysis (@data_analyst)`.
     - Stopwatch: `Elapsed: 00:05.4`.
   - **Dynamic Flow Indicators**:
     - Steps bar displays real-time animated status chips (Pending, Running with spinning loader, Completed with green check and latency, Failed with red X).
     - Clicking any step opens its detailed debugging inspector immediately.
   - **Live Debug Console Tab**:
     - Streaming terminal log with timestamped entries (`[21:05:02] ▶️ Step 1 started...`, `[21:05:04] 🔧 Tool called...`).
     - Auto-scroll lock toggle, copy logs button.
   - **Deep Step Inspector**:
     - Rendered prompt viewer.
     - Injected system instructions & knowledge/resources.
     - Tool calls table with arguments and returned stdout/JSON.
     - Output preview with copy button.
     - Error diagnostics panel when a step fails.

## Implementation steps

1. **Step 1: Backend Model & Execution Engine Enhancement**
   - Update `WorkflowRunRequest` in `backend/app/workflows/models.py` to include `attached_artifacts: List[Dict[str, Any]] = Field(default_factory=list)`.
   - Update `execute_single_step` and `execute_workflow` in `backend/app/workflows/engine.py` to ingest test `attached_artifacts` into `relevant_files` and `inputs`.

2. **Step 2: Backend Real-Time SSE Streaming Endpoint**
   - Add `POST /api/workflows/{workflow_id}/run-stream` in `backend/app/main.py`.
   - Stream `pipeline_start`, `step_start`, `step_completed`, `step_failed`, and `pipeline_complete` via `text/event-stream`.

3. **Step 3: Frontend Test File Attachments (`WorkflowSystemTestModal.tsx`)**
   - Implement local file upload (base64 / text reading) and artifact studio selection.
   - Render attached test resource chips with role badges and removal triggers.
   - Include `attached_artifacts` in the test run payload.

4. **Step 4: Frontend Live Progress, Real-Time Streaming & Debugger UI (`WorkflowSystemTestModal.tsx`)**
   - Implement SSE streaming consumer via `fetch` with `ReadableStream` reader (with fallback to standard POST).
   - Render live progress bar, active step ticker, and elapsed time counter.
   - Render live interactive step sequence with real-time status pills.
   - Add "Debug Console" tab showing streaming timestamped log entries.
   - Enhance "Step Traces" / "Step Inspector" tab with rendered prompts, tool call arguments/results, injected resources, and diagnostics.

5. **Step 5: Automated Testing & Verification**
   - Create `backend/test_system_test_debugger.py` testing run request with attached artifacts and SSE event streaming.
   - Run full regression tests and frontend typecheck / build.
   - Finalize documentation and QA checklist.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/models.py` | Add `attached_artifacts` to `WorkflowRunRequest` | Support file attachments in workflow run payload |
| `backend/app/workflows/engine.py` | Ingest test `attached_artifacts` into `relevant_files` in `execute_single_step` | Make test files available to steps during execution |
| `backend/app/main.py` | Implement `POST /api/workflows/{workflow_id}/run-stream` SSE endpoint | Stream real-time step progress and telemetry events |
| `frontend/src/app/workflows/types.ts` | Add `attached_artifacts` to payload types and step telemetry types | Frontend type safety |
| `frontend/src/app/workflows/components/WorkflowSystemTestModal.tsx` | Add file attachment picker, live progress bar, SSE stream consumer, Debug Console, and Deep Step Inspector | Resolve user inability to attach files, see progress, and debug steps |

## Interfaces

### API Endpoints
- `POST /api/workflows/{workflow_id}/run-stream`:
  - Request: `WorkflowRunRequest` (`inputs: Dict`, `attached_artifacts: List[Dict]`, `session_id: Optional[str]`)
  - Response: `text/event-stream` with JSON events:
    ```json
    data: {"type": "pipeline_start", "total_steps": 3, "steps": [...], "timestamp": "..."}
    data: {"type": "step_start", "step_id": "step_1", "step_index": 0, "step_name": "...", "agent_id": "...", "model": "...", "timestamp": "..."}
    data: {"type": "step_completed", "step_id": "step_1", "step_index": 0, "duration_ms": 2300, "tokens_used": 340, "output_preview": "...", "tool_calls": [...], "timestamp": "..."}
    data: {"type": "pipeline_complete", "run": {...}, "timestamp": "..."}
    ```

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Network interruption in SSE stream | Test might appear stuck if stream breaks | Implement heartbeat events and automatic fallback to standard POST execution |
| Large uploaded file sizes | Memory strain or payload limits | Truncate document bodies exceeding safe limit in `format_knowledge_context` |
| Long-running multi-step pipelines | Browser timeout | Keep-alive comment pings every 15s in the SSE stream generator |

## Verification

- Unit tests: Ingestion of `attached_artifacts` in `WorkflowRunRequest` and step execution.
- Integration tests: `POST /api/workflows/{workflow_id}/run-stream` SSE event streaming verification.
- Frontend verification: `pnpm exec tsc --noEmit` and `pnpm run build`.
