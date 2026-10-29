# Feature: Orchestrator Decomposition, Intelligent File Creator Tables & Markdown Table Rendering

**Datetime:** 2026-10-29T21:14:00+05:30  
**Status:** In progress  

## Goal

1. Suppress "Save as Workflow" suggestion banners and actions for 1-agent step executions.
2. Aggressively decompose incoming user queries into multi-agent workflows (2–3 steps) by the Swarm Orchestrator rather than collapsing into single-agent runs.
3. Upgrade the `file_creator` agent and spreadsheet pipeline to intelligently process data into structured tabular representations, creating true native `openpyxl` Excel Tables (`Table` and `TableStyleInfo`) with typed cells, auto-filters, frozen header rows, and formatted columns instead of raw text dumps.
4. Render GitHub-flavored Markdown (GFM) tables properly in the chat message response body with responsive styling, borders, headers, and theme integration.

## Scope

### In scope:
- **1-Agent Step Save Banner Suppression**:
  - In `GranularStepTrace.tsx`, gate the "Save as Workflow" banner and modal trigger with `canSuggestSave = isEphemeral && Boolean(workflowSpec) && isMultiStep && (stepRuns.length > 1 || (workflowSpec.steps?.length || 0) > 1)`.
  - Prevent 1-agent step runs from prompting the user to save.
- **Aggressive Multi-Agent Workflow Decomposition**:
  - In `backend/app/ai_generator.py` (`synthesize_on_the_fly_workflow`), eliminate premature collapse into 1-step workflows for coding, file generation, research, and data analysis.
  - File generation queries: `data_analyst` (structuring data schema and records) $\to$ `file_creator` (creating native formatted file artifact) $\to$ `synthesizer` (reviewing and providing user summary).
  - Coding queries: `coder` (implementation) $\to$ `reviewer` (security, quality & verification) $\to$ `synthesizer` (usage instructions & summary).
  - Research queries: `researcher` (live Sonar search) $\to$ `data_analyst` (comparative analysis/data synthesis) $\to$ `synthesizer` (structured briefing).
  - Data / math queries: `data_analyst` (computations & statistics) $\to$ `synthesizer` (insights & takeaways).
  - Only explicit `target_agent_id` overrides or trivial greetings ("hi", "hello") remain 1-agent steps.
- **Intelligent File Creator & Native Excel Tables**:
  - In `backend/app/agents/file_creator/tools.py` (`generate_spreadsheet_workbook`), import `openpyxl.worksheet.table.Table` and `TableStyleInfo`.
  - Dynamically parse and cast string cell values into proper typed integers, floats, formulas (`=...`), or strings.
  - Apply native Excel `Table` with `TableStyleMedium9`, banded rows, auto-filter headers, and column freeze (`ws.freeze_panes = "A2"`).
  - Add robust tabular data parser (`extract_tabular_data`) capable of parsing markdown tables, CSV blocks, and delimited text from agent outputs.
  - Update `extract_file_artifact_from_turn` in `backend/app/main.py` to extract tables from markdown table syntax and delimited blocks.
  - Update `backend/app/agents/file_creator/prompt.md` to instruct the agent to always structure spreadsheet data into normalized tabular columns.
- **Markdown Table Rendering**:
  - Install `remark-gfm` in `frontend/package.json`.
  - Configure `ReactMarkdown` in `frontend/src/app/chat/components/MessageItem.tsx` with `remarkPlugins={[remarkGfm]}`.
  - Implement custom component overrides for `table`, `thead`, `tbody`, `tr`, `th`, `td` with Tailwind CSS design tokens (`hairline`, `surface-1`, `surface-2`, `ink`, `linear-primary`).
- **Automated Tests & Verification**:
  - Backend tests 69–71 verifying native Excel `Table` generation, multi-agent decomposition, and table extraction.
  - Frontend production build verification with 0 lint/TypeScript errors.

### Out of scope:
- Changing third-party spreadsheet viewer software outside the browser/download artifact flow.
- Modifying permanently saved workflows that were already created in previous sessions.

## Current behavior

- In `GranularStepTrace.tsx`, line 167 renders `{isEphemeral && workflowSpec && (` which shows the "Save as Workflow" banner even when `workflowSpec.steps.length === 1` or `!is_multi_step`.
- In `backend/app/ai_generator.py`, lines 809–826 route standard file creation ("generate csv"), coding ("write python code"), and search queries directly to 1-agent workflows instead of multi-agent workflows.
- In `backend/app/agents/file_creator/tools.py`, `generate_spreadsheet_workbook` creates basic worksheet cells with border lines, but does NOT create an openpyxl `Table` object, does not parse numeric strings to typed numbers, and does not parse markdown tables.
- In `backend/app/main.py`, `extract_file_artifact_from_turn` only checks for comma-separated lines and ignores markdown tables (`| col1 | col2 |`).
- In `frontend/src/app/chat/components/MessageItem.tsx`, `ReactMarkdown` has no `remarkGfm` plugin and no table component overrides, causing markdown tables to render as plain text paragraphs.

