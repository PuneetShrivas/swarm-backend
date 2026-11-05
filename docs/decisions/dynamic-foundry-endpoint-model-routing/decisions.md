# Decision Record: Dynamic Azure Foundry Endpoint Routing by Model

## Datetime
`2026-11-05T15:24:15+05:30`

## Context
Azure AI Foundry hosts both Anthropic Claude models and OpenAI GPT models behind resource endpoints.
- Anthropic Claude models (e.g. `claude-opus-4-8`, `claude-sonnet-4-6`) require the `/anthropic/v1/messages` path.
- OpenAI models (specifically `gpt-5.4` and `gpt-5-mini`) on the same Azure resource require the `/openai/v1/messages` path.

Users may run pipelines specifying different models via CLI arguments (`--model gpt-5.4`) or environment variables while having a default `AZURE_FOUNDRY_ENDPOINT` set to the Anthropic path in their `.env` files.

## Decisions

1. **Model-Aware Endpoint Resolution**:
   Introduce a dedicated function `resolve_foundry_endpoint(model, base_endpoint)` in both instances of the agnostic workflow:
   - Matches `gpt-5.4` and `gpt-5-mini` (case-insensitive, prefix-tolerant).
   - If `gpt-5.4` or `gpt-5-mini` is used, converts any configured Anthropic endpoint (`.../anthropic/v1/messages`) or bare host to `.../openai/v1/messages`.
   - If Claude or other models are used, ensures `.../anthropic/v1/messages` is targeted.

2. **Dual Response & Token Schema Parsing**:
   Azure Foundry `/openai/v1/messages` and `/anthropic/v1/messages` return slightly different token metadata (`prompt_tokens`/`completion_tokens` vs `input_tokens`/`output_tokens`) and text payloads (`content` vs `choices`). `_execute_azure_chat_with_tokens()` is updated to support both schemas gracefully.

3. **Strict Zero-Coupling Invariant**:
   `agnostic_workflow/` implements the resolution independently without importing from `backend/app/*`.

## Consequences
- Pipelines can dynamically toggle between `claude-opus-4-8`, `claude-sonnet-4-6`, `gpt-5.4`, and `gpt-5-mini` without manual `.env` file changes or 404 RouteNotFound errors from Azure Foundry.
