# Feature: Stage 2 Real-Time Visual Progress & Granular CLI Telemetry

Datetime: 2026-11-05T16:15:00+05:30

## Status

Approved

## Goal

Provide rich, real-time, visual CLI telemetry and granular progress indicators during Stage 2 (`Concurrent Perplexity retrieval & fact extraction across N sections...`) and Stage 3 synthesis. When researching multiple sections in parallel (e.g., 10 sections with 3 rounds of search, extraction, and gap analysis), the terminal currently remains silent for 5–9 minutes without visual feedback. This feature makes every section's lifecycle (Planning, Search, Extraction, Gap Analysis, Narrative Drafting, Completion) transparently observable with real-time ASCII progress bars, section status tags, query and facts counters, and wall-clock elapsed timers.

## Scope

- In scope:
  - Granular real-time event reporting inside `_process_section()` for:
    - `[PLAN]` Search query planning initiation and completion with query counts.
    - `[SEARCH]` Perplexity web search execution with query count, round indicators `(R1/3)`, and snippet retrieval counts.
    - `[EXTRACT]` Evidence claim extraction with round indicators, newly added claims count, section claims total, and global ledger total.
    - `[GAP]` Gap analysis with missing fields verification and follow-up query counts.
    - `[DRAFT]` Section narrative drafting initiation, retry countdowns (if any), and completion token/citation stats.
    - `[DONE]` Section completion badge with total duration, query count, facts count, and visual ASCII progress bar `[████░░░░░░] X/N (Y%)`.
  - Rich stage-level progress notifications for Stage 1 (spec parsing), Stage 3 (executive synthesis & verdict passes), and Stage 4 (rendering).
  - Synchronized implementation across both workflow codebases:
    - `backend/app/workflows/agnostic_research_report/orchestrator.py`
    - `agnostic_workflow/orchestrator.py`
  - Update `agnostic_workflow.zip` distribution package.
  - Comprehensive unit test coverage for progress events.

- Out of scope:
  - Curses / ncurses full-screen TUI dashboards (needs cross-platform compatibility across Windows PowerShell, Linux, macOS, and non-interactive piped logs without screen corruption).
  - Modifying Perplexity API or LLM provider request parameters.

## Current behavior

During Stage 2, `AgnosticResearchOrchestrator.run()` prints:
`[*] Concurrent Perplexity retrieval & fact extraction across 10 sections...`
All sections run inside `asyncio.gather(*[_run_section_worker(s) for s in body_sections])`. Inside `_process_section()`, no callback or print statements are invoked except for rare retry warnings. The user receives 0 feedback for several minutes until the entire stage completes.

## Proposed behavior

1. Add an async-safe callback mechanism to `_process_section()`.
2. As each section executes its lifecycle steps, emit informative, visual progress updates with badges:
   - `[PLAN] [SECTION] Formulating targeted search queries...`
   - `[PLAN DONE] [SECTION] 3 queries generated (1.1s)`
   - `[SEARCH] [SECTION] (R1/3) Querying Perplexity for 3 queries...`
   - `[SEARCH DONE] [SECTION] (R1/3) 12 snippets retrieved (0.8s)`
   - `[EXTRACT] [SECTION] (R1/3) Extracting atomic facts...`
   - `[EXTRACT DONE] [SECTION] (R1/3) +5 facts extracted [Section: 5 | Global: 24 facts] (2.1s)`
   - `[GAP] [SECTION] (R1/3) Analyzing coverage...`
   - `[GAP DONE] [SECTION] (R1/3) 2 follow-up queries planned (1.4s)`
   - `[DRAFT] [SECTION] Drafting narrative citing 14 facts...`
   - `[DRAFT DONE] [SECTION] Draft complete (6.4s)`
   - `[SECTION DONE] [3/10] [███░░░░░░░] 30% [SECTION] finished in 28.4s | 14 facts | 5 queries`
3. Include visual progress bars and section counters so users can instantly gauge remaining workload and active pipeline steps.

## Implementation steps

1. Update `orchestrator.py` in `backend/app/workflows/agnostic_research_report/`:
   - Pass progress callback into `_process_section()`.
   - Implement thread-safe/asyncio-safe section completion tracking (`completed_count`, `total_sections`, `start_time`).
   - Add ASCII progress bar generator helper `_render_progress_bar(completed, total, width=12)`.
   - Add granular event emissions at every lifecycle milestone (`plan`, `plan_done`, `search`, `search_done`, `extract`, `extract_done`, `gap`, `gap_done`, `draft`, `draft_done`, `section_done`).
2. Replicate all changes identically to `agnostic_workflow/orchestrator.py`.
3. Update unit tests in `backend/test_agnostic_research_report.py` and `agnostic_workflow/test_standalone_workflow.py` to assert granular callback event triggers.
4. Repack `agnostic_workflow.zip`.
5. Run full test suite and verify clean test execution.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/agnostic_research_report/orchestrator.py` | Add granular progress notifications and progress bar to `_process_section` and `run` | Real-time CLI observability during Stage 2 |
| `agnostic_workflow/orchestrator.py` | Replicate progress callbacks and status bar | Maintain standalone workflow parity |
| `backend/test_agnostic_research_report.py` | Add tests verifying progress callback receives granular section events | Verify behavioral correctness |
| `agnostic_workflow/test_standalone_workflow.py` | Add tests verifying progress callback receives granular section events in standalone package | Parity verification |
| `agnostic_workflow.zip` | Re-bundle package archive | Keep standalone zip archive in sync |

## Interfaces

Callback signature remains backwards compatible:
```python
on_progress: Optional[Callable[[str, str], None]] = None
```
Emitted stage keys include:
- `stage_1`, `stage_2`, `stage_2_done`, `stage_3`, `stage_3_done`, `stage_4`, `stage_4_done`
- `plan`, `plan_done`, `search`, `search_done`, `extract`, `extract_done`, `gap`, `gap_done`, `draft`, `draft_done`, `section_done`

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Parallel async callbacks interleave output | Terminal lines might overlap if prints are buffered | Use `flush=True` and structured one-line messages with section titles |
| High volume of progress messages | Terminal clutter | Keep messages concise, single-line, and tagged with clear brackets `[TAG] [SECTION]` |
| Performance overhead | Slowing down async gathering | All status string rendering is in-memory formatting taking <0.05ms per call |

## Verification

- Unit tests: Run `backend/test_agnostic_research_report.py` and `agnostic_workflow/test_standalone_workflow.py`.
- Regression check: Validate mock orchestrator runs record all event types in callback collector.
- Package check: Repack zip and verify zero dependencies on `app/` in `agnostic_workflow/`.
