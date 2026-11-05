# Decision: Real-Time CLI Telemetry & Granular Visual Progress for Stage 2 Concurrent Research

Datetime: 2026-11-05T16:15:00+05:30

## Context

In the Agnostic Research and Report pipeline, Stage 2 executes concurrent web search (Perplexity API), atomic fact extraction, gap analysis, and narrative drafting across 8–12 sections in parallel via `asyncio.gather`. With 2 to 3 search/extract/gap rounds per section, this stage typically takes between 4 and 9 minutes of wall-clock time.

Previously, only two static stage messages were emitted:
- At the start: `[*] Concurrent Perplexity retrieval & fact extraction across N sections...`
- At the end: `[*] N sections researched in Xs | Y atomic facts collected`

During the multi-minute execution, no terminal output was generated unless an unexpected HTTP error occurred. Users were left with zero visibility into which sections were executing, whether queries were dispatched, how many evidence facts were accumulated, or how many sections had concluded.

## Considered Options

### Option 1: Full-Screen Terminal Dashboard (Curses / Rich Live Table)
- Pros: Dynamically rewrites terminal rows in-place, showing a live dashboard table with animated spinners per section.
- Cons: Causes severe rendering artifacts on Windows PowerShell and Command Prompt when terminal window size changes, breaks when output is piped to log files or background processes (like Antigravity or CI/CD runners), and adds heavy external dependencies (`rich` / `curses`).

### Option 2: Polling Background Thread / Timer
- Pros: Prints a status summary every N seconds.
- Cons: Decoupled from actual async pipeline events; does not show query planning completions or exact fact discovery moments; requires thread synchronization and locks.

### Option 3: Event-Driven Granular Lifecycle Callbacks with ASCII Completion Bars (Chosen)
- Pros:
  - True event-driven observability: Every milestone (`plan`, `search`, `extract`, `gap`, `draft`, `done`) emits immediately when finished.
  - Zero external dependencies: Works seamlessly in standard Python `asyncio` across Windows PowerShell, Linux, macOS, and headless logging environments.
  - Visual completion bar: Each section completion prints a visual progress bar `[████░░░░░░] 4/10 (40%)` along with running totals for facts collected in the global ledger.
  - 100% backwards compatible with existing `on_progress(stage, msg)` callback signatures in `orchestrator.py` and CLI tools.

## Decision

Adopt **Option 3**:
1. Implement granular event notifications inside `_process_section` for every phase (`[PLAN]`, `[SEARCH]`, `[EXTRACT]`, `[GAP]`, `[DRAFT]`).
2. Maintain an asyncio-safe section completion tracker providing real-time ASCII progress bar indicators: `[DONE] [X/N] [██████░░░░] P% [Section Title] finished in Y.Ys | F facts | Q queries`.
3. Replicate the behavior synchronously across both `backend/app/workflows/agnostic_research_report/` and `agnostic_workflow/`.
