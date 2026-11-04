# Architectural Decisions: Azure Foundry Three-Agent Pipeline

## Datetime
`2026-11-04T16:48:00+05:30`

## Context
The user requested a Python workflow in a new root folder that connects to three preview agents hosted in Azure AI Foundry:
1. `DO-researcher`
2. `DO-validator`
3. `DO-report-generator`

Project Endpoint:
`https://puneetshrivas32-0871-resource.services.ai.azure.com/api/projects/puneetshrivas32-0871`

The workflow requires passing user input to `DO-researcher`, sending the generated report to `DO-validator`, giving the validated report to `DO-report-generator`, creating a PDF artifact, tracking execution timings and token counts per step, and outputting file locations and logs.

## Decisions

### 1. Dedicated Root Folder (`azure_agents_pipeline/`)
To keep this multi-agent workflow decoupled from the existing CLI in `backend/app/workflows/do_risk_report/`, we place the script in a dedicated directory at the repository root: `azure_agents_pipeline/`.

### 2. Client Pattern: `azure-ai-projects` with `get_openai_client`
Each agent is accessed via `project_client.get_openai_client(agent_name=agent_name)` as prescribed in the Azure AI Projects SDK (`>=2.1.0`). GitHub Copilot / preview agents require creating a conversation via `openai_client.conversations.create()` and passing `conversation=conversation.id` to `openai_client.responses.create(...)`.

### 3. Sequential Context Piping & Prompt Hygiene
- **Turn 1 (`DO-researcher`)**: Receives the raw user request (e.g. company name, ticker, or custom investigation instructions).
- **Turn 2 (`DO-validator`)**: Receives the output of Turn 1 wrapped with an underwriting audit prompt instructing it to verify findings, remove inconsistencies, and finalize the structured report.
- **Turn 3 (`DO-report-generator`)**: Receives the validated report wrapped with executive document styling instructions.

### 4. Telemetry and Token Tracking
The `Response` object returned by `openai_client.responses.create()` includes a `usage` attribute of type `ResponseUsage` (`input_tokens`, `output_tokens`, `total_tokens`). We capture:
- Per-step wall-clock duration (seconds and milliseconds)
- Step token metrics (`input_tokens`, `output_tokens`, `total_tokens`)
- Response ID and Conversation ID
- Aggregate totals across all three agents

### 5. Document Artifact Generation (ReportLab)
`DO-report-generator` outputs markdown / executive text. We use the repository's native ReportLab engine (`azure_agents_pipeline/pdf_compiler.py`) to render a publication-grade PDF artifact saved to `artifacts/` or `azure_agents_pipeline/artifacts/`, returning the exact file path, size, and MD5 checksum.

### 6. Authentication Flexibility & Clear Diagnostics
`DefaultAzureCredential` supports:
1. Service Principal credentials in `.env`: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`.
2. Developer authentication: Azure CLI (`az login`).
3. Interactive Browser authentication: enabled with `--interactive` CLI flag.
If authentication fails, the script outputs explicit, actionable instructions on the exact missing variables.
