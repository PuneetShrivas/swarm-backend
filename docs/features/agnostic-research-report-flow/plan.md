# Feature: Prompt-Driven Agnostic Research & Report Generation Flow

## Datetime
`2026-11-05T11:17:20+05:30`

## Status
Complete

## Goal
Implement a domain-agnostic, prompt-driven research and report generation workflow (`backend/app/workflows/agnostic_research_report/`) inspired by the `do_risk_report` architecture. The workflow operates independently of any specific vertical or domain (not bound to financial underwriting or SEC filings), ingesting any user-provided subject/topic alongside an arbitrary single Markdown prompt specification file (`prompt.md`) defining desired sections, formatting rules, and evaluation criteria. An Orchestrator agent dynamically manages planning, live web search via Perplexity Search API, atomic evidence extraction into an Evidence Ledger, automated iterative Gap Analysis with research reruns, pipelined section drafting, and a File Generation Agent compiling publication-grade Markdown and ReportLab PDF documents with dynamic footnoting and NumberedCanvas page numbering. The system features model/provider selection via CLI, granular hierarchical timing trees, and token usage accounting.

## Scope
- In scope:
  - Create package `backend/app/workflows/agnostic_research_report/`:
    - `models.py`: Data models for agnostic section specs, prompt specs, evidence items, and execution results.
    - `spec_parser.py`: Dynamic Markdown prompt parser extracting global rules, section hierarchy, required fields, and closing statements.
    - `ledger.py`: Domain-agnostic Evidence Ledger storing atomic claims with citations, URLs, quotes, and confidence levels.
    - `retrieval.py`: Web Search Agent leveraging the raw Perplexity Search API with batching, disk caching, snippet cleaning, and syndicated wire deduplication.
    - `roles.py`: Multi-provider LLM role executor (Azure Foundry, Groq, Gemini, IteraCompute) with per-call token usage tracking, 429 TPM rate-limit backoff, and fallback failover. Roles include `plan`, `extract`, `gap`, `draft`, `synthesize`, and `verify`.
    - `orchestrator.py`: `AgnosticResearchOrchestrator` managing the multi-stage research, gap analysis, drafting, and synthesis pipeline.
    - `renderer.py`: File Generation Agent providing footnote citation conversion, Markdown compilation, and publication-ready ReportLab PDF generation (`Page X of Y`, headers/footers, metadata tables).
    - `telemetry.py`: Hierarchical timing trees, columnar timing tables, and token usage accounting per stage and section.
    - `cli.py`: Interactive and non-interactive CLI runner with model, provider, fallback model, mode, and prompt-file arguments.
    - `templates/standard_research_report.md`: Default comprehensive research report specification template.
  - Create CLI entrypoint `backend/run_agnostic_research_report.py`.
  - Comprehensive unit test suite `backend/test_agnostic_research_report.py`.
  - Architecture decisions doc in `docs/decisions/agnostic-research-report-flow/decisions.md`.
  - Feature lifecycle docs (`plan.md`, `implementation.md`, `verification.md`, `qa-checklist.md`).
- Out of scope:
  - Modifying the existing D&O specific workflow (`backend/app/workflows/do_risk_report/`).
  - SEC EDGAR lookups (specific to public US corporations).

## Current behavior
`backend/app/workflows/do_risk_report/` is tightly coupled to public company D&O risk underwriting (hardcoded SEC EDGAR CIK resolutions, XBRL financial facts parsing, litigation dockets, and fixed 13-section D&O templates). There is no generic, domain-agnostic workflow that can accept an arbitrary subject and an arbitrary Markdown format prompt to conduct web research, gap analysis, and document compilation.

## Proposed behavior
1. The user invokes the CLI with any subject (e.g., "Solid State Battery Commercialization", "AI in Healthcare Diagnostics", "Acme Corp Risk Analysis") and a path to a prompt `.md` file:
   ```bash
   python backend/run_agnostic_research_report.py "Solid State Battery Commercialization" \
       --prompt-file path/to/prompt.md \
       --model claude-sonnet-4-6 \
       --provider azure \
       --fallback-model claude-opus-4-8 \
       --mode standard \
       --format tree
   ```
2. `spec_parser.py` parses the `.md` file, extracting the section hierarchy, required data points, formatting guidelines, and closing statement.
3. The Orchestrator triggers the `plan` role to generate search queries per section.
4. The Web Search Agent queries Perplexity Search API and extracts verified atomic facts into an Evidence Ledger.
5. Automated Gap Analysis determines if any section requires follow-up queries, triggering research reruns based on `--mode` (`fast`, `standard`, `deep`).
6. The `draft` role generates each section citing `[E###]` evidence tokens.
7. The `synthesize` role handles executive summaries or overarching sections.
8. The File Generation Agent compiles both `.md` and publication-grade `.pdf` (ReportLab) files with running headers, footers, two-pass `Page X of Y` numbering, footnotes table, and metadata.
9. Granular timings and token usage are output in the terminal (tree/table) and persisted in `<report>_telemetry.json`.

