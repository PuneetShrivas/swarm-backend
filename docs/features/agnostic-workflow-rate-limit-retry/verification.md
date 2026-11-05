# Verification Report: Agnostic Workflow Azure Rate Limit (HTTP 429) Retry & Non-Skipping Recovery

## Datetime
`2026-11-05T13:42:15+05:30`

## Scope of Verification
Verifying that Azure Foundry HTTP 429 rate limit errors (such as output token TPM rate limit: `"Rate limit of 8000 per 60s exceeded for UserByModelByMinuteOutputTokens. Please wait 8 seconds before retrying."`) are dynamically parsed, gracefully waited out via backoff and cooldown, and retried without skipping sections in the final generated report.

## Automated Test Results

Test runner: `backend/venv/Scripts/python.exe -m unittest backend/test_agnostic_research_report.py -v`

```text
test_orchestrator_section_draft_retry_recovers (backend.test_agnostic_research_report.TestAgnosticRateLimitRetry.test_orchestrator_section_draft_retry_recovers)
Verifies that orchestrator _process_section retries on transient draft failure and succeeds. ... [*] [SECTION DRAFT RETRY] Section 'Test Section' drafting encountered error (Azure Foundry HTTP 429: Rate limit exceeded). Waiting 15s before retry (attempt 2/3)...
ok
test_parse_retry_delay (backend.test_agnostic_research_report.TestAgnosticRateLimitRetry.test_parse_retry_delay) ... ok
test_roles_retry_on_429 (backend.test_agnostic_research_report.TestAgnosticRateLimitRetry.test_roles_retry_on_429)
Simulates a 429 rate limit error followed by success. ... [RATE LIMIT 429] Role 'draft' hit rate limit on 'claude-opus-4-8'. Failing over to fallback model 'claude-sonnet-4-6'...
[AZURE SUCCESS] Role 'draft' succeeded with model 'claude-sonnet-4-6' (round 1/2)
ok
test_models_instantiation (backend.test_agnostic_research_report.TestAgnosticResearchReportStep1.test_models_instantiation)
Verifies dataclass creation and serialization. ... ok
test_spec_parser_custom_markdown (backend.test_agnostic_research_report.TestAgnosticResearchReportStep1.test_spec_parser_custom_markdown)
Verifies MarkdownSpecParser on arbitrary custom markdown structure. ... ok
test_spec_parser_standard_template (backend.test_agnostic_research_report.TestAgnosticResearchReportStep1.test_spec_parser_standard_template)
Verifies MarkdownSpecParser parses the standard research template accurately. ... ok
test_ledger_sequential_id_and_citation_resolution (backend.test_agnostic_research_report.TestAgnosticResearchReportStep2.test_ledger_sequential_id_and_citation_resolution)
Verifies ledger adds items with E001, E002, resolves citations, and produces stats. ... ok
test_result_compactor (backend.test_agnostic_research_report.TestAgnosticResearchReportStep2.test_result_compactor)
Verifies cleaning snippets and deduplicating syndicated articles. ... ok
test_search_queue_live_strict_credentials_enforcement (backend.test_agnostic_research_report.TestAgnosticResearchReportStep2.test_search_queue_live_strict_credentials_enforcement)
Verifies that in live mode (no mock flags), missing PERPLEXITY_API_KEY raises RuntimeError. ... ok
test_search_queue_mock_batch (backend.test_agnostic_research_report.TestAgnosticResearchReportStep2.test_search_queue_mock_batch)
Verifies PerplexitySearchQueue batch retrieval under test mock conditions. ... ok
test_execute_azure_chat_with_tokens_mock (backend.test_agnostic_research_report.TestAgnosticResearchReportStep3.test_execute_azure_chat_with_tokens_mock)
Verifies _execute_azure_chat_with_tokens properly parses content and usage. ... ok
test_extract_json_resilience (backend.test_agnostic_research_report.TestAgnosticResearchReportStep3.test_extract_json_resilience)
Verifies _extract_json parses thinking blocks, markdown fences, and trailing commas. ... ok
test_provider_configuration (backend.test_agnostic_research_report.TestAgnosticResearchReportStep3.test_provider_configuration)
Verifies setting active provider and fallback model. ... ok
test_run_role_mock_with_tokens (backend.test_agnostic_research_report.TestAgnosticResearchReportStep3.test_run_role_mock_with_tokens)
Verifies run_role yields 4-tuple with parsed payload and token usage. ... ok
test_footnote_transformer (backend.test_agnostic_research_report.TestAgnosticResearchReportStep4.test_footnote_transformer)
Verifies [E###] citation replacement and footnote dictionary assembly. ... ok
test_markdown_and_pdf_renderers (backend.test_agnostic_research_report.TestAgnosticResearchReportStep4.test_markdown_and_pdf_renderers)
Verifies Markdown and ReportLab PDF file generation with NumberedCanvas. ... ok
test_orchestrator_end_to_end_mock (backend.test_agnostic_research_report.TestAgnosticResearchReportStep4.test_orchestrator_end_to_end_mock)
Verifies AgnosticResearchOrchestrator runs multi-stage workflow in mock test environment. ... ok
test_cli_argument_parsing (backend.test_agnostic_research_report.TestAgnosticResearchReportStep5.test_cli_argument_parsing)
Verifies CLI argument parser flags. ... ok
test_cli_execution_mock (backend.test_agnostic_research_report.TestAgnosticResearchReportStep5.test_cli_execution_mock)
Verifies execute_cli completes cleanly with mock environment. ... ok
test_render_tree_and_table (backend.test_agnostic_research_report.TestAgnosticResearchReportStep5.test_render_tree_and_table)
Verifies render_tree and render_table produce formatted ASCII displays. ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.310s

OK
```

## Summary of Verification Checks

| Scenario | Expected Outcome | Actual Outcome | Status |
|---|---|---|---|
| HTTP 429 delay string extraction | Parses `"Please wait 8 seconds before retrying."` and adds `+2.0s` safety buffer | Computed `10.0s` | PASS |
| Transient 429 during `run_role` | Retries and recovers without raising | Recovers on attempt 2 | PASS |
| Transient failure during section drafting | Retries drafting instead of writing `- Section drafting unavailable due to upstream error` | Section contains analytical draft | PASS |
| End-to-end workflow execution | Compiles all sections into Markdown & PDF with telemetry | All artifacts generated successfully | PASS |
