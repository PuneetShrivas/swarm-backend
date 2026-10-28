# QA Checklist: Workflow Builder, Visual Editor, Execution Engine & Debugging

*Created: 2026-10-28T18:15:00+05:30*  
*Status: Verified & Completed (2026-10-28T18:49:00+05:30)*

## Database & Persistence
- [x] `workflows` table created with RLS and share slug.
- [x] `workflow_tools` table created with Python code storage.
- [x] `workflow_knowledge_files` table created with text extraction column.
- [x] `workflow_runs` and `workflow_step_runs` tables created.
- [x] `user_agents` table created for custom user agents.
- [x] MemoryStore fallback maintains 100% feature parity in offline tests.

## Backend Workflow Engine
- [x] Python tool runner parses AST and rejects malicious modules (`os`, `sys`, `subprocess`, etc.).
- [x] Tool runner enforces 5-second timeout and captures stdout/stderr.
- [x] Tool contract adheres strictly to `execute(input_data: dict, context: dict) -> dict`.
- [x] Engine executes DAG steps with topological sorting and handles linear pipelines.
- [x] Variable interpolation works for `{{inputs.*}}` and `{{steps.*.output}}`.
- [x] Knowledge file content is injected cleanly into step agent context.
- [x] Unit testing endpoint evaluates single step in isolation without executing preceding steps.
- [x] System test endpoint executes full workflow, saves telemetry, and returns output.
- [x] Shared workflow endpoint returns read-only data; update/delete operations return 403 Forbidden.

## Frontend Workflow Studio & Visual Editor
- [x] `/workflows` dashboard displays cards, search, filter, and create modal.
- [x] `/workflows/[id]` supports switching between Structured Card Editor and React Flow Graph Editor.
- [x] Connecting nodes in React Flow automatically updates step dependencies in card editor.
- [x] Editing step cards automatically updates React Flow nodes and edges.
- [x] Tools tab allows viewing Python code, editing, and running a live test.
- [x] Knowledge Base tab allows uploading files (.txt, .md, .csv) and previewing text.
- [x] Runs & Debugging tab shows historical runs, duration, token usage, and step logs.
- [x] Unit test drawer executes isolated step test and displays live output.
- [x] Share modal generates link with copy-to-clipboard and read-only indication.
- [x] Shared page (`/workflows/share/[slug]`) is read-only and includes a Fork Workflow button.

## Chat Integration
- [x] Chat input features a Workflow launcher button and `/workflow` command.
- [x] Running a workflow in chat injects an interactive workflow execution card with step progress and final output.
- [x] Chat session links directly to `workflow_runs`.
