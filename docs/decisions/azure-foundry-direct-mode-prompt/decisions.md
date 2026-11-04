# Architecture Decision: Direct Mode Senior Underwriter Specification Prompt

## Datetime
`2026-11-04T18:22:00+05:30`

## Status
Accepted

## Context
When running the fast alternative pipeline in `--mode direct` or `--mode both`, the output of `DO-researcher` is sent to an Azure Foundry model (`claude-sonnet-4-6` / `claude-opus-4-8`) to generate an underwriting report quickly. The user provided an exact, 13-section D&O underwriting report structure and content instruction prompt (`# D&O UNDERWRITING REPORT — STRUCTURE AND CONTENT INSTRUCTIONS`) that specifies global formatting rules, section hierarchy, field definitions, individual history filters, securities litigation risk scoring bands, and an exact closing statement.

## Decisions

### 1. Externalized Verbatim Prompt Module (`azure_agents_pipeline/prompts.py`)
- We maintain the prompt text verbatim in a dedicated module `azure_agents_pipeline/prompts.py` as `DIRECT_REPORT_PROMPT`.
- This ensures clarity, allows import in tests and documentation, and avoids cluttering `config.py` or `fast_pipeline.py`.

### 2. Payload Structure for Azure Foundry Anthropic REST API
- In Anthropic's Claude messages API on Azure Foundry:
  - `"system"`: Contains `DIRECT_REPORT_PROMPT` containing all formatting instructions, constraints, and section outlines.
  - `"messages"`: Contains a single user turn enclosing the target company and the researcher evidence base:
    ```
    TARGET COMPANY: {target_company}

    SUPPLIED EVIDENCE BASE (FROM DO-RESEARCHER):
    {research_output}

    Transform the supplied evidence into a comprehensive, professionally structured D&O underwriting report according to the instructions and structure.
    ```
  - This separation ensures the model treats the instructions as immutable system-level guardrails and the researcher output strictly as evidence without hallucination.

### 3. Dual Authentication (API Key + Entra ID Bearer Token)
- If `AZURE_API_KEY` is available, it is passed in `Authorization: Bearer <key>`.
- If `AZURE_API_KEY` is not present, the pipeline falls back to `DefaultAzureCredential` using `get_bearer_token_provider(..., "https://ai.azure.com/.default")()` to dynamically fetch an Entra ID bearer token for the REST call.

### 4. Overridability
- The prompt can be overridden via `FastAzureFoundryPipeline(direct_model_prompt=...)` or via CLI `--prompt-file path/to/prompt.md`.
