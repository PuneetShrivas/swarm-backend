# QA Checklist: Azure Foundry Direct Mode Comprehensive Underwriter Prompt

## Datetime
`2026-11-04T18:22:00+05:30`

- [x] Standardized prompt module created under `azure_agents_pipeline/prompts.py`.
- [x] Full 13-section D&O underwriting report structure matches requested prompt verbatim.
- [x] Closing statement `"Assessment based solely on information contained in this report."` preserved.
- [x] Direct model call in `FastAzureFoundryPipeline` transmits the prompt in the `"system"` payload field.
- [x] User payload clearly segments `TARGET COMPANY` and `SUPPLIED EVIDENCE BASE`.
- [x] Authentication supports both `AZURE_API_KEY` and dynamic Entra ID Bearer token via `DefaultAzureCredential`.
- [x] Constructor and CLI `--prompt-file` support custom prompt overrides.
- [x] Unit test suite passes with zero failures or regressions (13/13 tests pass).
- [x] Architecture decision recorded in `docs/decisions/azure-foundry-direct-mode-prompt/decisions.md`.
- [x] Changelog updated in `CHANGELOG.md`.
