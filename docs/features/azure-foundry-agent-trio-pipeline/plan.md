# Feature: Azure Foundry Three-Agent Pipeline (Researcher -> Validator -> Report Generator)

## Datetime
`2026-11-04T16:48:00+05:30`

## Status
Approved

## Goal
Create an independent, production-grade Python workflow in a new root folder (`azure_agents_pipeline/`) that coordinates three Azure AI Foundry preview agents (`DO-researcher`, `DO-validator`, `DO-report-generator`) using `azure-ai-projects>=2.1.0` and `DefaultAzureCredential`.
The pipeline chains user input through the researcher agent, sends the generated report to the validator agent for audit, passes the validated report to the file generator agent, compiles a polished PDF report artifact, tracks granular timings and token consumption across all steps, and emits detailed logs and metadata summaries.

## Scope
- In scope:
  - Create directory `azure_agents_pipeline/` at repository root.
  - Core orchestration script (`azure_agents_pipeline/run_pipeline.py`) supporting CLI arguments (`--input`, `--ticker`, `--endpoint`, `--output-dir`, `--interactive`).
  - Agent connector module (`azure_agents_pipeline/pipeline.py`) implementing sequential conversations with Azure AI Foundry preview endpoints using `project_client.get_openai_client(agent_name=...)`.
  - Telemetry and token accumulator (`azure_agents_pipeline/telemetry.py`) capturing per-step duration, input tokens, output tokens, total tokens, conversation IDs, and response IDs.
  - PDF document compiler (`azure_agents_pipeline/pdf_compiler.py`) converting markdown/text output into an executive PDF using ReportLab with tables, styles, and page numbering.
  - Configuration and credential loader (`azure_agents_pipeline/config.py`) loading `.env` variables and configuring `DefaultAzureCredential`.
  - Comprehensive unit tests in `backend/test_azure_agents_pipeline.py` verifying chaining logic, telemetry math, token calculation, and PDF artifact generation.
  - Documentation and credentials instructions for Entra ID authentication.
- Out of scope:
  - Modifying existing workflow endpoints in `backend/app/workflows/do_risk_report/`.

## Current behavior
The existing repository uses a modular LLM role router and local tools (`backend/app/workflows/do_risk_report/`). There is no dedicated script connecting directly to the Azure AI Foundry preview agent endpoints (`DO-researcher`, `DO-validator`, `DO-report-generator`) via `azure-ai-projects` and `DefaultAzureCredential`.

## Proposed behavior
1. A dedicated executable package in `azure_agents_pipeline/` provides a standalone entry point.
2. Step 1 (`DO-researcher`): Receives initial prompt/ticker, initiates a preview conversation, and retrieves the initial D&O research report.
3. Step 2 (`DO-validator`): Receives the researcher's output in a dedicated conversation, runs adversarial validation, and produces the audited report.
4. Step 3 (`DO-report-generator`): Receives the validated report, formats executive presentation blocks, and provides file generation instructions.
5. Step 4 (PDF Compilation & Telemetry Output): Emits a PDF artifact into `artifacts/`, writes complete telemetry JSON, and outputs a formatted terminal summary displaying timings, token counts, and file locations.

## Implementation steps
1. Create `azure_agents_pipeline/config.py` for project endpoint and credential management.
2. Create `azure_agents_pipeline/telemetry.py` for step timing, token aggregation, and metadata recording.
3. Create `azure_agents_pipeline/pdf_compiler.py` for generating formatted PDF documents via ReportLab.
4. Create `azure_agents_pipeline/pipeline.py` implementing the 3-agent orchestration with preview conversations.
5. Create `azure_agents_pipeline/run_pipeline.py` CLI entrypoint with formatted reporting.
6. Create `azure_agents_pipeline/README.md` with execution and credentials instructions.
7. Add automated unit tests in `backend/test_azure_agents_pipeline.py`.
8. Document decisions in `docs/decisions/azure-foundry-agent-trio-pipeline/decisions.md`.
9. Update `CHANGELOG.md`.

## Files to change / create
| File | Change | Reason |
| ---- | ------ | ------ |
| `azure_agents_pipeline/config.py` | Create | Configuration, environment loading, and credential defaults |
| `azure_agents_pipeline/telemetry.py` | Create | Tracking step timings, tokens, and metadata |
| `azure_agents_pipeline/pdf_compiler.py` | Create | High-quality PDF document generation via ReportLab |
| `azure_agents_pipeline/pipeline.py` | Create | 3-agent Foundry workflow coordinator |
| `azure_agents_pipeline/run_pipeline.py` | Create | CLI executable entrypoint |
| `azure_agents_pipeline/README.md` | Create | User manual and authentication guide |
| `backend/test_azure_agents_pipeline.py` | Create | Unit test suite verifying agent chaining and telemetry |
| `docs/features/azure-foundry-agent-trio-pipeline/*` | Create | Required feature documentation |
| `docs/decisions/azure-foundry-agent-trio-pipeline/decisions.md` | Create | Key architecture decisions |
| `CHANGELOG.md` | Update | Changelog tracking |

## Risks and mitigations
| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| `DefaultAzureCredential` fails if no Entra ID environment variables or Azure CLI token exists | Script fails to connect to Azure Foundry | Document exact credentials needed (`AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` or `az login`), provide `--interactive` browser login fallback, and emit helpful diagnostic guidance |
| Agent output exceeds single-turn token limits | Truncated report | Response token tracking surfaces limits; orchestrator logs output length |
| Agent returns text instead of raw PDF bytes | File cannot be saved directly as PDF | `pdf_compiler.py` parses agent output and compiles a structured PDF with ReportLab |

## Verification
- Unit test suite: `backend/venv/Scripts/python.exe -m unittest backend.test_azure_agents_pipeline`
- Syntax verification: `backend/venv/Scripts/python.exe -m py_compile azure_agents_pipeline/*.py`
