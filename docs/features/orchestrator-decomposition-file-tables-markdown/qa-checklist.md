# QA Checklist: Orchestrator Decomposition, File Creator Tables & Markdown Tables

**Datetime:** 2026-10-29T21:26:00+05:30  
**Status:** Complete  

- [x] 1-Agent step workflows never show "Save as Workflow" suggestion banner or modal trigger.
- [x] Multi-agent workflows (>1 step) show "Save as Workflow" banner and modal trigger when ephemeral.
- [x] Orchestrator breaks down coding queries into multi-agent DAGs (`coder` -> `reviewer` -> `synthesizer`).
- [x] Orchestrator breaks down file generation queries into multi-agent DAGs (`data_analyst` -> `file_creator` -> `synthesizer`).
- [x] Orchestrator breaks down research queries into multi-agent DAGs (`researcher` -> `data_analyst` -> `synthesizer`).
- [x] Orchestrator breaks down math queries into multi-agent DAGs (`data_analyst` -> `synthesizer`).
- [x] `generate_spreadsheet_workbook` generates true openpyxl `Table` with zebra stripes and filters.
- [x] Cell values are typed (ints, floats, formulas) rather than dumped as text.
- [x] Header pane is frozen at `A2` for easy table scrolling.
- [x] Markdown tables in chat responses are rendered as styled HTML tables with headers, borders, and padding (`remark-gfm`).
- [x] Backend test suite (all 71 tests) passes.
- [x] Frontend build succeeds with zero errors (all 14 routes compiled).
- [x] Deployed to Vercel production.
