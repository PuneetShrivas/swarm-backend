# Architecture Decisions: Groq Default Provider, File Generator Agent Fix, and Perplexity Research Workflow

## Datetime
2026-10-29T17:24:00+05:30

## Context
1. The user reported that asking for a sample CSV file did not produce downloadable files in the frontend. Root cause analysis identified that `"csv"` was present in `data_keywords`, so queries like `"generate a sample csv file"` were hijacked by `data_analyst` rather than routed to `file_creator`. Furthermore, the code fence extraction regex was strict on `\n` without accommodating CRLF (`\r\n`) or trailing spaces after language fences.
2. The user required the research step in the default workflow to strictly run on Perplexity's Sonar model for real-time web discovery and grounding.
3. The user requested adding Groq as the default site-wide model provider with `qwen-3.8` as primary model, while retaining Gemini and Perplexity options.

## Decisions

### 1. Keyword Routing Hierarchy
- **Decision**: Evaluate `file_create_keywords` and composite verb/noun creation expressions before general `data_keywords`.
- **Rationale**: Creation intents ("generate", "create", "make", "export", "download", "write") combined with dataset/file nouns ("csv", "json", "file", "spreadsheet") unambiguously represent synthesis tasks. General data analysis keywords are narrowed to analytical terms ("statistics", "mean", "median", "variance", "trend", "distribution", "analyze data").

### 2. Multi-Pipeline File Artifact Extraction
- **Decision**: Update `extract_file_artifact_from_turn` to handle `r"```([a-zA-Z0-9_-]+)?[ \t]*\r?\n([\s\S]+?)\r?\n```"`, infer file extensions from prompts if untagged, support tabular CSV fallback for `file_creator`, and hook this extraction across all providers (Groq, Gemini, Perplexity, fallback simulation).
- **Rationale**: Prevents missing download cards regardless of LLM newline conventions or model verbosity.

### 3. Groq Provider Integration & Model Resolution
- **Decision**: Implement `backend/app/groq_client.py` as a centralized service layer using the official `groq` SDK.
- **Model Resolution**: Standardize on `qwen-3.8` as the user-facing model slug, resolving to candidate IDs (`qwen/qwen3.8-27b`, `qwen-2.5-32b`, `qwen-2.5-coder-32b`, etc.) with automatic fallback if a specific tag is decommissioned.
- **Provider Precedence**:
  1. Perplexity Sonar for `sonar` models, research agent, and live query intents.
  2. Groq for default execution and `qwen-3.8` / `llama` models when `GROQ_API_KEY` is present.
  3. Google Gemini when `gemini-*` models are requested or as secondary provider.
  4. Deterministic demo simulation when offline or keys unconfigured.

### 4. WorkflowStep Schema Extension
- **Decision**: Add `model: Optional[str] = Field(default=None)` to `WorkflowStep` in `backend/app/workflows/models.py`.
- **Rationale**: Ensures step-level model selections (such as `sonar` for `step_research`) survive Pydantic validation when seeding, saving, or executing workflows.
