# Feature: D&O Public Risk Report Granular Timing Telemetry & Single-Instruction CLI Runner

**Created Datetime**: 2026-11-03T14:08:00+05:30  
**Last Updated Datetime**: 2026-11-03T14:08:00+05:30  

## Status

Draft (Awaiting User Approval)

## Goal

Provide:
1. Copy-pasteable CLI instructions to immediately test the D&O Public Risk Report workflow on the existing codebase.
2. An organized hierarchical timing telemetry model that instruments and logs granular wall-clock and processing timings down to each pipeline stage, section, and subsection (e.g., Perplexity batch search latency, Groq fact extraction, Groq gap analysis, Groq section drafting, SEC EDGAR XBRL parsing, zero-web validation agent checks, and document rendering).
3. A single-instruction, standalone CLI test runner (`backend/run_do_risk_report.py` and `python -m app.workflows.do_risk_report.cli`) that accepts a ticker and executes the entire pipeline from ticker submission to final report artifact delivery, outputting a structured hierarchical ASCII/rich timings breakdown table.

## Scope

- In scope:
  - Immediate CLI instructions to test the existing workflow via python one-liner and HTTP curl.
  - Telemetry schema expansion in [`backend/app/workflows/do_risk_report/models.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/models.py) to represent hierarchical stage, section, and subsection timings.
  - Timing instrumentation in [`backend/app/workflows/do_risk_report/edgar.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/edgar.py) for CIK lookup, submissions fetch, XBRL facts parsing, and ledger population.
  - Timing instrumentation in [`backend/app/workflows/do_risk_report/retrieval.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/retrieval.py) per search query/batch.
  - Timing instrumentation in [`backend/app/workflows/do_risk_report/roles.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/roles.py) for individual Groq role calls.
  - Timing instrumentation in [`backend/app/workflows/do_risk_report/orchestrator.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/orchestrator.py) tracking per-section loops (round-level Perplexity search, Groq extract, Groq gap check, Groq draft narrative) and rendering sub-components (footnote transform, Markdown, Word DOCX, PDF).
  - Standalone single-instruction CLI tool [`backend/run_do_risk_report.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/run_do_risk_report.py) and module runner [`backend/app/workflows/do_risk_report/cli.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/cli.py).
  - Terminal-formatted hierarchical table rendering (tree/table format displaying stages, sections, subsections, elapsed ms, claim counts, and concurrency speedup multiplier).
  - Automated tests covering telemetry structure, CLI options, and execution output.
- Out of scope:
  - Modifying underlying Groq model selection or SEC EDGAR endpoints.
  - Altering core report contents or validation rules.
  - Modifying the Next.js frontend UI.

## Current behavior

1. Today, [`DORiskReportOrchestrator.run()`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/orchestrator.py#L120-L227) only records coarse stage timings in a flat dictionary:
   - `stages.edgar_resolution_ms`
   - `stages.research_and_draft_ms`
   - `stages.synthesis_ms`
   - `stages.validation_agent_ms`
   - `stages.rendering_ms`
   - `total_duration_ms`
2. Within Stage 2 (`research_and_draft_ms`), 11 sections are processed concurrently, but there is zero visibility into how much time each individual section took, or how much time was spent on Perplexity web retrieval vs Groq fact extraction vs Groq gap analysis vs Groq narrative drafting.
3. Within Stage 1, EDGAR ticker resolution, submissions metadata fetching, and XBRL Company Facts parsing are lumped together.
4. Within Stage 5, Markdown, DOCX, and PDF rendering times are lumped together.
5. There is no dedicated single-instruction CLI script (e.g. `python backend/run_do_risk_report.py AAPL`) to trigger end-to-end report generation from the command line outside of writing temporary python scripts or invoking `unittest`.

## Proposed behavior

1. **Hierarchical Timing Telemetry Structure**:
   `ReportResult.telemetry` will be expanded into a structured hierarchy:
   ```json
   {
     "total_wall_clock_ms": 42150.2,
     "total_compute_ms": 138400.5,
     "concurrency_speedup": "3.28x",
     "stages": {
       "stage_1_edgar_resolution": {
         "wall_clock_ms": 1420.5,
         "subsections": {
           "ticker_to_cik_lookup_ms": 180.2,
           "submissions_metadata_fetch_ms": 320.1,
           "company_facts_xbrl_fetch_ms": 680.4,
           "fact_extraction_and_ledger_ms": 239.8,
           "facts_found_count": 24
         }
       },
       "stage_2_research_and_draft": {
         "wall_clock_ms": 28400.1,
         "parallel_workers_count": 11,
         "sections": {
           "company_snapshot": {
             "total_ms": 4200.5,
             "subsections": {
               "retrieval_ms": 1100.2,
               "groq_extract_ms": 1450.1,
               "groq_gap_check_ms": 750.3,
               "groq_draft_narrative_ms": 899.9,
               "queries_count": 3,
               "claims_extracted": 5,
               "evidence_cited_count": 8,
               "char_length": 1420
             }
           },
           "financial_forensics": { ... },
           "litigation_regulatory": { ... },
           "governance_board": { ... },
           "cyber_ai_exposure": { ... },
           "esg_climate": { ... },
           "market_short_interest": { ... },
           "capital_structure": { ... },
           "executive_compensation": { ... },
           "peer_comparison": { ... },
           "industry_macro": { ... }
         }
       },
       "stage_3_synthesis_and_verdict": {
         "wall_clock_ms": 3800.4,
         "subsections": {
           "groq_synthesis_ms": 3800.4,
           "model_used": "openai/gpt-oss-120b",
           "risk_tier": "Contained",
           "char_length": 1850
         }
       },
       "stage_4_validation_agent": {
         "wall_clock_ms": 2900.2,
         "subsections": {
           "deterministic_validator_ms": 15.2,
           "deterministic_issues_count": 0,
           "validation_agent_pass_ms": 2885.0,
           "repair_coordinator_ms": 0.0,
           "repair_rounds": 0,
           "model_used": "qwen/qwen3.8-27b"
         }
       },
       "stage_5_artifact_rendering": {
         "wall_clock_ms": 850.1,
         "subsections": {
           "footnote_transformation_ms": 45.2,
           "footnotes_count": 42,
           "render_markdown_ms": 12.3,
           "render_docx_ms": 310.4,
           "render_pdf_ms": 482.2
         }
       }
     }
   }
   ```
2. **Single-Instruction CLI Runner**:
   A dedicated runner `backend/run_do_risk_report.py` (and `backend/app/workflows/do_risk_report/cli.py`):
   ```bash
   python backend/run_do_risk_report.py <TICKER> [--mode fast|standard] [--format table|tree|json] [--output-dir DIR]
   ```
   - Validates the ticker.
   - Executes the end-to-end pipeline in one instruction.
   - Prints an ASCII formatted tree/table of granular timings organized by stage, section, and subsection.
   - Prints final delivery paths for `.md`, `.docx`, and `.pdf` artifacts.
   - Returns exit code 0 on success.

## Implementation steps

1. **Step 1: Define Telemetry Models in `models.py`**
   - Add `SubstageTiming`, `SectionTimingTelemetry`, `StageTimingTelemetry`, and updated `ReportTelemetry` Pydantic models.
2. **Step 2: Instrument SEC EDGAR Extractor in `edgar.py`**
   - Track micro-timings for ticker-to-CIK resolution, submissions fetch, facts fetch, and ledger population.
3. **Step 3: Instrument Retrieval & Roles in `retrieval.py` and `roles.py`**
   - Record elapsed ms in search batches and LLM role executions.
4. **Step 4: Instrument Section & Pipeline Orchestrator in `orchestrator.py`**
   - Record per-section and per-round timing breakdowns: `retrieval_ms`, `groq_extract_ms`, `groq_gap_check_ms`, `groq_draft_narrative_ms`.
   - Record rendering breakdown: `footnote_transform_ms`, `render_markdown_ms`, `render_docx_ms`, `render_pdf_ms`.
   - Record validation breakdown: `deterministic_validator_ms`, `validation_agent_pass_ms`, `repair_coordinator_ms`.
   - Calculate total wall-clock time vs cumulative compute time and concurrency multiplier.
5. **Step 5: Build CLI Runner `cli.py` & `backend/run_do_risk_report.py`**
   - Implement argument parser (`--ticker`, `--mode`, `--format`, `--output-dir`, `--no-artifacts`).
   - Implement hierarchical terminal printer (rich ASCII table or tree).
   - Display delivery summary with file paths, sizes, and underwriting verdict.
6. **Step 6: Update Automated Tests in `backend/test_do_risk_report.py`**
   - Add unit tests for telemetry models and CLI parser.
   - Add test validating that granular timings contain all 5 stages, all 11 sections, and all expected subsections.
7. **Step 7: Verify, Document & Log**
   - Execute verification test suite.
   - Update `implementation.md`, `verification.md`, `qa-checklist.md`, and `CHANGELOG.md`.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| [`backend/app/workflows/do_risk_report/models.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/models.py) | Add typed Pydantic timing telemetry models | Strong typing and validation for hierarchical timing telemetry |
