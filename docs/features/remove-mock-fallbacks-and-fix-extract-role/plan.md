# Feature: Remove Mock Fallbacks and Fix Extract Role

## Datetime
`2026-11-04T15:25:00+05:30`

## Status
Approved

## Goal
1. Eliminate all mock and synthetic data fallbacks across the report generation pipeline so that no fake or mock disclosures are ever injected into the Evidence Ledger or final generated D&O risk report.
2. Fix the runtime failure of the `extract` role when executing via Azure Foundry (`claude-sonnet-4-6`), resolving issues in multi-block Anthropic content extraction, thinking block stripping, JSON parse handling, retry logic, and orchestrator fault tolerance.

## Scope
- In scope:
  - Purging synthetic and mock data fallbacks from `edgar.py` (`fetch_submissions`, `fetch_company_facts`, `resolve_cik`).
  - Disabling silent fallback to `_generate_mock_results` in `retrieval.py` when running live report generation (`TESTING != 'true'`).
  - Disabling silent fallback to `_generate_mock_role_output` in `roles.py` when running live report generation.
  - Updating `_execute_azure_chat` in `roles.py` to aggregate all text content blocks and properly surface Azure API error payloads.
  - Enhancing `_extract_json_from_llm_response` to strip thinking tags (`<thinking>...</thinking>`), tolerate conversational wrappers, and normalize top-level arrays into `{"items": [...]}`.
  - Fixing `roles.py` retry logic when JSON parsing returns empty/fails: recording a descriptive error, retrying with backoff, failing over to fallback models, and marking parse errors as retryable.
  - Increasing `max_tokens` for the `extract` role from 2500 to 4000 to prevent JSON truncation on multi-item extraction.
  - Adding defensive exception handling in `orchestrator.py` around section extraction and gap checks so failures degrade gracefully without crashing the whole report.
  - Updating automated unit tests to verify zero mock data injection in production mode and resilient JSON parsing.
- Out of scope:
  - Running live end-to-end report generation tests directly (per explicit user instruction: the user will run this test).

## Current behavior
1. When SEC EDGAR API requests fail or time out, `edgar.py` returns a hardcoded mock Apple payload (Cupertino, CA, One Apple Park Way, $383B revenue, $352B assets), injecting Apple's data into reports for other companies (e.g. NVDA).
2. When Perplexity search API key is unconfigured or search fails, `retrieval.py` silently returns synthetic mock litigation and regulatory snippets.
3. In `roles.py`, `_execute_azure_chat` inspects only `content_items[0].get("text", "")`. If the response contains thinking blocks or multiple blocks, it returns an empty string `""`.
4. If `_extract_json_from_llm_response` encounters thinking tags or fails to parse, it returns `{}`. In `run_role`, `if parsed:` evaluates to `False`, immediately executing `break` without populating `last_azure_error`, which aborts the retry loop with an empty error message:
   `RuntimeError: Role 'extract' Azure Foundry execution failed across models ['claude-sonnet-4-6'] after 5 retry rounds:`
5. In `orchestrator.py`, `run_role("extract", user_prompt)` is not wrapped in exception handling, crashing the entire report on any unhandled role failure.

## Proposed behavior
1. Live Report Integrity (Zero Mock Fallbacks):
   - In `edgar.py`, failed network requests return `{}` rather than synthetic Apple filings. `resolve_cik` returns `""` if unresolvable rather than a random hash.
   - In `retrieval.py`, if `PERPLEXITY_API_KEY` is missing in live mode (`TESTING != "true"`), raise `RuntimeError("PERPLEXITY_API_KEY is not configured or invalid.")` instead of generating synthetic search items.
   - In `roles.py`, live report generation never invokes `_generate_mock_role_output`. If credentials or execution fails, raise clear, actionable runtime errors.
2. Robust Anthropic & Azure Role Execution:
   - In `_execute_azure_chat`, loop over all items in `data.get("content", [])` and concatenate all text blocks. Check for error payloads.
   - In `_extract_json_from_llm_response`, remove `<thinking>...</thinking>` blocks, support fenced and unfenced JSON, and normalize top-level arrays into `{"items": [...]}`.
   - If parsing fails, assign `last_azure_error`, log the failure note, retry across attempts, and fail over to the secondary model.
   - Expand `is_retryable` keywords to include JSON parse errors.
   - In `orchestrator.py`, wrap `run_role("extract", ...)` and `run_role("gap", ...)` in defensive try-except blocks so that any extraction failure logs a warning and allows the report to continue using authoritative SEC filing evidence.

## Implementation steps
1. Update `backend/app/workflows/do_risk_report/edgar.py` to remove mock submissions, mock facts, and synthetic CIK generation in live mode.
2. Update `backend/app/workflows/do_risk_report/retrieval.py` to forbid mock search results when not running in explicit test mode with mock allowance.
3. Update `backend/app/workflows/do_risk_report/roles.py`:
   - Enhance `_execute_azure_chat` to aggregate all text blocks and check error fields.
   - Enhance `_extract_json_from_llm_response` to strip thinking blocks, handle arrays, and repair minor JSON issues.
   - Fix Azure retry loop: record parse failure error, retry across attempts, fail over on unparseable responses, and mark parse failures retryable.
   - Increase `extract` role `max_tokens` to 4000.
   - Ensure live mode never falls back to `_generate_mock_role_output`.
4. Update `backend/app/workflows/do_risk_report/orchestrator.py` to wrap `extract` and `gap` role executions defensively.
5. Add comprehensive unit tests in `backend/test_do_risk_report.py` covering text aggregation, thinking block stripping, array normalization, and zero mock fallback enforcement.
6. Run unit tests (`TESTING="true"`) to verify zero regressions.
7. Record implementation, decisions, verification, qa-checklist, and changelog.

## Files to change
| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/do_risk_report/edgar.py` | Remove mock submissions and facts fallbacks; eliminate synthetic CIK hash | Stop injecting Apple or synthetic data into the Evidence Ledger |
| `backend/app/workflows/do_risk_report/retrieval.py` | Require live API key in production; prevent silent mock results | Stop injecting synthetic search snippets into live reports |
| `backend/app/workflows/do_risk_report/roles.py` | Fix Azure text block aggregation, thinking block stripping, parse error retries, max_tokens | Fix empty error and failure on role 'extract' |
| `backend/app/workflows/do_risk_report/orchestrator.py` | Wrap extraction and gap checks in defensive try-except blocks | Prevent pipeline crash on role extraction glitches |
| `backend/test_do_risk_report.py` | Add unit tests for zero mock fallbacks and robust Anthropic response extraction | Verify fixes and guard against regressions |
| `docs/features/remove-mock-fallbacks-and-fix-extract-role/*` | Feature documentation | Mandatory development process |
| `docs/decisions/remove-mock-fallbacks-and-fix-extract-role/decisions.md` | Architecture decisions | Mandatory development process |
| `CHANGELOG.md` | Log entry | Definition of done |

## Risks and mitigations
| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Unit tests failing because they expect mock role output | Tests break during CI | Maintain `TESTING == "true"` allowance strictly for unit tests while disallowing mock data in live execution |
| SEC EDGAR rate limit causing empty filing metrics | Report has fewer financial items | Underwriter guide Rule 3 correctly notes "Not found in public disclosures" instead of hallucinating fake numbers |
| LLM returns text with extra commentary | JSON parse failure | Regex extraction and thinking block stripping cleanly isolate JSON payload |

## Verification
- Unit tests: `backend/venv/Scripts/python.exe -m unittest backend.test_do_risk_report`
- Syntax check: `python -m py_compile backend/app/workflows/do_risk_report/*.py`
