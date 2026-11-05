# Implementation: Stage 2 Real-Time Visual Progress & Granular CLI Telemetry

Datetime: 2026-11-05T16:25:00+05:30

## Overview

Added granular, real-time lifecycle event notifications and ASCII completion bars during Stage 2 parallel research and extraction, as well as Stage 3 executive synthesis and Stage 5 artifact generation.

## Key Changes

### 1. Progress Bar Helper (`_render_progress_bar`)
Created ASCII visual bar generator with customizable width and percentage formatting:
```python
def _render_progress_bar(completed: int, total: int, width: int = 14) -> str:
    if total <= 0:
        return "[--------------]"
    fraction = min(max(completed / total, 0.0), 1.0)
    filled_len = int(round(width * fraction))
    bar = "█" * filled_len + "░" * (width - filled_len)
    percent = int(fraction * 100)
    return f"[{bar}] {percent}%"
```

### 2. Granular Milestone Notifications inside `_process_section`
Added an async-safe callback parameter `progress_cb: Optional[Callable[[str, str], None]] = None` and integrated scoped milestone triggers:
- **`[PLAN]`**: Notifies before query formulation and reports elapsed duration and query count upon completion.
- **`[SEARCH]`**: Notifies at Perplexity retrieval start with `(R{rnd}/{total})` indicators and reports retrieved snippets count and round duration.
- **`[EXTRACT]`**: Notifies when extracting claims and reports newly extracted claims, section claim total, and global ledger running total.
- **`[GAP]`**: Notifies during gap analysis and reports follow-up query counts.
- **`[DRAFT]`**: Notifies when drafting section narratives with evidence counts, handles drafting retries, and notifies on completion with token counts.

### 3. Stage 2 Completion Tracker in Orchestrator `run()`
Inside `_run_section_worker(sec_spec: SectionSpec)`:
- Maintained an asyncio completion counter (`completed_sections / total_sections`).
- On section completion, emits a formatted progress bar with section duration, facts count, queries count, and global ledger running total:
  ```
  [*] [DONE] [3/10] [████░░░░░░░░░░] 30% 'COMPETITIVE POSITION' completed in 24.3s | 14 facts | 4 queries | Global Ledger: 42 facts
  ```

### 4. Stage 3 & Stage 5 Telemetry Polish
- Stage 3 emits notifications for individual synthesis sections (`[SYNTH] [EXECUTIVE SUMMARY] (1/2) Synthesizing cross-section insights...`).
- Stage 5 reports citation resolution count (`Resolved and linked N [E###] citation tokens to footnotes`).

### 5. CLI Clean Prefixes
Updated `backend/app/workflows/agnostic_research_report/cli.py` and `agnostic_workflow/run_workflow.py` so messages that already contain `[*]` are not prefixed twice.

### 6. Synchronized Standalone Package
All changes applied synchronously to:
- `backend/app/workflows/agnostic_research_report/orchestrator.py`
- `agnostic_workflow/orchestrator.py`
- Re-packaged `agnostic_workflow.zip` (47,718 bytes).
