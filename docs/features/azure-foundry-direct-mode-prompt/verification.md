# Verification: Azure Foundry Direct Mode Comprehensive Underwriter Prompt

## Datetime
`2026-11-04T18:22:00+05:30`

## Summary of Verification Activities

### 1. Automated Test Suite Execution
- **Command**: `backend\venv\Scripts\python.exe -m unittest backend.test_azure_fast_pipeline backend.test_azure_agents_pipeline`
- **Output**:
  ```text
  Ran 13 tests in 0.446s
  OK
  ```
- **Tests Verified**:
  1. `test_execute_direct_model_uses_underwriter_prompt`: Asserts that `_execute_direct_model` transmits `# D&O UNDERWRITING REPORT — STRUCTURE AND CONTENT INSTRUCTIONS`, all 13 sections, and the closing statement verbatim into the Anthropic messages `system` parameter.
  2. `test_custom_prompt_override`: Asserts that a custom prompt passed to constructor overrides the default prompt cleanly.
  3. `test_bearer_token_provider_fallback`: Asserts that when `AZURE_API_KEY` is not set, the pipeline dynamically fetches a bearer token from `azure.identity.get_bearer_token_provider` for the REST call.
  4. `test_fast_pipeline_mode_both_execution`: Asserts dual PDF artifacts (`_fast_agent.pdf` and `_fast_direct.pdf`) are compiled.
  5. `test_fast_pipeline_mode_agent_only`: Asserts only agent artifacts are compiled.
  6. `test_fast_pipeline_mode_direct_only`: Asserts only direct model artifacts are compiled.
  7. `test_run_fast_pipeline_cli_parsing`: Asserts `--prompt-file`, `--mode`, and `--model` flags parse cleanly.

### 2. Manual CLI Verification
- Evaluated `--help` output of `azure_agents_pipeline/run_fast_pipeline.py` confirming `--prompt-file` parameter is documented.
