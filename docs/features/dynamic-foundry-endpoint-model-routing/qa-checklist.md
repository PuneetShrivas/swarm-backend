# QA Checklist: Dynamic Azure Foundry Endpoint Routing for GPT-5.4 and GPT-5-Mini

## Datetime
`2026-11-05T15:29:05+05:30`

## Pre-Release QA Checks

- [x] **Model Detection Accuracy**:
  - `is_openai_foundry_model` matches `gpt-5.4` and `gpt-5-mini` (case-insensitive).
  - Handles variants with prefix/whitespace.
  - Returns `False` for Anthropic models (`claude-opus-4-8`, `claude-sonnet-4-6`).
- [x] **Endpoint Routing Transformation**:
  - Automatically targets `https://puneetshrivas32-0871-resource.services.ai.azure.com/openai/v1/messages` for `gpt-5.4` and `gpt-5-mini`.
  - Replaces `/anthropic/` with `/openai/` if a user's `.env` specifies the Anthropic endpoint.
  - Automatically targets `https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages` for Claude models.
- [x] **Response & Usage Parsing Robustness**:
  - Parses Anthropic `content` blocks.
  - Parses OpenAI `choices` blocks as fallback.
  - Supports `input_tokens` / `prompt_tokens` and `output_tokens` / `completion_tokens`.
- [x] **Both Instances Updated**:
  - `backend/app/workflows/agnostic_research_report/roles.py` updated.
  - `agnostic_workflow/roles.py` updated.
- [x] **Zero App Dependencies Invariant**:
  - Verified `0` imports of `app.*` in `agnostic_workflow/`.
- [x] **Automated Test Coverage**:
  - 14/14 tests pass in `agnostic_workflow/test_standalone_workflow.py`.
  - 21/21 tests pass in `backend/test_agnostic_research_report.py`.
- [x] **Distribution Package Updated**:
  - `agnostic_workflow.zip` repacked with updated modules.
- [x] **Documentation Integrity**:
  - Feature plan, implementation log, verification report, and QA checklist completed with datetimes.
  - Architecture decisions recorded in `docs/decisions/dynamic-foundry-endpoint-model-routing/decisions.md`.
