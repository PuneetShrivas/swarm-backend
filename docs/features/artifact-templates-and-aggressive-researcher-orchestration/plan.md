# Feature: Detailed Markdown Artifact Templates, Custom User Templates & Aggressive Researcher Orchestration

**Datetime**: 2026-11-02T15:35:00+05:30  
**Status**: Completed

---

## Goal

1. **Detailed Markdown Artifact Templates**:
   - Upgrade artifact report templates from superficial section lists into comprehensive markdown documents detailing:
     - Specific Tone & Voice (e.g. authoritative, analytical, direct, third-person executive).
     - Construction & Narrative Framework (e.g. inverted pyramid, problem-solution-action, evidence hierarchy).
     - Data Heaviness & Quantitative Rigor (e.g. specific metric densities, comparative tables, delta percentages, financial KPIs).
     - Length & Structural Constraints (e.g. target word counts, maximum paragraph sizes, structured callouts).
     - Detailed Section Directives & Schema Blueprint.
   - Restructure the templates architecture so every template is represented by its own Markdown file (`.md`).
   - Enable users to click on attached template chips in the chat input area to inspect the complete template specifications in an interactive preview modal.
   - Ensure selecting a template cleanly clears the input bar before inserting `"prepare a report according to /artifact [<Template Title>]"`.
   - Empower users to create and manage custom template artifacts directly in the Artifacts tab (`.md` files with `type: "template"`).
   - Dynamically load and surface both built-in system templates and custom user `.md` templates in the `/artifact` template picker.

2. **Aggressive Live Web Search & Dynamic Orchestration via Researcher Agent**:
   - Fix routing so chat turns without explicit single-agent overrides always route to the **Swarm Orchestrator** instead of being hijacked into single-agent turns by premature keyword matching in `route_agent`.
   - Upgrade the orchestrator's on-the-fly workflow synthesis so queries requiring fresh internet information, live market data, stock performances, news, or web search (e.g. *"search out the latest stock performances of apple, amazon and microsoft and then put them in an excel sheet"*) **aggressively deploy the Researcher Agent with Perplexity Sonar (`model: "sonar"`) as Step 1**.
   - Chain Step 1's live web search discoveries into `data_analyst` (for metrics calculation and schema normalization) and `file_creator` (for generating native Excel `.xlsx` spreadsheets or data tables), concluding with a synthesized briefing and downloadable file artifact.

---

## Scope

### In Scope
- **Markdown Template Files**:
  - Store built-in templates as standalone markdown files under `frontend/src/app/chat/templates/` and expose them via `frontend/src/app/chat/templates/index.ts`.
  - Include detailed guidelines for Executive Summary, Research Synthesis, Technical Spec, Financial Analysis, Compliance Review, and Meeting Minutes.
- **Template Details Modal & Click-to-Inspect**:
  - Make attached template chips clickable in `ChatInput.tsx`.
  - Render a modal showing Tone, Construction, Data Heaviness, Word Count, and the full formatted Markdown instructions.
- **Input Bar Clearing**:
  - Clear the input bar prior to inserting `"prepare a report according to /artifact [${template.title}]"`.
- **Custom User Template Artifacts**:
  - Add "Create Template" action in `frontend/src/app/artifacts/page.tsx` saving `.md` template artifacts.
  - Add "Template" filter pill in Artifacts Studio.
  - In `ChatInput.tsx`, query user artifacts (`type === "template"` or `.md` files) and display them in the `/artifact` picker.
- **Aggressive Researcher Orchestration**:
  - Update `route_agent` in `backend/app/main.py` so requests without an explicit non-orchestrator agent ID always route to the Swarm Orchestrator.
  - Expand `requires_fresh_internet_information` in `backend/app/ai_generator.py` with broader cues (`search out`, `stock performance`, etc.).
  - Re-order and enhance `synthesize_on_the_fly_workflow` so any query with fresh internet information or web search intent aggressively executes `researcher` (Perplexity Sonar) as Step 1, even when combined with file generation (`excel sheet`, `csv`) or reporting.
