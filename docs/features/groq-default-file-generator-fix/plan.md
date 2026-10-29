# Feature: Groq Default Provider, File Generator Agent Fix, and Perplexity Research Workflow

## Status

In progress

## Date

2026-10-29T17:05:00+05:30

## Goal

Provide high-speed inference via Groq as the default site-wide LLM provider with Qwen 3.8, fix the file generator agent so queries like "generate a sample csv file" correctly route to `file_creator` and emit downloadable file artifacts in chat metadata, and ensure the default multi-agent workflow runs its research step using Perplexity Sonar.

## Scope

- In scope:
  - Install and configure `groq` SDK in backend requirements.
  - Implement Groq client integration with model mapping (`qwen-3.8` -> `qwen-2.5-32b-it` / `qwen-2.5-coder-32b`).
  - Make Groq default provider across `/api/chat`, custom agent tester, and workflow steps while preserving Gemini and Perplexity options.
  - Fix routing bug in `backend/app/main.py` where `data_keywords` intercepted `"csv"` requests before `file_create_keywords`.
  - Fix regex in `extract_file_artifact_from_turn` to match CRLF (`\r\n`) and trailing spaces.
  - Ensure all completion pathways invoke `extract_file_artifact_from_turn` and set `metadata.file_artifact` and `metadata.artifacts`.
  - Ensure the research step in `default-wf-research-pipeline` explicitly uses `sonar` (Perplexity) for web search and live grounding.
  - Update frontend model selector options and defaults.
  - Unit and integration tests for new endpoints, routing, and artifact emission.
- Out of scope:
  - Removing Gemini SDK or Perplexity SDK (they remain available and configurable).
  - Removing other existing models.

## Current behavior

1. When a user asks "generate a sample csv file", `route_agent` checks `data_keywords` containing `"csv"`, routing the message to `data_analyst` instead of `file_creator`.
2. `extract_file_artifact_from_turn` only matches strict LF `\n` without Windows `\r\n` or trailing whitespace after code block fence markers (` ```csv \n `), causing extraction failures.
3. Chat completions from Perplexity or other paths did not always populate `metadata.file_artifact`, so the frontend `MessageItem.tsx` download card did not render.
4. Gemini was the hardcoded default site-wide model provider; Groq SDK was not installed.

## Proposed behavior

1. `route_agent` checks `file_create_keywords` before `data_keywords`. File creation intent with `"csv"`, `"spreadsheet"`, `"json"`, or `"generate ... file"` routes to `file_creator`.
2. `extract_file_artifact_from_turn` handles CRLF and any spacing after fences. File artifacts are automatically extracted from all generation paths and attached to message metadata.
3. `groq` is installed and wrapped in `backend/app/groq_client.py`. Default model is `qwen-3.8` (mapped to Groq's active high-performance Qwen model `qwen-2.5-32b-it` / `qwen-2.5-coder-32b`).
4. If `GROQ_API_KEY` is set, Groq is used by default. If `GEMINI_API_KEY` is set, Gemini remains available and is used for Gemini models. If `PERPLEXITY_API_KEY` is set, Sonar models are used for live search/research.
5. In `default-wf-research-pipeline`, `step_research` explicitly targets `model: "sonar"` and `agent_id: "researcher"`.

## Implementation steps

1. Install `groq` SDK in backend venv and add `groq>=0.18.0` to `backend/requirements.txt`.
2. Create `backend/app/groq_client.py` with client init, model resolution, and chat completion generator.
3. Update `backend/app/main.py`:
   - Reorder routing in `route_agent` to give `file_create_keywords` higher precedence than `data_keywords`.
   - Update regex in `extract_file_artifact_from_turn`.
   - Integrate Groq execution into `/api/chat` and custom agent testing.
   - Attach file artifacts in chat metadata.
4. Verify `backend/app/workflows/default_workflows.py` sets model to `sonar` for the research agent.
5. Update frontend model selectors in `frontend/src/app/chat/components/ChatHeader.tsx` and settings.
6. Add unit tests in `backend/test_endpoints.py`.
7. Build frontend and verify all tests pass.
8. Document decisions and changelog.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/requirements.txt` | Add `groq>=0.18.0` | Groq Python SDK dependency |
| `backend/app/groq_client.py` | Create Groq client wrapper and model normalizer | Clean abstraction for Groq API calls |
| `backend/app/main.py` | Update agent routing, artifact extraction, default model, Groq handler | Fix file creator, default to Groq Qwen 3.8 |
| `backend/app/workflows/default_workflows.py` | Ensure `step_research` uses `model: "sonar"` | Perplexity web search enforcement |
| `frontend/src/app/chat/components/ChatHeader.tsx` | Add `qwen-3.8` as default model option | Frontend UI model selection |
| `backend/test_endpoints.py` | Add unit tests for routing, artifacts, Groq normalization | Prevent regressions |

## Verification

- Unit tests: Routing tests for `file_creator`, artifact extraction regex tests, Groq model mapping tests.
- Integration tests: `POST /api/chat` with file generation intent returns `file_artifact` in metadata; default workflow includes `sonar` research step.
- Commands: `backend\venv\Scripts\python backend\test_endpoints.py`, `npm --prefix frontend run build`.
