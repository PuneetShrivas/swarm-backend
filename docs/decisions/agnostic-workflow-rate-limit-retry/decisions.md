# Architecture Decision: Agnostic Workflow Azure Rate Limit (HTTP 429) Retry & Recovery

## Datetime
`2026-11-05T13:30:35+05:30`

## Context
When running extensive multi-section reports (e.g. 11+ sections on a single company prompt), multiple sections attempt drafting concurrently. Azure AI Foundry enforces strict Tokens-Per-Minute (TPM) limits on high-tier reasoning models like `claude-opus-4-8` (e.g. `8000 per 60s exceeded for UserByModelByMinuteOutputTokens`).
Previously:
1. `roles.py` only attempted 2 to 3 immediate tries with tiny 2s/4s sleep intervals, quickly exhausting retries.
2. `orchestrator.py` caught exceptions during `run_role("draft")` and directly populated the section text with `- Section drafting unavailable due to upstream error: ...`, resulting in skipped sections in the generated report.

## Decision
1. **Dynamic Wait Parsing (`_parse_retry_delay`)**:
   Parse the exact wait recommendation from Azure's error message:
   `Please wait (\d+(?:\.\d+)?) seconds before retrying`
   and add a 2.0s safety margin. If no explicit duration is given, fall back to exponential backoff (e.g., 5s, 10s, 20s).
2. **Multi-Round Outer Retry Loop in `roles.py`**:
   Implement `max_outer_rounds = int(os.environ.get("AZURE_MAX_RETRY_ROUNDS", "5"))`. When all models in a sequence hit rate limits, pause for quota reset (`base_wait = 15s + round * 10s` or parsed wait) with live progress logging (`⏳ [AZURE COOLDOWN] Role 'draft': [#####-----] 10s/25s...`).
3. **Persistent Section Drafting in `orchestrator.py`**:
   Wrap drafting in a persistent loop with retries. Never output placeholder error bullets that corrupt final publications; instead wait and retry until successful drafting occurs.

## Consequences
- Reports never contain corrupted "Section drafting unavailable" placeholder text.
- Full section narratives are preserved even under strict Azure Foundry token quotas.
- Clear, live terminal progress logging keeps the user informed while waiting for quota replenishment.