- **Automated Verification**:
  - Automated tests verifying custom template loading, prompt clearing, on-the-fly workflow synthesis with live researcher agent, and Excel spreadsheet generation.

### Out of Scope
- Modifying underlying Perplexity API authentication mechanisms or billing tiers.
- Replacing the ReportLab PDF rendering engine with an external binary.

---

## Current Behavior

1. **Templates**:
   - `ARTIFACT_TEMPLATES` in `frontend/src/app/chat/components/ChatInput.tsx` is a flat TypeScript array containing only short descriptions and 4 section names.
   - It lacks instructions regarding tone, construction, data density, word count, and writing standards.
   - Templates are not markdown files.
   - Attached template chips above the input box are static and cannot be clicked to inspect instructions.
   - Selecting a template appends to or replaces input text without guarantee of clearing existing drafted text.
   - The `/artifact` picker only lists the 6 hardcoded templates; users cannot add their own template artifacts or pick uploaded `.md` templates.
2. **Orchestrator Routing**:
   - In `backend/app/main.py`, `route_agent` intercepts queries containing words like `"excel sheet"` or `"briefing"` and routes them to a single agent (`file_creator` or `synthesizer`) before the Orchestrator is reached.
   - Even in `synthesize_on_the_fly_workflow`, the File Generation branch (`has_file_gen`) sets `data_analyst` as Step 1 without checking if live web search is required.
   - As a result, the query `"search out the latest stock performances of apple, amazon and microsoft and then put them in an excel sheet"` fails to invoke the Researcher agent with Perplexity Sonar.

---

## Proposed Behavior

1. **Rich Markdown Templates**:
   - Create 6 dedicated `.md` files in `frontend/src/app/chat/templates/`:
     - `executive_summary.md`
     - `research_synthesis.md`
     - `technical_specification.md`
     - `financial_analysis.md`
     - `compliance_review.md`
     - `meeting_minutes.md`
   - Each markdown file contains comprehensive writing instructions:
     - **Tone & Persona**: Voice, perspective, vocabulary register.
     - **Construction Architecture**: Argument progression, paragraph structure.
     - **Data Heaviness**: Specificity thresholds, percentages, comparative tables, KPIs.
     - **Target Length**: Target word count and section sizing.
     - **Required Sections & Blueprint**: Concrete heading hierarchy and content requirements.
2. **Template Click-to-Inspect**:
   - Clicking an attached template chip opens `TemplateDetailsModal.tsx`, rendering the full formatted markdown specifications and parameter badges.
3. **Input Clearing on Selection**:
   - Selecting any template clears the input bar and sets `prepare a report according to /artifact [<Template Title>]`.
4. **User Custom Template Artifacts**:
   - Users can create a custom template directly in the Artifacts tab (`Create Template` button) or upload `.md` files.
   - The `/artifact` popover in `ChatInput.tsx` reads both built-in templates and user custom `.md` templates from the artifact store, presenting user templates in a dedicated "Your Custom Templates" group.
5. **Aggressive Live Web Search Orchestration**:
   - `route_agent` in `backend/app/main.py` defaults to `orchestrator` when no explicit single agent is selected by the user.
   - In `backend/app/ai_generator.py`, `synthesize_on_the_fly_workflow` checks for live web search and fresh information at top priority.
   - When a prompt seeks live information (e.g. stock performances, current prices, recent news) and file creation (e.g. excel sheet):
     - Step 1: `researcher` (`model: "sonar"`) -> Gathers live web quotes and evidence.
     - Step 2: `data_analyst` -> Evaluates valuation metrics and normalizes tabular schema.
     - Step 3: `file_creator` -> Generates production Excel spreadsheet (`.xlsx`) and summarizes insights.

---

## Implementation Steps

### Step 1: Rich Markdown Template Architecture & Inspection Modal
1. Create directory `frontend/src/app/chat/templates/` with 6 detailed `.md` files:
   - `executive_summary.md`
   - `research_synthesis.md`
   - `technical_specification.md`
   - `financial_analysis.md`
   - `compliance_review.md`
   - `meeting_minutes.md`
