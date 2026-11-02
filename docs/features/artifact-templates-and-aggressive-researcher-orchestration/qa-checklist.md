# QA Checklist: Markdown Artifact Templates, Custom Templates & Aggressive Researcher Orchestration

**Datetime**: `2026-11-02T16:11:30+05:30`  
**Reviewer**: Automated Pair Programmer  
**Status**: Completed  

---

## 1. Functional QA

- [x] **Detailed Built-in Markdown Templates**:
  - [x] Executive Summary Report markdown specification exists with Tone, Inverted Pyramid construction, data density, word count (800-1200), and section blueprint.
  - [x] Research Synthesis Report markdown specification exists with Academic tone, IMRAD construction, empirical citations, and comparative matrix.
  - [x] Technical Specification Report markdown specification exists with RFC imperative conventions, typed schemas, and p95 SLAs.
  - [x] Financial Analysis Report markdown specification exists with GAAP/non-GAAP margins, multi-period tables, and sensitivity scenarios.
  - [x] Compliance Review Report markdown specification exists with audit baselines, pass/fail checklists, and remediation SLAs.
  - [x] Meeting Minutes markdown specification exists with action registers and DRI matrices.
  - [x] All 6 templates are exposed via central registry `BUILTIN_ARTIFACT_TEMPLATES`.

- [x] **Template Inspection Modal**:
  - [x] Attached template chip above input box is clickable and opens `TemplateDetailsModal`.
  - [x] Info inspection button exists on each template item in the `/artifact` popover list.
  - [x] Modal displays Tone, Construction Framework, Data Heaviness, and Target Length metadata pills.
  - [x] Modal displays section blueprint tags.
  - [x] Modal renders full scrollable markdown specifications.
  - [x] Copy markdown instructions button works cleanly.

- [x] **Input Box Behavior**:
  - [x] Selecting a template clears existing text from the input bar before inserting `"prepare a report according to /artifact [<Template Title>]"`.
  - [x] Removing the template chip restores normal input without clearing user-typed text.

- [x] **Custom User Templates in Artifacts Studio**:
  - [x] "New Template" button added to header in `frontend/src/app/artifacts/page.tsx`.
  - [x] `CreateTemplateModal` allows user to define Template Title, Badge, Description, and Markdown Specification.
  - [x] Saves custom template into artifact repository with `type: "template"` and `.md` filename.
  - [x] "Template" filter pill available in Artifacts Studio to filter template artifacts.
  - [x] `/artifact` popover in chat dynamically discovers custom templates and user-uploaded `.md` files.
  - [x] Custom templates display distinct amber badge (`bg-amber-500/15 text-amber-500 border-amber-500/30`).

- [x] **Aggressive Researcher Orchestration & Routing**:
  - [x] `route_agent` in `backend/app/main.py` defaults to `orchestrator` when no explicit single agent is selected.
  - [x] Explicit single agent target overrides (e.g. `@coder`) are preserved.
  - [x] `requires_fresh_internet_information` detects search verbs (`search out`, `search for`, `look up`, `find out`), financial/stock metrics, and temporal cues.
  - [x] Prompt `"search out the latest stock performances of apple, amazon and microsoft and then put them in an excel sheet"` generates multi-step pipeline: `step_1: researcher (model: sonar) -> step_2: data_analyst -> step_3: file_creator`.
  - [x] Researcher agent strictly uses Perplexity Sonar (`model: "sonar"`).
  - [x] Non-stock live search prompts with spreadsheet export generate `researcher (sonar) -> data_analyst -> file_creator`.
  - [x] Market intelligence prompts without file export generate `researcher (sonar) -> data_analyst -> synthesizer`.

---

## 2. Regression & Code Quality QA

- [x] `backend/test_aggressive_researcher_orchestration.py` passed (6/6 tests).
- [x] `backend/test_pdf_report_artifact.py` passed (3/3 tests).
- [x] Next.js production build succeeded (`npm --prefix frontend run build`, 14 routes statically generated, 0 errors).
- [x] All file paths in documentation formatted as clickable markdown links (`file:///...`).
- [x] All datetimes explicitly documented.
