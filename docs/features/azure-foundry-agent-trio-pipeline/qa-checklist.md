# QA Checklist: Azure Foundry Three-Agent Pipeline

## Datetime
`2026-11-04T16:48:00+05:30`

- [x] Directory `azure_agents_pipeline/` created at root.
- [x] `azure_agents_pipeline/config.py` loads default endpoint, agent names, and environment variables.
- [x] `azure_agents_pipeline/telemetry.py` tracks timings, input/output/total tokens, and response IDs.
- [x] `azure_agents_pipeline/pdf_compiler.py` converts report output into a PDF artifact.
- [x] `azure_agents_pipeline/pipeline.py` executes `DO-researcher` -> `DO-validator` -> `DO-report-generator`.
- [x] `azure_agents_pipeline/run_pipeline.py` CLI provides command-line flags and summary logs.
- [x] User is informed about missing Entra ID credentials (`AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` or `az login`).
- [x] Unit tests pass in `backend/test_azure_agents_pipeline.py`.
- [x] Python syntax passes `py_compile`.
- [x] CHANGELOG.md is updated.
