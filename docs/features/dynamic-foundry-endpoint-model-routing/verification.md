# Verification Report: Dynamic Azure Foundry Endpoint Routing for GPT-5.4 and GPT-5-Mini

## Datetime
`2026-11-05T15:28:50+05:30`

## Scope of Verification
Verifying that both instances of the agnostic workflow (`backend/app/workflows/agnostic_research_report/` and `agnostic_workflow/`) dynamically route requests to:
- `AZURE_FOUNDRY_ENDPOINT="https://puneetshrivas32-0871-resource.services.ai.azure.com/openai/v1/messages"` when `gpt-5.4` or `gpt-5-mini` is used.
- `AZURE_FOUNDRY_ENDPOINT="https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages"` when Anthropic Claude models (e.g. `claude-opus-4-8`, `claude-sonnet-4-6`) are used.

## Automated Test Results

### 1. Standalone Package Suite (`agnostic_workflow/test_standalone_workflow.py`)
```text
test_01_zero_app_imports (__main__.TestStandaloneAgnosticWorkflow.test_01_zero_app_imports) ... ok
test_02_spec_parser_standard_markdown (__main__.TestStandaloneAgnosticWorkflow.test_02_spec_parser_standard_markdown) ... ok
test_03_spec_parser_unstructured_prompt (__main__.TestStandaloneAgnosticWorkflow.test_03_spec_parser_unstructured_prompt) ... ok
test_04_evidence_ledger_sequential_citations (__main__.TestStandaloneAgnosticWorkflow.test_04_evidence_ledger_sequential_citations) ... ok
test_05_retrieval_compactor_and_dedup (__main__.TestStandaloneAgnosticWorkflow.test_05_retrieval_compactor_and_dedup) ... ok
test_05b_perplexity_fast_search_payload (__main__.TestStandaloneAgnosticWorkflow.test_05b_perplexity_fast_search_payload) ... ok
test_06_roles_json_extraction (__main__.TestStandaloneAgnosticWorkflow.test_06_roles_json_extraction) ... ok
test_07_footnote_transformation_and_rendering (__main__.TestStandaloneAgnosticWorkflow.test_07_footnote_transformation_and_rendering) ... ok
test_08_telemetry_renderers (__main__.TestStandaloneAgnosticWorkflow.test_08_telemetry_renderers) ... ok
test_09_end_to_end_orchestrator_execution (__main__.TestStandaloneAgnosticWorkflow.test_09_end_to_end_orchestrator_execution) ... ok
test_10_rate_limit_delay_parsing (__main__.TestStandaloneAgnosticWorkflow.test_10_rate_limit_delay_parsing) ... ok
test_11_run_role_429_retry_recovery (__main__.TestStandaloneAgnosticWorkflow.test_11_run_role_429_retry_recovery) ... ok
test_12_orchestrator_section_draft_retry_recovers (__main__.TestStandaloneAgnosticWorkflow.test_12_orchestrator_section_draft_retry_recovers) ... ok
test_13_resolve_foundry_endpoint_routing (__main__.TestStandaloneAgnosticWorkflow.test_13_resolve_foundry_endpoint_routing) ... ok

----------------------------------------------------------------------
Ran 14 tests in 0.410s

OK
```

### 2. Backend Regression Suite (`backend/test_agnostic_research_report.py`)
```text
test_resolve_foundry_endpoint_routing (backend.test_agnostic_research_report.TestAgnosticRateLimitRetry.test_resolve_foundry_endpoint_routing) ... ok
...
Ran 21 tests in 0.483s

OK
```

## Summary of Verification Checks

| Scenario | Expected Outcome | Actual Outcome | Status |
|---|---|---|---|
| Model `gpt-5.4` default endpoint | Routes to `https://.../openai/v1/messages` | `https://puneetshrivas32-0871-resource.services.ai.azure.com/openai/v1/messages` | PASS |
| Model `gpt-5-mini` default endpoint | Routes to `https://.../openai/v1/messages` | `https://puneetshrivas32-0871-resource.services.ai.azure.com/openai/v1/messages` | PASS |
| Model `claude-opus-4-8` default endpoint | Routes to `https://.../anthropic/v1/messages` | `https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages` | PASS |
| Model `claude-sonnet-4-6` default endpoint | Routes to `https://.../anthropic/v1/messages` | `https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages` | PASS |
| Env var `AZURE_FOUNDRY_ENDPOINT` with `/anthropic/` converted for `gpt-5.4` | Converts `/anthropic/` to `/openai/` | Successfully converted | PASS |
| Bare host endpoint converted according to model family | Appends `/openai/v1/messages` or `/anthropic/v1/messages` | Correct path appended | PASS |
| Zero external app imports | `agnostic_workflow/` has 0 dependencies on `backend/app/*` | 0 violations | PASS |
| Zip distribution sync | `agnostic_workflow.zip` contains updated code | Repacked successfully (46,201 bytes) | PASS |
