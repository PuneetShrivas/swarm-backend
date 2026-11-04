# Architectural Decisions: Azure Foundry Fast Alternative Pipeline

## Datetime
`2026-11-04T17:45:22+05:30`

## Context
The user requested an alternative pipeline using the same Azure Foundry resources with the following topology:
1. Target company name is sent to `DO-researcher`.
2. The response is:
   - Pathway 1: Directly sent to `DO-report-generator` agent (bypassing `DO-validator`).
   - Pathway 2: A model from Azure Foundry (`claude-sonnet-4-6` or `claude-opus-4-8`) is called directly with the response to generate an executive report quickly.

## Decisions

### 1. Unified Fast Pipeline Module (`azure_agents_pipeline/fast_pipeline.py`)
Rather than creating separate ad-hoc scripts, we implement `FastAzureFoundryPipeline` in `azure_agents_pipeline/fast_pipeline.py` alongside the existing standard pipeline. It supports three flexible modes:
- `--mode both` (default): Runs both Pathway 1 and Pathway 2, timing both and comparing token usage and latency.
- `--mode agent`: Runs only Pathway 1 (Researcher → Agent Generator).
- `--mode direct`: Runs only Pathway 2 (Researcher → Direct Azure Foundry Model).

### 2. Dual Generation Mechanisms on the Same Azure Resource
- **Pathway 1 (`DO-report-generator`)**: Uses `AIProjectClient` to bind the preview OpenAI client to `agent_name="DO-report-generator"`, opens a conversation, and executes a turn.
- **Pathway 2 (Direct Model)**: Directly queries the Azure Foundry endpoint (`https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages`) using `httpx` and `AZURE_API_KEY`. This provides sub-second network overhead and eliminates conversational state setup for ultra-fast generation.

### 3. Comprehensive Artifacts & Comparative Telemetry
When running in `--mode both`, the pipeline writes:
- `DO_Risk_Report_<TICKER>_fast_agent.md` and `.pdf` (Report from Agent Generator)
- `DO_Risk_Report_<TICKER>_fast_direct.md` and `.pdf` (Report from Direct Model)
- `DO_Risk_Report_<TICKER>_fast_telemetry.json` (Full metrics comparing latency, tokens, and output length)
- Terminal summary prints a side-by-side comparison table showing speedup and token efficiency.
