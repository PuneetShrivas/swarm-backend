# Feature: Workflow Step Artifact & Resource Judicious Assignment and Persistence

Created At: 2026-11-02T19:57:00+05:30
Status: Draft

## Status

Draft | Awaiting User Approval

## Goal

When a user attaches various files (such as report formats, source documents, data attachments) either directly from their device or from the Artifacts Studio, the workflow synthesis engine must judiciously assign each file to its corresponding step based on semantic purpose and prompt references. Furthermore, when the user saves the synthesized workflow via the UI "Save Workflow" button, the assigned files must be persisted as permanent step resources within each step's specification so they are referenced on every subsequent execution.

## Scope

- In scope:
  - **Judicious Semantic File Classification & Step Assignment (`backend/app/ai_generator.py`)**:
    - Classify attached artifacts into semantic roles:
      - `template`: Report formats, markdown guidelines, structure specifications (e.g. `*.md` template, `*format*`, `*template*`, style guides).
      - `source`: Source data files, numerical spreadsheets, tables (`.xlsx`, `.xls`, `.csv`, `.json`).
      - `reference`: Research documents, PDFs, background briefs, articles (`.pdf`, `.docx`, `.txt`).
    - Parse user prompt for explicit filename references (e.g., `"use report_template.md for formatting"`, `"analyze data.xlsx in step 1"`).
    - Assign files to appropriate pipeline steps:
      - Research / Domain steps receive reference documents.
      - Data Analysis / Excel steps receive tabular source data.
      - Writer / Synthesizer steps receive formatting templates.
    - Each step receives `resources` and `attached_artifact_ids`, and the step instructions are enriched to reference its specific assigned resources.
  - **Step-Level Resource Schema & Engine Execution (`backend/app/workflows/`)**:
    - Add `resources: List[Dict[str, Any]] = Field(default_factory=list)` to `WorkflowStep` in `models.py`.
    - In `engine.py`, ensure `execute_single_step` resolves step resources and formats them into the step's knowledge base context (`kb_text`), making them accessible to the agent during execution.
  - **UI Resource Display & Workflow Persistence (`frontend/`)**:
    - In `GranularStepTrace.tsx`, display resource chips (`[Paperclip] <filename> (<Role>)`) under each step.
    - In `SaveWorkflowModal.tsx`, display assigned resources under each step in the workflow preview, and ensure `payload.steps` sends `resources` and `attached_artifact_ids` to `POST /api/workflows`.
    - In `backend/app/main.py`, ensure `create_workflow` persists step `resources` to Supabase or `memory_store`.

- Out of scope:
  - Modifying non-workflow chat prompt routing.
  - Binary image generation steps.

## Current behavior

- In `synthesize_on_the_fly_workflow` and `build_workflow_from_intent` in [backend/app/ai_generator.py](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/ai_generator.py), all attached artifact IDs are either dumped into Step 1 or omitted from remaining steps.
- There is no distinction between report templates, source data, and background research documents.
- In [backend/app/workflows/models.py](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/models.py), `WorkflowStep` only has `attached_artifact_ids: List[str]`, lacking a dedicated `resources: List[Dict[str, Any]]` field to store artifact content, filename, and role directly within the step.
- When saving a workflow via `SaveWorkflowModal.tsx`, step resources are not displayed, and if the user later runs the saved workflow, the step does not retain the original attached file contents as a permanent resource.

## Proposed behavior

1. **Semantic Role Classification & Prompt Entity Matching**:
   - `classify_artifact_purpose(art: Dict[str, Any], prompt: str) -> str`: Categorizes each artifact as `template`, `source`, or `reference`.
   - `assign_artifacts_to_steps(steps: List[Dict[str, Any]], artifacts: List[Dict[str, Any]], prompt: str)`: Judiciously distributes artifacts to matching agent steps (e.g. templates to `writer`/`synthesizer`, spreadsheets to `data_analyst`/`excel_specialist`, documents to `researcher`/`file_parser`).
   - Explicit prompt filename mentions override general heuristics to guarantee precise placement.
2. **Step Resource Schema & Execution**:
   - `WorkflowStep` model gains `resources: List[Dict[str, Any]] = Field(default_factory=list)`.
   - `execute_single_step` extracts `step.get("resources")` and injects their content into `relevant_files` and `kb_text`, ensuring the assigned model has full visibility.
3. **UI Preview & Persistent Saving**:
   - `GranularStepTrace` renders resource badges per step.
   - `SaveWorkflowModal` displays assigned resources under each step and transmits `resources` in `POST /api/workflows`.
   - Saved workflows retain resource contents permanently for repeated future executions.

## Implementation steps

1. **Backend Step Resource Schema & Engine Injection (`backend/app/workflows/`)**:
   - Add `resources` field to `WorkflowStep` in `models.py`.
   - Update `execute_single_step` in `engine.py` to extract `step.get("resources")` and inject into `relevant_files`.
2. **Backend Judicious Artifact Assignment in Workflow Synthesis (`backend/app/ai_generator.py`)**:
   - Implement `classify_artifact_purpose` and `assign_artifacts_to_steps`.
   - Update `build_workflow_from_intent` and `synthesize_on_the_fly_workflow` to assign artifacts judiciously and enrich step instructions.
3. **Frontend Step Resource Display & Save Persistence (`frontend/`)**:
   - Update `WorkflowSpec` interface in `GranularStepTrace.tsx` to include `resources`.
   - Render step resource badges in `GranularStepTrace.tsx`.
   - Update `SaveWorkflowModal.tsx` to display step resources and serialize `resources` in the save payload.
4. **Automated Testing & Verification**:
   - Add unit test suite `backend/test_workflow_step_resource_assignment.py` testing classification, assignment, and execution with step resources.
   - Run frontend typecheck and production build.
5. **Documentation & Changelog**:
   - Update `implementation.md`, `verification.md`, `qa-checklist.md`, `README.md`, and decision record.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/models.py` | Add `resources` to `WorkflowStep` | Schema support for persisting step resources |
| `backend/app/workflows/engine.py` | Extract `step.get("resources")` into knowledge context | Ensure steps can access assigned resource files at runtime |
| `backend/app/ai_generator.py` | Implement `classify_artifact_purpose` and `assign_artifacts_to_steps` | Judiciously assign attached files to appropriate steps |
| `backend/app/main.py` | Ensure `ephemeral_wf` step resources are preserved in `workflow_spec` | Enable UI to receive assigned step resources |
| `frontend/src/app/chat/components/GranularStepTrace.tsx` | Add `resources` to `WorkflowSpec` and render step resource badges | Display assigned files on trace |
| `frontend/src/app/chat/components/SaveWorkflowModal.tsx` | Show step resources and transmit in save payload | Persist resources when workflow is saved from UI |
| `backend/test_workflow_step_resource_assignment.py` | Create automated test suite | Verify classification, assignment, and persistence |

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Large file contents in step resources | DB payload size bloat when saving | Store parsed text or summarize content if size exceeds threshold; truncate raw binaries while keeping text schemas |
| Ambiguous file roles (e.g. a markdown file that could be source or template) | File assigned to wrong step | Inspect heading structure and keywords (e.g. `# Template`, `Executive Summary`) and prioritize explicit filename mentions in prompt |

## Verification

- Unit tests:
  - `pytest backend/test_workflow_step_resource_assignment.py`
- Integration tests:
  - Save workflow with step resources via `/api/workflows` and execute it, verifying step receives resource text.
- Frontend build:
  - `pnpm run build`