## Implementation steps
1. **Planning & Approval**: Review and obtain user approval on implementation plan artifact.
2. **Data Models & Prompt Parser**:
   - Create `models.py` and `spec_parser.py` in `backend/app/workflows/agnostic_research_report/`.
   - Provide default prompt template in `templates/standard_research_report.md`.
3. **Evidence Ledger & Web Retrieval**:
   - Create `ledger.py` (domain-agnostic claim ledger).
   - Create `retrieval.py` (Perplexity Search API integration with caching and compaction).
4. **LLM Roles with Granular Token Tracking**:
   - Create `roles.py` supporting Azure Foundry (with API key & Entra ID Bearer token), Groq, Gemini, and IteraCompute.
   - Return token usage (`input_tokens`, `output_tokens`, `total_tokens`) and timing for every LLM call.
5. **Orchestrator & File Generation Agent**:
   - Create `orchestrator.py` managing multi-round research, gap checks, pipelined drafting, and synthesis.
   - Create `renderer.py` handling footnote transformations, Markdown output, and ReportLab PDF compilation.
6. **Telemetry & CLI**:
   - Create `telemetry.py` rendering hierarchical timing trees and token tables.
   - Create `cli.py` and `backend/run_agnostic_research_report.py`.
7. **Verification & Testing**:
   - Create `backend/test_agnostic_research_report.py` covering parser, ledger, orchestrator, PDF generation, and CLI parsing.
   - Run all test suites ensuring 100% pass rate.
8. **Documentation**:
   - Update `implementation.md`, `verification.md`, `qa-checklist.md`, and `decisions.md`.
   - Update `CHANGELOG.md`.

## Files to change / create
| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/agnostic_research_report/models.py` | Create | Agnostic data models and execution types |
| `backend/app/workflows/agnostic_research_report/spec_parser.py` | Create | Dynamic Markdown prompt structure and rules parser |
| `backend/app/workflows/agnostic_research_report/ledger.py` | Create | Agnostic evidence ledger with citation resolution |
| `backend/app/workflows/agnostic_research_report/retrieval.py` | Create | Perplexity Search API queue with compaction and caching |
| `backend/app/workflows/agnostic_research_report/roles.py` | Create | Multi-provider LLM roles with token tracking and 429 retry |
| `backend/app/workflows/agnostic_research_report/orchestrator.py` | Create | Cognitive orchestrator for planning, research, gap loops, and drafting |
| `backend/app/workflows/agnostic_research_report/renderer.py` | Create | File generation agent for Markdown and ReportLab PDF |
| `backend/app/workflows/agnostic_research_report/telemetry.py` | Create | Hierarchical timing tree and token usage accounting |
| `backend/app/workflows/agnostic_research_report/cli.py` | Create | Full-featured CLI runner |
| `backend/app/workflows/agnostic_research_report/templates/standard_research_report.md` | Create | Default general-purpose research prompt template |
| `backend/app/workflows/agnostic_research_report/__init__.py` | Create | Package initialization |
| `backend/run_agnostic_research_report.py` | Create | Top-level CLI entrypoint |
| `backend/test_agnostic_research_report.py` | Create | Automated unit tests |
| `docs/features/agnostic-research-report-flow/*` | Create | Feature lifecycle documentation |
| `docs/decisions/agnostic-research-report-flow/decisions.md` | Create | Architecture decisions |
| `CHANGELOG.md` | Modify | Changelog record |

## Interfaces
- **CLI**: `python backend/run_agnostic_research_report.py <subject> --prompt-file <path.md> [options]`
- **Python API**: `AgnosticResearchOrchestrator.run(subject=..., prompt_file=..., mode=..., provider=..., model=...)`
- **Output Artifacts**: `<output_dir>/<subject_slug>_<timestamp>.md`, `.pdf`, and `_telemetry.json`

## Risks and mitigations
| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Rate limits on selected LLM (e.g. Azure Foundry 429 TPM) | Pipeline failure | Outer retry loops with backoff and automatic failover to `--fallback-model` |
| Malformed or unusual prompt `.md` syntax | Incomplete section extraction | Robust multi-pattern heading parser with fallback to default sectioning |
| Perplexity API timeout on large batch queries | Retrieval failure | Per-query retry with exponential backoff and disk caching |
| Large report token consumption | Truncation or excessive cost | Configurable max tokens per role, section pipelining, and compact search snippets |

## Verification
- Unit tests: `backend\venv\Scripts\python.exe -m unittest backend.test_agnostic_research_report`
- Regression suite: `backend\venv\Scripts\python.exe -m unittest backend.test_azure_fast_pipeline backend.test_azure_agents_pipeline`
- Manual CLI test: Execute `run_agnostic_research_report.py` with custom prompt file.
