# QA Checklist: Workflow Step Artifact & Resource Judicious Assignment and Persistence

Created At: 2026-11-02T19:59:00+05:30
Updated At: 2026-11-02T20:18:30+05:30
Status: Verified

## Acceptance Checklist

- [x] Attached files are categorized by semantic purpose (`template`, `source`, `reference`).
- [x] Synthesized workflows assign templates to formatting/writer/synthesizer steps.
- [x] Synthesized workflows assign tabular data files to data analysis / computational steps.
- [x] Synthesized workflows assign research documents to researcher / parsing steps.
- [x] Explicit filename mentions in the user prompt take priority in step assignment.
- [x] Each step carries `resources: [...]` with file name, type, content, and role.
- [x] Step instructions are enriched with references to their assigned resources.
- [x] `WorkflowStep` schema supports `resources`.
- [x] `WorkflowExecutionEngine` injects step resources into `kb_text` during step execution.
- [x] `GranularStepTrace.tsx` renders resource chips under each step card.
- [x] `SaveWorkflowModal.tsx` previews step resources and includes them in the save payload.
- [x] Saved workflows retain step resources permanently upon retrieval and re-execution.
- [x] All automated tests pass (`test_workflow_step_resource_assignment.py`).
- [x] Frontend builds cleanly with zero errors (`pnpm run build`).
