# Architectural Decisions: Remove Mock Fallbacks and Fix Extract Role

## Datetime
`2026-11-04T15:25:00+05:30`

## Context
During D&O risk report generation for NVDA with `--provider azure --mode standard`, two critical issues occurred:
1. Synthetic mock disclosures from `edgar.py` (Apple Cupertino address and $383B revenue) and `retrieval.py` (synthetic litigation dockets) were leaking into production reports whenever network requests failed or were throttled.
2. The pipeline aborted with:
   `RuntimeError: Role 'extract' Azure Foundry execution failed across models ['claude-sonnet-4-6'] after 5 retry rounds:` with an empty error message.

## Decisions

### 1. Zero Mock Data Policy in Live Mode
- In live execution (when `TESTING != 'true'`), the system must never generate or inject synthetic/mock data.
- If SEC EDGAR endpoints are unreachable and no cached filing exists on disk, `fetch_submissions` and `fetch_company_facts` will return empty dicts `{}`.
- If a ticker's CIK cannot be resolved from the known lookup or SEC directory, `resolve_cik` will return `""` instead of an MD5 synthetic hash.
- If `PERPLEXITY_API_KEY` is missing in live mode, `retrieval.py` will raise a descriptive `RuntimeError` rather than silently generating synthetic litigation dockets.
- If LLM credentials are missing or role execution fails in live mode, `roles.py` will raise an informative `RuntimeError` rather than synthesizing mock section text.

### 2. Multi-Block Text Aggregation for Anthropic Messages API
- Anthropic on Azure Foundry can return responses composed of multiple content blocks (e.g. thinking blocks, text blocks, preamble).
- `_execute_azure_chat` must iterate across all items in `content` where `type == "text"` or `text in item` and concatenate them into a single string.
- If no text blocks exist, the payload must be examined for `"error"` or `"message"` keys and raise a clear `RuntimeError`.

### 3. Resilient JSON Extraction with Thinking Tag Stripping and Array Normalization
- `_extract_json_from_llm_response` will strip `<thinking>[\s\S]*?</thinking>` tags before searching for JSON.
- If an LLM returns a JSON array (e.g. `[{"claim": "..."}]`) instead of a dict with `"items"`, it will be normalized into `{"items": [...]}` to satisfy consumer expectations.
- If parsing returns empty or fails, `roles.py` will record the exact reason into `last_azure_error`, log a visible parse failure message, and treat parse failures as transient retryable errors across attempts and model failovers.

### 4. Extract Role Token Quota and Orchestrator Defense
- The `extract` role `max_tokens` is raised from 2500 to 4000 to prevent JSON truncation when extracting up to 10 search snippets.
- `orchestrator.py` wraps `extract` and `gap` role calls in defensive try-except blocks, ensuring that if search extraction fails, the report continues cleanly with primary SEC filing evidence.
