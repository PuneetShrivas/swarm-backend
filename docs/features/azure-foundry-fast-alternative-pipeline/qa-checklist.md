# QA Checklist: Azure Foundry Fast Alternative Pipeline

## Datetime
`2026-11-04T17:45:22+05:30`

- [x] `azure_agents_pipeline/config.py` provides direct model endpoint and default model names.
- [x] `azure_agents_pipeline/fast_pipeline.py` implements DO-researcher querying with company name.
- [x] `azure_agents_pipeline/fast_pipeline.py` implements Pathway 1 directly to `DO-report-generator`.
- [x] `azure_agents_pipeline/fast_pipeline.py` implements Pathway 2 directly calling an Azure Foundry model.
- [x] Both pathways compile styled PDF reports and record tokens and duration.
- [x] `azure_agents_pipeline/run_fast_pipeline.py` provides `--mode both|agent|direct` CLI interface.
- [x] Unit tests pass in `backend/test_azure_fast_pipeline.py`.
- [x] Existing tests in `backend/test_azure_agents_pipeline.py` and `backend/test_do_risk_report.py` pass without regressions.
- [x] Python syntax passes `py_compile`.
- [x] `CHANGELOG.md` is updated.
