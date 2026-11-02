# Implementation Log: Markdown Artifact Templates, Custom Templates & Aggressive Researcher Orchestration

All changes and step executions are tracked below chronologically.

---

### Step 1: Rich Markdown Template Architecture & Interactive Inspection Modal
- **Datetime**: `2026-11-02T15:45:00+05:30`
- **Files Changed**:
  - [`frontend/src/app/chat/templates/executive_summary.md`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/templates/executive_summary.md): [NEW] Detailed specification with Tone, Inverted Pyramid construction, high data density, 800-1200 words, and section blueprint.
  - [`frontend/src/app/chat/templates/research_synthesis.md`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/templates/research_synthesis.md): [NEW] Detailed specification with academic tone, IMRAD construction, empirical citations, 1200-2000 words, and comparative matrix.
  - [`frontend/src/app/chat/templates/technical_specification.md`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/templates/technical_specification.md): [NEW] Detailed specification with RFC imperative conventions, typed schemas, p95 SLAs, and implementation phasing.
  - [`frontend/src/app/chat/templates/financial_analysis.md`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/templates/financial_analysis.md): [NEW] Detailed specification with GAAP/non-GAAP margins, multi-period financial tables, bull/base/bear scenarios, and capital allocation.
  - [`frontend/src/app/chat/templates/compliance_review.md`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/templates/compliance_review.md): [NEW] Detailed specification with audit baselines, pass/fail checklist matrices, gap severities, and remediation SLAs.
  - [`frontend/src/app/chat/templates/meeting_minutes.md`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/templates/meeting_minutes.md): [NEW] Detailed specification with succinct action-oriented register, binding decisions, and DRI accountability matrix.
  - [`frontend/src/app/chat/templates/index.ts`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/templates/index.ts): [NEW] Central registry exporting `BUILTIN_ARTIFACT_TEMPLATES` with complete markdown instructions, tone, construction, data heaviness, and target length parameters.
  - [`frontend/src/app/chat/types.ts`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/types.ts): [MODIFY] Enriched [`ArtifactTemplate`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/types.ts) interface to support `tone`, `construction`, `dataHeaviness`, `targetLength`, `markdownInstructions`, `isCustom`, and `artifactId`.
  - [`frontend/src/app/chat/components/TemplateDetailsModal.tsx`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/components/TemplateDetailsModal.tsx): [NEW] Full-featured preview modal showing metadata pills, section blueprint tags, and complete scrollable markdown specifications with copy-to-clipboard action.
  - [`frontend/src/app/chat/components/ChatInput.tsx`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/components/ChatInput.tsx): [MODIFY]
    - Made attached template chip clickable to trigger `TemplateDetailsModal`.
    - Added info inspection trigger icon to popover template list items.
    - Updated `handleSelectTemplate` to explicitly clear the input bar before inserting `"prepare a report according to /artifact [${template.title}]"`.
- **Reason**: Fulfill user requirements for detailed markdown-based template guidelines (tone, construction, data heaviness, length), clickable inspection popup for attached template chips, and input bar clearing on selection.
- **Tests Added/Updated**:
  - Verified Next.js compilation, TypeScript types, and static page generation.
- **Commands Run**:
  - `npm --prefix frontend run build`
- **Result**:
  - Clean build succeeded: Exit code 0, 14 routes statically generated with 0 errors.

---

### Step 2: User Custom Templates in Artifacts Studio & Dynamic Picker Integration
- **Datetime**: `2026-11-02T15:53:00+05:30`
- **Files Changed**:
  - [`frontend/src/app/artifacts/page.tsx`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/artifacts/page.tsx):
    - Added "New Template" action button in the studio header.
    - Added `CreateTemplateModal` allowing users to define a custom report template (Name, Badge, Description, and Markdown Specification) and store it with `type: "template"`, `origin_agent: "user_template"`, and `.md` filename in the artifact repository.
    - Added `"template"` filter tab to filter custom templates alongside other media types.
  - [`frontend/src/app/chat/components/ChatInput.tsx`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/components/ChatInput.tsx):
    - Added dynamic loading of user custom `.md` and `type: "template"` artifacts from `localStorage` and `/api/artifacts`.
    - Automatically maps user templates into `ArtifactTemplate` objects with section parsing, custom badges, and full markdown specification preview.
    - Enriched `AttachedArtifact` interface with `source_title`, `source_type`, `mime_type`, and `origin_agent`.
    - Distinguishes custom templates in the `/artifact` popover with distinct amber badges (`bg-amber-500/15 text-amber-500 border-amber-500/30`).
