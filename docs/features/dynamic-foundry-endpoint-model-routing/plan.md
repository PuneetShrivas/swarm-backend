# Feature: Dynamic Azure Foundry Endpoint Routing for GPT-5.4 and GPT-5-Mini

## Datetime
`2026-11-05T15:23:45+05:30`

## Status
Completed

## Goal
Enable dynamic Azure Foundry endpoint switching across both instances of the agnostic workflow (`backend/app/workflows/agnostic_research_report/` and `agnostic_workflow/`):
- When `gpt-5.4` or `gpt-5-mini` is selected as the model, route requests to:
  `AZURE_FOUNDRY_ENDPOINT="https://puneetshrivas32-0871-resource.services.ai.azure.com/openai/v1/messages"`
- When Anthropic models (e.g. `claude-opus-4-8`, `claude-sonnet-4-6`) are selected, retain:
  `AZURE_FOUNDRY_ENDPOINT="https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages"`

## Scope
- In scope:
  - `backend/app/workflows/agnostic_research_report/roles.py`:
    - Implement `is_openai_foundry_model()` and `resolve_foundry_endpoint()` helper functions.
    - Update `_execute_azure_chat_with_tokens()` to use `resolve_foundry_endpoint(model)`.
    - Enhance response parsing to support both Anthropic `content` blocks and OpenAI `choices` structures and dual token usage keys (`input_tokens`/`prompt_tokens`, `output_tokens`/`completion_tokens`).
  - `agnostic_workflow/roles.py`:
    - Implement identical model-aware endpoint routing and response parsing while preserving zero dependencies on `backend/app/*`.
  - `backend/test_agnostic_research_report.py`:
    - Add unit tests verifying dynamic endpoint resolution for `gpt-5.4`, `gpt-5-mini`, and `claude-*` models.
  - `agnostic_workflow/test_standalone_workflow.py`:
    - Add standalone unit tests verifying endpoint switching and response parsing compatibility.
  - `agnostic_workflow.zip`:
    - Re-pack standalone zip distribution with updated endpoint routing.
  - Documentation & Changelog:
    - Feature lifecycle docs, decision record, and Keep a Changelog update.
- Out of scope:
  - Changing non-agnostic workflows (e.g. `do_risk_report` or `azure_agents_pipeline`).

## Current behavior
Both agnostic workflow instances hardcode or default to:
`https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages`
even if `gpt-5.4` or `gpt-5-mini` is passed via `--model` or configured in environment variables.

## Proposed behavior
Both instances dynamically inspect the target `model` name. If `gpt-5.4` or `gpt-5-mini` is selected, the Azure Foundry endpoint automatically switches to:
`https://puneetshrivas32-0871-resource.services.ai.azure.com/openai/v1/messages`
even if `AZURE_FOUNDRY_ENDPOINT` was set to the Anthropic messages URL in `.env`.

## Implementation steps
1. Create plan, implementation log, verification report, QA checklist, and decision record.
2. Update `backend/app/workflows/agnostic_research_report/roles.py`.
3. Update `agnostic_workflow/roles.py`.
4. Add unit test coverage in `backend/test_agnostic_research_report.py` and `agnostic_workflow/test_standalone_workflow.py`.
5. Execute test suites for both instances.
6. Re-pack `agnostic_workflow.zip`.
7. Update `CHANGELOG.md`.
8. Git commit and push to `origin/main`.

## Files to change
| File | Change | Reason |
|---|---|---|
| `backend/app/workflows/agnostic_research_report/roles.py` | Modify | Add `resolve_foundry_endpoint` switching to `/openai/v1/messages` for `gpt-5.4` and `gpt-5-mini` |
| `agnostic_workflow/roles.py` | Modify | Replicate dynamic endpoint resolution in standalone package |
| `backend/test_agnostic_research_report.py` | Modify | Add tests for endpoint resolution |
| `agnostic_workflow/test_standalone_workflow.py` | Modify | Add tests for standalone endpoint resolution |
| `agnostic_workflow.zip` | Re-generate | Keep standalone zip archive in sync |
| `docs/decisions/dynamic-foundry-endpoint-model-routing/decisions.md` | Create | Architecture decisions |
| `docs/features/dynamic-foundry-endpoint-model-routing/*` | Create | Feature lifecycle documentation |
| `CHANGELOG.md` | Modify | Document dynamic model routing update |

## Verification
- Unit test verification in both test suites.
- Regression verification.
