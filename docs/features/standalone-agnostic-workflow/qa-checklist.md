# QA Checklist: Standalone Portable Agnostic Workflow Package

## Datetime
`2026-11-05T12:53:50+05:30`

- [x] **Zero-coupling isolation**: Package lives entirely inside root directory `agnostic_workflow/` and does not import anything from `backend/app/`.
- [x] **Standalone configuration**: `config.py` automatically discovers `.env` locally or in parent folders; `.env.example` provides complete configuration options.
- [x] **Enhanced prompt parser**: Robustly parses both standard `#`/`##` Markdown templates and unstructured plaintext / uppercase / bold prompts (resolving the 0-sections bug in `web-search-prompt.md`).
- [x] **Sequential evidence ledger**: Atomic facts are stored with sequential tokens `[E001]`, `[E002]`, etc. and mapped to numbered publication footnotes `[1]`, `[2]`.
- [x] **Zero-dependency Perplexity client**: Directly executes `httpx` POST to `https://api.perplexity.ai/search` with exponential retry, wire news deduplication, and disk caching.
- [x] **Multi-provider LLM executor**: Supports Azure AI Foundry (with API key and Entra ID bearer token fallback), Groq, Google Gemini, and IteraCompute with token accounting (`input_tokens`, `output_tokens`, `total_tokens`).
- [x] **Publication renderer**: Generates clean Markdown reports and ReportLab PDF documents with two-pass `NumberedCanvas` ('Page X of Y'), running headers/footers, cover metadata tables, and footnotes tables.
- [x] **CLI entrypoint**: `run_workflow.py` supports CLI flags (`--prompt-file`, `--provider`, `--model`, `--fallback-model`, `--mode`, `--output-dir`, `--format`).
- [x] **Packaging instructions**: `README.md` details how to zip, transfer, install dependencies, and execute in any external environment.
- [x] **Unit test coverage**: `agnostic_workflow/test_standalone_workflow.py` passes 9/9 tests; `backend/test_agnostic_research_report.py` passes 17/17 tests.
- [x] **Feature documentation**: Lifecycle docs created under `docs/features/standalone-agnostic-workflow/` and decisions in `docs/decisions/standalone-agnostic-workflow/decisions.md`.
