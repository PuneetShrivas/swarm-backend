# Feature: Standalone Portable Agnostic Workflow Package

## Datetime
`2026-11-05T12:34:19+05:30`

## Status
In progress

## Goal
Extract and package the prompt-driven agnostic research and report workflow into an entirely independent, zero-coupling standalone directory in the repository root (`agnostic_workflow/`). This folder can be zipped and transferred to any external environment (e.g., remote server, fresh VM, local machine, Docker container) and executed directly with its own `.env` configuration, `requirements.txt`, and entrypoint without any dependencies on the rest of the backend codebase.

## Scope
- In scope:
  - Create `agnostic_workflow/` in project root containing:
    - `__init__.py`: Package initialization and exports.
    - `config.py`: Self-contained environment variable loader (`.env` in current directory or parent) and default configurations.
    - `models.py`: Lightweight dataclasses (`SectionSpec`, `ReportPromptSpec`, `AgnosticEvidence`, `AgnosticReportResult`).
    - `spec_parser.py`: Robust Markdown specification parser supporting standard `#`/`##`/`###` headings, plain all-caps headings (`COMPANY SNAPSHOT`), and bold headings (`** UPDATES...**`).
    - `ledger.py`: Domain-agnostic Evidence Ledger with sequential citation indexing (`[E001]`, `[E002]`, etc.) and citation resolution.
    - `retrieval.py`: Self-contained Perplexity Search API client with batching, exponential retry, disk caching, snippet compaction, and wire news deduplication.
    - `roles.py`: Self-contained multi-provider LLM executor (Azure AI Foundry Anthropic REST / Entra ID, Groq, Google Gemini, IteraCompute) with per-step token tracking and 429 TPM rate-limit retry.
    - `renderer.py`: Publication File Generation Agent providing footnote transformations, Markdown formatting, and publication-ready ReportLab PDF compilation with NumberedCanvas (`Page X of Y`), running headers, and metadata tables.
    - `telemetry.py`: Granular ASCII hierarchical timings tree and columnar timings/token accounting table.
    - `orchestrator.py`: `AgnosticResearchOrchestrator` managing planning, web retrieval, gap analysis loops, pipelined drafting, and executive synthesis.
    - `run_workflow.py`: Standalone CLI executable entrypoint.
    - `templates/standard_research_report.md`: Default comprehensive research report specification template.
    - `requirements.txt`: Minimal dependencies (`reportlab`, `httpx`, `python-dotenv`, `azure-identity`, `azure-ai-projects`).
    - `.env.example`: Environment configuration template.
    - `README.md`: Instructions for standalone deployment, zipping, running, and configuring credentials.
    - `test_standalone_workflow.py`: Standalone test suite verifying independent execution.
  - Verification: Run unit tests and execute sample standalone workflow runs.
  - Documentation: Record feature docs in `docs/features/standalone-agnostic-workflow/` and decisions in `docs/decisions/standalone-agnostic-workflow/decisions.md`.
  - Update `CHANGELOG.md`.
- Out of scope:
  - Modifying the internal `backend/app/workflows/` files.

## Current behavior
The agnostic workflow created previously lives inside `backend/app/workflows/agnostic_research_report/` and relies on `app.agents.researcher.tools` for Perplexity searches and project-wide backend imports. Transferring it as a standalone zip to another environment would result in `ModuleNotFoundError` for missing `app.*` dependencies. Furthermore, `spec_parser.py` did not parse plain un-prefixed uppercase headers such as those found in `web-search-prompt.md`.

## Proposed behavior
1. `agnostic_workflow/` is a completely self-contained root folder.
2. It contains its own zero-dependency Perplexity client inside `retrieval.py` and its own multi-provider LLM caller in `roles.py`.
3. `spec_parser.py` is upgraded to support both Markdown `#`/`##` headings and plain text all-caps headings (`COMPANY SNAPSHOT`, `** UPDATES / PRESS RELEASES / NEWS**`), enabling seamless ingestion of files like `web-search-prompt.md`.
4. Anyone can zip `agnostic_workflow/`, copy it to another machine, run `pip install -r requirements.txt`, provide a `.env` file, and execute:
   ```bash
   python run_workflow.py "NVIDIA Corporation" --prompt-file web-search-prompt.md --provider azure --model claude-sonnet-4-6
   ```

## Implementation steps
1. Create `agnostic_workflow/` root directory.
2. Implement self-contained data models and config (`models.py`, `config.py`, `.env.example`).
3. Implement enhanced specification parser (`spec_parser.py`) supporting `#`/`##`/`###`, all-caps, and bold header patterns.
4. Implement self-contained Evidence Ledger (`ledger.py`) and Perplexity Web Search client (`retrieval.py`).
5. Implement self-contained multi-provider LLM roles with token accounting (`roles.py`).
6. Implement publication renderers (`renderer.py`) and orchestrator (`orchestrator.py`).
7. Implement telemetry (`telemetry.py`), standalone CLI entrypoint (`run_workflow.py`), default template, requirements, and README.
8. Add standalone unit test suite (`test_standalone_workflow.py`) and verify all tests pass.
9. Verify execution with `web-search-prompt.md` to confirm the 0-sections bug is resolved.
10. Update feature lifecycle documentation and `CHANGELOG.md`.

## Files to change / create
| File | Change | Reason |
| ---- | ------ | ------ |
| `agnostic_workflow/config.py` | Create | Self-contained environment config loader |
| `agnostic_workflow/models.py` | Create | Independent dataclasses |
| `agnostic_workflow/spec_parser.py` | Create | Enhanced parser supporting Markdown and plain uppercase headers |
| `agnostic_workflow/ledger.py` | Create | Independent evidence ledger |
| `agnostic_workflow/retrieval.py` | Create | Zero-dependency Perplexity Search API client & compactor |
| `agnostic_workflow/roles.py` | Create | Independent LLM caller with token accounting |
| `agnostic_workflow/renderer.py` | Create | Standalone ReportLab PDF & Markdown file generator |
| `agnostic_workflow/orchestrator.py` | Create | Complete workflow orchestrator |
| `agnostic_workflow/telemetry.py` | Create | Timing tree & token table renderers |
| `agnostic_workflow/run_workflow.py` | Create | Standalone CLI entrypoint |
| `agnostic_workflow/templates/standard_research_report.md` | Create | Standard report template |
| `agnostic_workflow/requirements.txt` | Create | Minimal pip dependencies list |
| `agnostic_workflow/.env.example` | Create | Environment variables template |
| `agnostic_workflow/README.md` | Create | Standalone deployment and execution guide |
| `agnostic_workflow/test_standalone_workflow.py` | Create | Standalone unit tests |
| `docs/features/standalone-agnostic-workflow/*` | Create | Feature lifecycle documentation |
| `docs/decisions/standalone-agnostic-workflow/decisions.md` | Create | Architecture decisions |
| `CHANGELOG.md` | Modify | Release log |

## Verification
- Run `python agnostic_workflow/test_standalone_workflow.py`
- Test parsing on `agent-instructions/web-search-prompt.md`
- Verify zero imports from `backend.app`
