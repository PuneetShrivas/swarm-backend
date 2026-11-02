# QA Checklist: Batch Workflow Execution, Zip Output, and File Trace Carousel

Created At: 2026-11-02T19:19:45+05:30
Status: Complete

## Acceptance Checklist

- [x] Typing `/workflow` or `/wf` mid-sentence in `ChatInput` opens a floating workflow selector popover.
- [x] Selecting a workflow replaces the `/workflow` token with `/workflow [Workflow Title]` and renders a workflow badge pill above the input box.
- [x] Typing a natural prompt containing `/workflow <title>` does not clear the input box upon Enter/Send.
- [x] Backend extracts the workflow reference cleanly from mid-sentence prompts, supporting both bracketed and unbracketed titles.
- [x] If multiple files are attached and a workflow is referenced with batch intent, the orchestrator runs the workflow once per file.
- [x] Each file execution receives only its isolated file input in `attached_artifacts`.
- [x] Failures in one file run are recorded cleanly without aborting the other files in the batch.
- [x] The orchestrator compiles an in-memory `.zip` archive containing `outputs/`, `logs/`, and `batch_execution_summary.md`.
- [x] The assistant response returns a downloadable ZIP file artifact.
- [x] The UI renders a carousel header with `<` and `>` buttons.
- [x] The UI carousel displays `File X of N: <filename>`, status badge, duration, and tokens.
- [x] Clicking `<` and `>` navigates between files and updates the displayed step runs, tool calls, and output preview.
- [x] Boundary conditions: `<` is disabled on the first file (File 1), `>` is disabled on the last file (File N).
- [x] 1-click download button for the ZIP archive works cleanly.
- [x] All automated tests pass (`test_batch_workflow_execution.py`).
- [x] Frontend builds without TypeScript or ESLint errors (`pnpm run build`).