| [`backend/app/workflows/do_risk_report/edgar.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/edgar.py) | Add granular timing returns in `build_entity_card` and `populate_edgar_ledger` | Subsection timings for Stage 1 |
| [`backend/app/workflows/do_risk_report/orchestrator.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/orchestrator.py) | Capture per-section, per-round, and per-renderer subsection timings | Populate full hierarchical telemetry tree |
| [`backend/app/workflows/do_risk_report/cli.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/workflows/do_risk_report/cli.py) | Create CLI entry point and ASCII table/tree formatter | Execute workflow and render organized timings in terminal |
| [`backend/run_do_risk_report.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/run_do_risk_report.py) | Root-level CLI executable script | Convenient single-command execution (`python backend/run_do_risk_report.py AAPL`) |
| [`backend/test_do_risk_report.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/test_do_risk_report.py) | Add unit tests for telemetry models and CLI execution | Ensure telemetry schema and CLI integrity |
| [`CHANGELOG.md`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/CHANGELOG.md) | Document CLI runner and granular telemetry feature | Maintain repository changelog |

## Interfaces

### CLI Interface
```bash
python backend/run_do_risk_report.py <TICKER> [OPTIONS]

Options:
  --mode [fast|standard]     Execution mode (fast=1 search round, standard=2 search rounds). Default: standard
  --format [table|tree|json] Timing display format. Default: table
  --output-dir PATH          Custom directory to write artifacts (.md, .docx, .pdf). Default: backend/artifacts
  --date YYYY-MM-DD          Override current date for validation agent. Default: today
  --json-output PATH         Optional path to write full ReportResult JSON including telemetry
```

### JSON Telemetry Schema
Embedded in `ReportResult.telemetry` (and output with `--format json`):
- `total_wall_clock_ms`: float
- `total_compute_ms`: float
- `concurrency_speedup`: string (e.g. `"3.28x"`)
- `stages`: Dict mapping stage names (`stage_1_edgar_resolution`, `stage_2_research_and_draft`, `stage_3_synthesis_and_verdict`, `stage_4_validation_agent`, `stage_5_artifact_rendering`) to wall-clock ms and subsections/sections.

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Timing measurement overhead slows pipeline | Low | `time.perf_counter()` has sub-microsecond overhead; will not impact network-bound calls. |
| CLI terminal output width clipping on narrow displays | Medium | Adaptive formatter adjusting column widths or falling back to a clean indented tree format. |
| Backward compatibility with existing API consumers of `telemetry` | Low | Maintain existing top-level keys (`edgar_facts_count`, `evidence_count`, `total_duration_ms`) while adding nested structures. |

## Verification

- Unit tests:
  - `test_timing_telemetry_schema`: validates Pydantic model serialization and fields.
  - `test_cli_argument_parser`: tests CLI flags parsing and defaults.
  - `test_orchestrator_hierarchical_telemetry`: runs mock/fast pipeline and verifies all stages, sections, and subsections are populated.
- Integration test:
  - Run `python backend/run_do_risk_report.py AAPL --mode fast --format table` and verify zero errors, exit code 0, and non-empty artifact generation.
- Commands:
  - `backend\venv\Scripts\python.exe -m unittest backend.test_do_risk_report.TestDORiskReportModels`
  - `backend\venv\Scripts\python.exe backend/run_do_risk_report.py AAPL --mode fast`

## Rollout

- Immediate deployment in `backend/app/workflows/do_risk_report/` and root helper `backend/run_do_risk_report.py`.
- No database migrations or breaking API changes.
