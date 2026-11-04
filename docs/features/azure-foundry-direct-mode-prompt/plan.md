# Feature: Azure Foundry Direct Mode Comprehensive Underwriter Prompt

## Datetime
`2026-11-04T18:22:00+05:30`

## Status
In progress

## Goal
Configure the Azure AI Foundry fast alternative pipeline direct model execution pathway (`fast_pipeline.py`) to send the user's standardized 13-section D&O Underwriting Report structure and content prompt (`# D&O UNDERWRITING REPORT — STRUCTURE AND CONTENT INSTRUCTIONS...`) directly to the Azure Foundry model endpoint (`claude-sonnet-4-6` / `claude-opus-4-8`), transforming the researcher evidence base into an executive underwriting report.

## Scope
- In scope:
  - Create `azure_agents_pipeline/prompts.py` defining `DIRECT_REPORT_PROMPT` containing the verbatim 13-section D&O underwriting specification.
  - Update `azure_agents_pipeline/fast_pipeline.py`:
    - Inject `DIRECT_REPORT_PROMPT` into `_execute_direct_model` system instructions and user evidence payload.
    - Support optional custom prompt override via constructor `direct_model_prompt` and CLI `--prompt-file`.
    - Enhance REST authentication with fallback to Entra ID bearer token via `get_bearer_token_provider(..., "https://ai.azure.com/.default")` when `AZURE_API_KEY` is absent.
  - Export `DIRECT_REPORT_PROMPT` from `azure_agents_pipeline/__init__.py`.
  - Update `azure_agents_pipeline/run_fast_pipeline.py` CLI to support optional `--prompt-file`.
  - Add unit tests in `backend/test_azure_fast_pipeline.py` verifying that `_execute_direct_model` sends `DIRECT_REPORT_PROMPT` in the payload.
  - Maintain feature documentation in `docs/features/azure-foundry-direct-mode-prompt/` and architectural decision in `docs/decisions/azure-foundry-direct-mode-prompt/decisions.md`.
  - Update `CHANGELOG.md`.
- Out of scope:
  - Modifying the 3-agent pipeline (`run_pipeline.py`).

## Current behavior
`_execute_direct_model` in `azure_agents_pipeline/fast_pipeline.py` used a short 5-header placeholder synthesis prompt (`### 1. EXECUTIVE SUMMARY & VERDICT...`), rather than the comprehensive 13-section senior underwriter specification.

## Proposed behavior
1. `azure_agents_pipeline/prompts.py` stores the full 13-section prompt verbatim:
   - Global formatting rules (bullet points, risk tiers: Contained / Elevated / High-Volatility / Severe Tail Exposure).
   - Section 1: Executive Summary
   - Section 2: Company Snapshot (with CPI, listings, share price, assets, revenue, AI exposure)
   - Section 3: Updates / Press Releases / News (chronological, max 12 items, strict format)
   - Section 4: Financial Overview & Debt/Refinancing Profile
   - Section 5: Analysts & Sentiment
   - Section 6: Governance & Culture
   - Section 7: Director & Officer History (mandatory 4 roles + discretionary, historical horizon)
   - Section 8: Strategic & Operational Profile
   - Section 9: Securities Class Action Risk (Bands for Likelihood, Severity, Side A/C, Scenario)
   - Section 10: Legal, Regulatory & Claims Context
   - Section 11: ESG, Cyber & Operational Exposure
   - Section 12: Forward-Looking Strategic Risk
   - Section 13: Overall D&O Underwriter Verdict & Band Register
   - Closing Statement: "Assessment based solely on information contained in this report."
2. When `_execute_direct_model` is invoked in `fast_pipeline.py`, this prompt is passed as the system instruction to Azure Foundry (`claude-sonnet-4-6` with fallback to `claude-opus-4-8`).
3. The raw findings from `DO-researcher` are passed as the user turn evidence base.

## Implementation steps
1. Create `azure_agents_pipeline/prompts.py` containing `DIRECT_REPORT_PROMPT`.
2. Update `azure_agents_pipeline/fast_pipeline.py` to use `DIRECT_REPORT_PROMPT` and support custom prompt parameter.
3. Update `azure_agents_pipeline/run_fast_pipeline.py` with `--prompt-file` option.
4. Export `DIRECT_REPORT_PROMPT` in `azure_agents_pipeline/__init__.py`.
5. Update `backend/test_azure_fast_pipeline.py` with unit tests checking prompt propagation.
6. Verify test execution.
7. Update implementation, verification, and QA checklist docs.
8. Commit and push.

## Files to change / create
| File | Change | Reason |
| ---- | ------ | ------ |
| `azure_agents_pipeline/prompts.py` | Create | Store verbatim 13-section underwriter prompt |
| `azure_agents_pipeline/fast_pipeline.py` | Modify | Use `DIRECT_REPORT_PROMPT` in `_execute_direct_model` |
| `azure_agents_pipeline/run_fast_pipeline.py` | Modify | Allow `--prompt-file` override |
| `azure_agents_pipeline/__init__.py` | Modify | Export `DIRECT_REPORT_PROMPT` |
| `backend/test_azure_fast_pipeline.py` | Modify | Add unit tests for prompt injection |
| `docs/features/azure-foundry-direct-mode-prompt/*` | Create | Feature lifecycle documentation |
| `docs/decisions/azure-foundry-direct-mode-prompt/*` | Create | Architectural decision records |
| `CHANGELOG.md` | Modify | Document the enhancement |
