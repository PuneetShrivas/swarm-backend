# Feature: Azure Foundry Fast Alternative Pipeline (Researcher → Report Generator & Direct Model)

## Datetime
`2026-11-04T17:45:22+05:30`

## Status
Approved

## Goal
Create an alternative pipeline within the Azure AI Foundry resources (`azure_agents_pipeline/`) where a target company name/input is sent to `DO-researcher`, and its output is routed through two parallel/selectable fast pathways:
1. **Direct Agent Pathway**: Sent directly to `DO-report-generator` (bypassing the validator agent for fast turnaround).
2. **Direct Model Pathway**: Sent directly to an Azure Foundry model (`claude-sonnet-4-6` or `claude-opus-4-8` via direct messages API) to generate a high-speed underwriting report.
The pipeline tracks timings, token usage, comparative metrics, and compiles publication-ready PDF reports for both outputs.

## Scope
- In scope:
  - Add configuration for direct Azure Foundry model endpoint and model choices in `azure_agents_pipeline/config.py`.
  - Implement `azure_agents_pipeline/fast_pipeline.py` providing:
    - Step 1: Query `DO-researcher` with company name / user input.
    - Pathway 1: Route researcher response directly to `DO-report-generator` agent turn.
    - Pathway 2: Route researcher response directly to Azure Foundry deployed model (`claude-sonnet-4-6` / `claude-opus-4-8`) for rapid report synthesis.
    - Support modes: `--mode both` (concurrently executes both and compares), `--mode agent` (only `DO-report-generator`), `--mode direct` (only direct model).
  - Enhance `azure_agents_pipeline/telemetry.py` to support comparative telemetry, speedup ratios, and multi-artifact tracking.
  - Generate formatted PDF reports for both outputs using `ReportPdfCompiler`.
  - CLI script `azure_agents_pipeline/run_fast_pipeline.py` with full argument parsing and formatted comparative summary table.
  - Comprehensive unit test suite in `backend/test_azure_fast_pipeline.py`.
  - Document architectural decisions in `docs/decisions/azure-foundry-fast-alternative-pipeline/decisions.md`.
  - Update `CHANGELOG.md`.
- Out of scope:
  - Modifying the full 3-agent pipeline (`run_pipeline.py`).

## Current behavior
The standard pipeline (`run_pipeline.py`) routes sequentially through all three agents: `DO-researcher` → `DO-validator` → `DO-report-generator`. There is no streamlined fast-path bypassing validation or comparing against direct model synthesis on the same resource.

## Proposed behavior
1. `run_fast_pipeline.py` sends the company name to `DO-researcher`.
2. As soon as `DO-researcher` responds:
   - Branch 1: Calls `DO-report-generator` agent via preview conversation API.
   - Branch 2: Calls direct Azure Foundry model (`claude-sonnet-4-6` or `claude-opus-4-8`) with executive D&O underwriting report synthesis instructions.
3. Both branches can run asynchronously via `asyncio.gather` (or synchronously if preferred).
4. Both generated reports are compiled into styled PDFs:
   - `DO_Risk_Report_<TICKER>_fast_agent.pdf`
   - `DO_Risk_Report_<TICKER>_fast_direct.pdf`
5. Telemetry logs comparative metrics:
   - Duration of Researcher vs Agent Generator vs Direct Model
   - Tokens consumed per branch
   - Time savings / speedup comparison
   - Output file locations.

## Implementation steps
1. Update `azure_agents_pipeline/config.py` with direct model endpoint and default model settings.
2. Update `azure_agents_pipeline/telemetry.py` with comparative telemetry metrics.
3. Create `azure_agents_pipeline/fast_pipeline.py` implementing the dual-path fast orchestration.
4. Create `azure_agents_pipeline/run_fast_pipeline.py` CLI entrypoint.
5. Update `azure_agents_pipeline/__init__.py` and `azure_agents_pipeline/README.md`.
6. Add unit tests in `backend/test_azure_fast_pipeline.py`.
7. Verify all checks and tests pass with 0 regressions.
8. Update `docs/features/azure-foundry-fast-alternative-pipeline/` files and `CHANGELOG.md`.

## Files to change / create
| File | Change | Reason |
| ---- | ------ | ------ |
| `azure_agents_pipeline/config.py` | Update | Add direct model endpoint, model defaults, API key |
| `azure_agents_pipeline/telemetry.py` | Update | Add comparative metrics support |
| `azure_agents_pipeline/fast_pipeline.py` | Create | Fast alternative pipeline implementation |
| `azure_agents_pipeline/run_fast_pipeline.py` | Create | Fast alternative pipeline CLI executable |
| `azure_agents_pipeline/__init__.py` | Update | Export fast pipeline components |
| `azure_agents_pipeline/README.md` | Update | Document fast pipeline usage and comparison flags |
| `backend/test_azure_fast_pipeline.py` | Create | Unit test suite for fast pipeline |
| `docs/features/azure-foundry-fast-alternative-pipeline/*` | Create | Feature lifecycle documentation |
| `docs/decisions/azure-foundry-fast-alternative-pipeline/decisions.md` | Create | Architecture decisions |
| `CHANGELOG.md` | Update | Changelog entry |

## Risks and mitigations
| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Bypassing validator agent might preserve raw research inconsistencies | Less audited findings | Documented as an intentional high-speed alternative mode; prompts instruct generator to maintain consistency |
| Direct model call rate limits | HTTP 429 | Retry logic with exponential backoff and fallback model support |
| Concurrent execution running out of memory/tokens | Failed runs | Bounded execution with clear exception handling and independent error traps |

## Verification
- Unit test suite: `$env:PYTHONPATH=".;backend"; backend\venv\Scripts\python.exe -m unittest backend.test_azure_fast_pipeline`
- Syntax check: `backend\venv\Scripts\python.exe -m py_compile azure_agents_pipeline/*.py`