- **Reason**: Enable users to author their own template artifacts or upload `.md` files directly in Artifacts Studio and immediately pick them from the `/artifact` template popover.
- **Tests Added/Updated**:
  - Verified Next.js build and TypeScript type check.
- **Commands Run**:
  - `npm --prefix frontend run build`
- **Result**:
  - Initial compile flagged missing `source_title` on `AttachedArtifact`.
  - Resolved by extending the `AttachedArtifact` interface with optional artifact metadata.
  - Re-run succeeded: Exit code 0, 14 routes statically generated with 0 errors.

---

### Step 3: Backend Orchestrator Default Routing & Aggressive Researcher Orchestration
- **Datetime**: `2026-11-02T16:08:00+05:30`
- **Files Changed**:
  - [`backend/app/main.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/main.py):
    - Refactored [`route_agent`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/main.py#L359-L380): Removed premature single-agent keyword interception so that whenever `target_id` is None, empty, or `"orchestrator"`, it returns `agent_registry.get_orchestrator()`. This guarantees the Orchestrator on-the-fly workflow synthesis engine always runs for chat interactions unless the user explicitly chose a single specialist from the UI.
  - [`backend/app/ai_generator.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/ai_generator.py):
    - Enhanced [`requires_fresh_internet_information`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/ai_generator.py#L548-L600) with aggressive live search triggers: search verbs (`"search out"`, `"search for"`, `"look up"`, `"find out"`), financial/stock metrics (`"stock performance"`, `"stock performances"`, `"stock movement"`, `"share price"`, `"market performance"`, `"financial metrics"`, `"quarterly earnings"`, `"market cap"`), and regex boundaries.
    - Updated [`synthesize_on_the_fly_workflow`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/ai_generator.py#L605-L1500):
      - Branch A (Live Market & Financial Intelligence): Evaluated `has_file_export`. When queries combine live stock/market research with spreadsheet/file requests, synthesizes a 3-step pipeline: `step_1: researcher (sonar) -> step_2: data_analyst -> step_3: file_creator`.
      - Branch D (Data Analysis & Export): Added `requires_fresh_internet_information` check to ensure live internet queries with file requests always begin with `researcher (sonar)`.
      - Branch E (Deep Research): Added `not has_file_export` guard to prevent long queries with file requests from prematurely terminating without `file_creator`.
      - Branch F (Structured File Generation): Added `requires_fresh_internet_information` check to ensure `step_1` is `researcher (sonar)` whenever live data is required.
      - Branch H (Real-Time Research): Added `has_file_export` check to generate `researcher (sonar) -> data_analyst -> file_creator`.
  - [`backend/test_aggressive_researcher_orchestration.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/test_aggressive_researcher_orchestration.py):
    - Added automated unit tests covering:
      1. Default auto-route to Orchestrator and preservation of explicit single targets.
      2. User stock performance and Excel prompt workflow synthesis.
      3. Comprehensive `requires_fresh_internet_information` detection.
      4. Live search with spreadsheet/file export.
      5. Market queries without file export ending in executive briefing.
- **Reason**: Fix orchestrator bypassing and ensure queries requiring fresh internet data (like `"search out the latest stock performances of apple, amazon and microsoft and then put them in an excel sheet"`) aggressively execute live web search with the researcher agent using Perplexity Sonar (`model: "sonar"`).
- **Tests Added/Updated**:
  - `backend/test_aggressive_researcher_orchestration.py`: 6 tests covering routing and multi-agent synthesis.
  - `backend/test_pdf_report_artifact.py`: 3 regression tests.
- **Commands Run**:
  - `$env:PYTHONPATH='backend'; backend\venv\Scripts\python backend/test_aggressive_researcher_orchestration.py`
  - `$env:PYTHONPATH='backend'; backend\venv\Scripts\python backend/test_pdf_report_artifact.py`
  - `npm --prefix frontend run build`
- **Result**:
  - All 6 orchestration tests PASSED (Ran 6 tests in 0.025s, OK).
  - All 3 PDF report artifact regression tests PASSED.
  - Next.js production build succeeded with exit code 0 across all 14 routes.
