# Architecture Decision Record: Judicious Workflow Step Artifact Assignment and Resource Persistence

Created At: 2026-11-02T19:57:30+05:30
Status: Accepted

## Context

When users attach documents (e.g. report templates, source datasets, research papers) in chat, the orchestrator synthesizes an on-the-fly multi-agent workflow. Previously:
1. All attached files were dumped into Step 1 or left unassigned to subsequent steps.
2. A writer/synthesizer step needing a report template could not distinguish it from raw input spreadsheets or research documents.
3. When saving a workflow from the UI button (`SaveWorkflowModal`), the steps did not retain the attached files as permanent resources, causing subsequent runs of the saved workflow to lose access to the reference materials.

## Decisions

### 1. Semantic Artifact Purpose Classification
Artifacts are categorized into three primary roles:
- `template`: Report formats, layout templates, style guidelines (`.md` templates, `*format*`, `*template*`).
- `source`: Tabular datasets, metrics, computational inputs (`.xlsx`, `.xls`, `.csv`, `.json`).
- `reference`: Research documents, briefings, background articles (`.pdf`, `.docx`, `.txt`).

### 2. Judicious Step-to-Artifact Mapping
- Prompt entity references (e.g. `"use my_template.md for the report"`) take top priority.
- Semantic step roles:
  - `researcher` and `file_parser` steps receive `reference` artifacts.
  - `data_analyst` and `excel_specialist` steps receive `source` artifacts.
  - `writer` and `synthesizer` steps receive `template` artifacts.
- When a step receives an artifact, its instructions are enriched with an explicit directive mentioning the resource name.

### 3. Step-Level `resources` Schema & Execution Context Injection
- `WorkflowStep` model in `models.py` is extended with:
  ```python
  resources: List[Dict[str, Any]] = Field(default_factory=list)
  ```
- In `WorkflowExecutionEngine.execute_single_step`:
  - `step.get("resources")` are extracted.
  - Their text contents are appended to `relevant_files` and injected into the step's system instructions (`kb_text`).

### 4. UI Resource Visibility & Save Workflow Modal Integration
- `GranularStepTrace.tsx` displays resource chips under each step card.
- `SaveWorkflowModal.tsx` displays assigned resources in the modal preview and preserves `step.resources` in the `POST /api/workflows` payload.
- Saved workflows permanently store step resources in Supabase / `memory_store`, allowing repeated future executions with grounded context.

## Consequences

- Positive:
  - Clear separation of concerns between source data, reference materials, and report templates across multi-step pipelines.
  - Saved workflows become truly self-contained, retaining necessary templates and reference data without requiring re-attachment.
  - Fully backward compatible with workflows lacking step resources.
