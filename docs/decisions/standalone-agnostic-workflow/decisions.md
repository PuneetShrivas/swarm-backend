# Architecture Decision: Standalone Portable Agnostic Workflow Package

## Datetime
`2026-11-05T12:34:19+05:30`

## Status
Accepted

## Context
The user requested a completely self-contained folder in the repository root for the agnostic research workflow so that it can be zipped, transferred to another environment, and executed independently with its own `.env` file without any dependencies on the main backend repository structure. Additionally, the prompt parser must reliably ingest both standard Markdown formatted headings and un-prefixed uppercase section headings (such as those in `agent-instructions/web-search-prompt.md`) which previously resulted in 0 parsed sections.

## Decisions

### 1. Independent Root Folder (`agnostic_workflow/`)
- Located directly at the root of the project: `agnostic_workflow/`.
- Contains all required modules, templates, entrypoints, and documentation.
- Has zero imports referencing `backend.app.*`. All modules use clean local package imports (`from .models import ...` or `import ...`).

### 2. Built-in Standalone Perplexity Client
- Inlined the asynchronous Perplexity Search API caller with exponential backoff directly within `agnostic_workflow/retrieval.py` using standard `httpx`.
- Removes the previous external dependency on `backend.app.agents.researcher.tools`.

### 3. Dual-Syntax Specification Parser (`spec_parser.py`)
- The parser supports:
  1. Standard Markdown headings: `#`, `##`, `###`.
  2. Plain-text uppercase section headers: e.g. `COMPANY SNAPSHOT`, `FINANCIAL OVERVIEW`, `ANALYSTS`, `GOVERNANCE & CULTURE`.
  3. Bold-wrapped section headers: e.g. `** UPDATES / PRESS RELEASES / NEWS**`.
- Excludes common uppercase keywords (`TITLE`, `RULES`, `OUTPUT`, `GLOBAL FORMATTING RULES`) so that prompt guidelines are not mistaken for report sections.
- This resolves the issue where `agent-instructions/web-search-prompt.md` yielded 0 sections.

### 4. Portable Configuration Loader (`config.py`)
- Automatically looks for `.env` in the current working directory, then in the `agnostic_workflow/` directory, and finally in the parent directory.
- Allows the user to drop a `.env` file directly into the unzipped folder and run immediately.
