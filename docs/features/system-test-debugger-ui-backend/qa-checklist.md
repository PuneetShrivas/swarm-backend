# QA Checklist: System Test Process UI and Backend Debugger

Created At: 2026-11-02T21:05:50+05:30
Updated At: 2026-11-02T21:43:30+05:30
Status: Verified

## Acceptance Checklist

- [x] Users can upload files (PDF, XLSX, CSV, DOCX, TXT, MD, JSON) directly into the System Test Modal.
- [x] Users can select existing workspace artifacts to include in the system test.
- [x] Attached test files display file icons, names, size, role badges, and removal buttons.
- [x] `WorkflowRunRequest` schema accepts `attached_artifacts`.
- [x] Execution engine extracts and makes test file content accessible to workflow steps.
- [x] `POST /api/workflows/{workflow_id}/run-stream` emits real-time SSE step events.
- [x] `WorkflowSystemTestModal.tsx` shows an animated live progress bar with percentage and step counter.
- [x] Step sequence displays real-time status pills (pending, running with loader, completed with duration, failed).
- [x] "Debug Console" tab displays a real-time auto-scrolling log of execution events.
- [x] "Step Inspector" tab allows deep inspection of any step (rendered prompt, system prompt, knowledge documents, tool calls, and output).
- [x] Seamless fallback to standard execution if streaming is interrupted.
- [x] Automated tests pass (`test_system_test_debugger.py`).
- [x] Frontend builds cleanly with zero errors (`pnpm run build`).