## Proposed behavior

1. When a 1-agent workflow or step executes, `GranularStepTrace.tsx` displays the "1-Agent Step" pill in the header, but completely suppresses the "Save as Workflow" suggestion banner and action button. Only multi-agent workflows with 2 or more steps display the save suggestion banner.
2. In chat, when the orchestrator receives any substantive query, it decomposes the problem into a 2- or 3-step multi-agent workflow DAG (`is_multi_step: true`), leveraging specialist agents (`data_analyst`, `file_creator`, `coder`, `reviewer`, `researcher`, `synthesizer`).
3. Spreadsheets generated by `file_creator` feature true native Excel Tables (`openpyxl.worksheet.table.Table`) with filter dropdowns, zebra rows, typed numeric data, formulas, auto-adjusted column widths, and frozen header rows. Markdown tables emitted by agents are parsed and converted into native tables.
4. Chat messages render GFM markdown tables with sleek borders, styled header cells, responsive horizontal scroll containers, and theme-adaptive colors.

## Implementation steps

1. **Step 1: Suppress Save Workflow for 1-Agent Steps**:
   - Update `frontend/src/app/chat/components/GranularStepTrace.tsx` to compute `canSuggestSave` requiring `isMultiStep && steps > 1`.
2. **Step 2: Aggressive Multi-Agent Workflow Decomposition**:
   - Update `backend/app/ai_generator.py` to synthesize multi-agent pipelines for file creation, coding, research, data analysis, and general inquiries.
3. **Step 3: Intelligent File Creator & Native openpyxl Tables**:
   - Enhance `generate_spreadsheet_workbook` in `backend/app/agents/file_creator/tools.py` with openpyxl `Table`, `TableStyleInfo`, typed values, and `extract_tabular_data`.
   - Update `extract_file_artifact_from_turn` in `backend/app/main.py` to parse markdown tables.
   - Update `backend/app/agents/file_creator/prompt.md` with structured tabular guidelines.
4. **Step 4: Markdown Table Rendering in Chat**:
   - Install `remark-gfm` in `frontend/`.
   - Add `remarkPlugins={[remarkGfm]}` and customized `table`, `thead`, `tbody`, `tr`, `th`, `td` components to `MessageItem.tsx`.
5. **Step 5: Testing, Verification & Production Deployment**:
   - Add backend tests 69–71 in `backend/test_endpoints.py` and run full test suite.
   - Run `npm --prefix frontend run build` to confirm 0 compilation errors.
   - Deploy backend to Vercel production and update changelog and verification records.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `frontend/src/app/chat/components/GranularStepTrace.tsx` | Gate save workflow banner with `isMultiStep && steps > 1` | Never suggest saving 1-agent step workflows |
| `backend/app/ai_generator.py` | Decompose coding, file creation, research, and analysis into multi-agent DAGs | Orchestrator should break down queries into workflows |
| `backend/app/agents/file_creator/tools.py` | Add openpyxl `Table`, `TableStyleInfo`, typed cell parsing, and `extract_tabular_data` | Intelligent structured Excel tables inside `.xlsx` |
| `backend/app/agents/file_creator/prompt.md` | Add structured table requirements to system prompt | Prevent unintelligent data dumping |
| `backend/app/main.py` | Parse markdown tables in `extract_file_artifact_from_turn` | Automatically extract spreadsheets from markdown tables |
| `frontend/package.json` | Add `remark-gfm` | CommonMark does not support GFM table syntax |
| `frontend/src/app/chat/components/MessageItem.tsx` | Configure `remarkPlugins={[remarkGfm]}` and custom table components | Render styled tables in message body |
| `backend/test_endpoints.py` | Add Tests 69–71 | Verify openpyxl table generation and multi-step decomposition |

## Interfaces

- **Openpyxl Table Specification**:
  `openpyxl.worksheet.table.Table(displayName="Data_Table_1", ref="A1:G15")` with `TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)`.
- **Markdown Component Render Tree**:
  `<table>` wrapped in `<div className="overflow-x-auto my-3 rounded-lg border border-hairline bg-surface-1">`.

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Openpyxl Table display name collisions | Excel file corruption if table name contains spaces or duplicates | Sanitize display name with regex `[A-Za-z0-9_]` and prefix with unique sheet index |
| Unstructured text cannot be parsed into columns | Empty spreadsheet or single-column string dump | Implement fallback parsing: markdown table parser $\to$ CSV/TSV parser $\to$ key-value pair parser |
| Next.js build issue with `remark-gfm` ESM package | Next.js compilation failure | `remark-gfm` is fully compatible with Next.js 14 and React 18, verify with `npm run build` |

## Verification

- Unit tests: Openpyxl native table structure validation in `test_endpoints.py`.
- Integration tests: Multi-step orchestrator decomposition validation (`is_multi_step == True`, `steps >= 2`).
- Build checks: Next.js frontend production build cleanly passes.