2. Create `frontend/src/app/chat/templates/index.ts` to export structured `ArtifactTemplate` objects with full markdown content, tone, construction, data heaviness, and length metadata.
3. Update `frontend/src/app/chat/types.ts` to enrich the `ArtifactTemplate` interface.
4. Create `frontend/src/app/chat/components/TemplateDetailsModal.tsx` to preview any template's detailed specifications.
5. Update `frontend/src/app/chat/components/ChatInput.tsx`:
   - Make attached template chips clickable to trigger `TemplateDetailsModal`.
   - Update `handleSelectTemplate` to clear the input bar before setting the template line.

### Step 2: User Custom Templates in Artifacts Studio & Dynamic Picker Integration
1. In `frontend/src/app/artifacts/page.tsx`:
   - Add "Create Template" button and modal dialog (`isCreateTemplateOpen`).
   - Store custom templates in the artifact store with `type: "template"` and `.md` filename.
   - Add "Template" filter pill alongside existing filters.
2. In `frontend/src/app/chat/components/ChatInput.tsx`:
   - Fetch custom `.md` and `type: "template"` artifacts from `localStorage` and `/api/artifacts`.
   - Merge them into the `/artifact` popover under "Your Custom Templates".
   - Allow searching and selecting custom templates with full preview support.

### Step 3: Aggressive Researcher Orchestration & Multi-Agent Live Search Workflows
1. In `backend/app/main.py`:
   - In `route_agent`, when `target_id` is None or `"orchestrator"`, route directly to `orchestrator` so the Orchestrator's workflow engine handles all chat turns.
2. In `backend/app/ai_generator.py`:
   - Expand `requires_fresh_internet_information` to capture `"search out"`, `"stock performance"`, `"share price"`, etc.
   - Reorder `synthesize_on_the_fly_workflow` so live search/fresh intelligence takes precedence over generic file generation.
   - For queries requesting fresh research + Excel/spreadsheet/file:
     - Produce 3-step DAG: `researcher` (sonar) -> `data_analyst` -> `file_creator`.
3. Add automated test suite `backend/test_aggressive_researcher_orchestration.py`.

### Step 4: Verification, Feature Documentation, Changelog & Git Push
1. Run backend tests: `backend\venv\Scripts\python backend/test_aggressive_researcher_orchestration.py` and `backend/test_pdf_report_artifact.py`.
2. Run frontend build: `npm --prefix frontend run build`.
3. Create `implementation.md`, `verification.md`, and `qa-checklist.md`.
4. Update `CHANGELOG.md`.
5. Commit and push to `origin main`.

---

## Files to Change

| File | Change | Reason |
| :--- | :--- | :--- |
| `frontend/src/app/chat/templates/*.md` | [NEW] 6 markdown template specification files | Establish standalone `.md` files defining tone, construction, data heaviness, and length |
| `frontend/src/app/chat/templates/index.ts` | [NEW] Central registry and parser for artifact templates | Provide typed template library with loaded markdown specifications |
| `frontend/src/app/chat/types.ts` | [MODIFY] Enrich `ArtifactTemplate` interface | Add tone, construction, dataHeaviness, targetLength, and markdownInstructions fields |
| `frontend/src/app/chat/components/TemplateDetailsModal.tsx` | [NEW] Template specification preview modal | Render full markdown instructions and metadata when user clicks template chip |
| `frontend/src/app/chat/components/ChatInput.tsx` | [MODIFY] Clickable template chip, input clearing, dynamic custom templates | Make chip clickable, clear input before insertion, surface user `.md` templates |
| `frontend/src/app/artifacts/page.tsx` | [MODIFY] Custom template creation & template filtering | Allow creating `.md` template artifacts and filtering by template type |
| `backend/app/main.py` | [MODIFY] Correct `route_agent` routing | Ensure auto-routed queries default to Orchestrator rather than single-agent hijacking |
| `backend/app/ai_generator.py` | [MODIFY] Aggressive researcher live web search workflow synthesis | Prioritize live search with Perplexity Sonar for queries seeking fresh stock/web info + files |
| `backend/test_aggressive_researcher_orchestration.py` | [NEW] Automated test suite | Verify live web search workflow orchestration, Excel generation, and custom templates |

