# Architectural Decisions: Orchestrator Decomposition, File Creator Tables & Markdown Tables

**Datetime:** 2026-10-29T21:14:00+05:30  
**Status:** Approved  

## Decision 1: Gating the "Save as Workflow" UI Banner
- **Context:** Previously, the UI suggested saving any ephemeral workflow execution to the user's permanent workflow library, including 1-step single-agent executions.
- **Decision:** A workflow is only eligible for "Save as Workflow" suggestion if:
  1. `isEphemeral === true`
  2. `isMultiStep === true`
  3. The number of steps executed or defined is strictly greater than 1 (`steps.length > 1`).
  1-agent step executions will show the "1-Agent Step" badge in the trace header, but will NOT display the save suggestion banner or prompt the user.

## Decision 2: Aggressive Multi-Agent Workflow Synthesis by Orchestrator
- **Context:** Substantive queries for coding, file generation, research, or analysis were prematurely falling back to 1-agent executions in `synthesize_on_the_fly_workflow`.
- **Decision:** The Swarm Orchestrator will default to decomposing all non-trivial queries into multi-agent workflows:
  - File generation queries: `data_analyst` (structuring data schema and records) $\to$ `file_creator` (creating native formatted file artifact) $\to$ `synthesizer` (reviewing and providing user summary).
  - Coding queries: `coder` (implementation) $\to$ `reviewer` (security, quality & verification) $\to$ `synthesizer` (usage instructions & summary).
  - Research queries: `researcher` (live Sonar search) $\to$ `data_analyst` (comparative analysis/data synthesis) $\to$ `synthesizer` (structured briefing).
  - Data / math queries: `data_analyst` (computations & statistics) $\to$ `synthesizer` (insights & takeaways).
  Single-agent workflows are reserved exclusively for:
  1. Explicit user target selection (`target_agent_id` parameter supplied).
  2. Trivial one-phrase conversational greetings ("hi", "hello", "hey", "who are you").

## Decision 3: Native openpyxl Excel Tables & Intelligent Parsing
- **Context:** File creator was appending raw cells and borders without creating genuine Excel Tables (`openpyxl.worksheet.table.Table`), and cell values were not typed or converted from markdown/CSV outputs.
- **Decision:** Use openpyxl's `Table` class with `TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)`. Cell values will be cast to `int` or `float` where applicable, formulas starting with `=` preserved, top header row frozen (`ws.freeze_panes = "A2"`), and column widths auto-calculated. Implement `extract_tabular_data` to parse markdown tables (`| Col 1 | Col 2 |`) and CSV blocks into structured headers and rows.

## Decision 4: Markdown Table Rendering via `remark-gfm`
- **Context:** `react-markdown` strictly adheres to CommonMark by default, ignoring GFM table syntax.
- **Decision:** Install `remark-gfm` and configure `remarkPlugins={[remarkGfm]}` on `<ReactMarkdown>`. Provide tailored Tailwind component overrides for `table`, `thead`, `tbody`, `tr`, `th`, `td` matching the Linear design system tokens.
