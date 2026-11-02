# Architecture Decisions: System Test Process UI and Backend Debugger

Created At: 2026-11-02T21:05:00+05:30

## 1. Real-Time Telemetry via Server-Sent Events (SSE)

### Context
Executing multi-agent pipelines takes from 5 seconds to over a minute. A blocking unary HTTP POST leaves users blind to pipeline progress, active step states, and tool invocations.

### Decision
Implement `POST /api/workflows/{workflow_id}/run-stream` with `text/event-stream`. Leverage FastAPI's `StreamingResponse` with an `asyncio.Queue` and threadsafe callback in `WorkflowExecutionEngine.execute_workflow`.
If the client cannot establish an SSE connection, fall back gracefully to synchronous `POST /api/workflows/{workflow_id}/run`.

## 2. Test File Attachment Ingestion Strategy

### Context
In system testing, users need to supply test files (e.g. sample spreadsheets, report formats, PDFs) without needing to configure permanent static knowledge base IDs beforehand.

### Decision
Add `attached_artifacts: List[Dict[str, Any]] = Field(default_factory=list)` to `WorkflowRunRequest`.
During step execution, if `attached_artifacts` are present, parse them via `extract_text_from_artifact` and inject them into `relevant_files` / `format_knowledge_context`. Also provide them in `inputs["attached_artifacts"]` so interpolation tokens (`{{inputs.<var>}}`) can reference them directly.

## 3. UI Tabbed Layout with Live Console & Step Inspector

### Context
Users need to both observe real-time progress while running and deeply debug individual steps after or during execution.

### Decision
In `WorkflowSystemTestModal.tsx`:
1. Maintain top-level live progress header and interactive step sequence bar with animated status pills.
2. Provide tabs:
   - **Final Output**: Clean preview of final output text with quick-copy.
   - **Artifacts**: Display generated files/reports.
   - **Step Inspector**: Deep dive into the selected step (rendered prompt, system prompt/knowledge, tool calls with arguments/results, step output).
   - **Debug Console**: Real-time auto-scrolling log terminal of all execution events.
   - **Raw JSON**: Complete payload for debugging.