---

## Interfaces

### 1. Enriched `ArtifactTemplate` Type
```typescript
export interface ArtifactTemplate {
  id: string;
  title: string;
  badge: string;
  description: string;
  sections: string[];
  defaultFormat: "pdf" | "markdown" | "docx";
  tone?: string;
  construction?: string;
  dataHeaviness?: string;
  targetLength?: string;
  markdownInstructions: string;
  isCustom?: boolean;
  artifactId?: string;
}
```

### 2. User Template Artifact Storage Contract
```typescript
{
  id: "art-template-<timestamp>",
  name: "Executive QBR Template.md",
  filename: "executive_qbr_template.md",
  type: "template", // or "md"
  content: "# Executive QBR Template\n\n## Tone\n...",
  size_bytes: 1420,
  created_at: "2026-11-02T15:35:00Z",
  origin_agent: "user_template",
  source_type: "template",
  downloadable: true,
  is_base64: false
}
```

### 3. Live Research + Excel Spreadsheet Workflow Specification
```json
{
  "title": "Live Market Research & Excel Synthesis Pipeline",
  "steps": [
    {
      "id": "step_1",
      "name": "Live Web Market Research",
      "step_type": "agent",
      "agent_id": "researcher",
      "model": "sonar",
      "instructions": "Search live web sources via Perplexity Sonar for current stock performance, market quotes, and metrics for Apple, Amazon, and Microsoft: {{inputs.prompt}}"
    },
    {
      "id": "step_2",
      "name": "Quantitative Valuation & Tabular Normalization",
      "step_type": "agent",
      "agent_id": "data_analyst",
      "instructions": "Normalize the discovered market data into structured columns and calculate comparisons: {{steps.step_1.output.text}}"
    },
    {
      "id": "step_3",
      "name": "Production Excel Spreadsheet Generation",
      "step_type": "agent",
      "agent_id": "file_creator",
      "instructions": "Generate formatted Excel spreadsheet (.xlsx) incorporating the structured financial table: {{steps.step_2.output.text}}"
    }
  ]
}
```

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| Perplexity API key missing or quota exhausted in local environments | Live search step could fail or stall | Workflow engine has built-in graceful fallback that returns structured synthetic search evidence with citations when offline/in test mode |
| User uploads an empty or malformed `.md` file as a template | Could show blank preview in template details popup | Provide sensible fallback title, default guidelines, and empty state notice in modal |
| Existing chats with single-agent locks affected | Users who explicitly picked an agent in the dropdown might be overridden | `route_agent` checks `if target_id and target_id.strip()` first; explicit user agent selections are always honored |

---

## Verification

- **Automated Tests**:
  - `backend/test_aggressive_researcher_orchestration.py`:
    - `test_route_agent_defaults_to_orchestrator`: Verify auto-routing directs to orchestrator.
    - `test_live_search_stock_excel_workflow`: Verify `"search out latest stock performances ... excel sheet"` synthesizes `researcher` (`sonar`) -> `data_analyst` -> `file_creator`.
    - `test_requires_fresh_internet_information_expanded`: Verify comprehensive coverage of search verbs.
  - `backend/test_pdf_report_artifact.py`: Ensure regression-free PDF generation.
  - `npm --prefix frontend run build`: Ensure 0 compilation/type errors.
- **Manual Checks**:
  1. Open chat, type `/artifact` -> verify template picker shows built-in templates.
  2. Select a template -> verify input bar is cleared and replaced with `"prepare a report according to /artifact [...]"`.
  3. Click on the template chip above the input bar -> verify `TemplateDetailsModal` opens with full markdown instructions.
  4. Navigate to Artifacts Studio -> click "New Template" -> create custom template -> return to chat -> verify it appears in `/artifact` picker.
  5. Run query: `"search out the latest stock performances of apple, amazon and microsoft and then put them in an excel sheet"` -> verify `researcher` (Perplexity Sonar) runs as Step 1 in `LiveExecutionConsole`.

---

## Rollout

Direct rollout to `main` following full verification and test passage.
