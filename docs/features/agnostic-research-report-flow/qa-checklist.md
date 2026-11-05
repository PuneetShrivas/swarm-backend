# QA Checklist: Prompt-Driven Agnostic Research & Report Flow

## Datetime
`2026-11-05T11:17:20+05:30`

- [x] Agnostic data models defined in `models.py` (`SectionSpec`, `ReportPromptSpec`, `AgnosticEvidence`, `AgnosticReportResult`).
- [x] Dynamic Markdown prompt parser implemented in `spec_parser.py` supporting arbitrary section headings, field checklists, and concluding statements.
- [x] Standard default research prompt template provided in `templates/standard_research_report.md`.
- [x] Domain-agnostic evidence ledger created in `ledger.py` with sequential `[E001]` IDs and citation lookup.
- [x] Web Search Agent implemented in `retrieval.py` using Perplexity Search API with disk caching, snippet compaction, and wire deduplication.
- [x] Strict credential enforcement: Mock search/role data strictly prohibited in live runs.
- [x] Cognitive LLM roles created in `roles.py` (`plan`, `extract`, `gap`, `draft`, `synthesize`, `verify`) with granular token accounting and 429 TPM rate-limit retry/failover.
- [x] Multi-provider support verified for Azure Foundry (Anthropic REST / Entra ID token provider), Groq, Gemini, and IteraCompute.
- [x] Cognitive orchestrator created in `orchestrator.py` managing multi-round research, automated gap analysis, concurrent drafting, and cross-section synthesis.
- [x] File Generation Agent created in `renderer.py` supporting footnote transformations, Markdown export, and publication ReportLab PDF generation with NumberedCanvas (`Page X of Y`), running headers/footers, and cover metadata table.
- [x] Hierarchical timing tree and token table formatters implemented in `telemetry.py`.
- [x] CLI entrypoints implemented in `cli.py` and `backend/run_agnostic_research_report.py`.
- [x] All 30 unit tests pass across test suites with zero regressions.
- [x] Feature documentation and architecture decisions recorded.
- [x] CHANGELOG entry added under `## [Unreleased] - 2026-11-05`.
