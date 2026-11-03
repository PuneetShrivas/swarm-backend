# QA Checklist: D&O Public Risk Report Granular Timing Telemetry & Single-Instruction CLI Runner

**Created Datetime**: 2026-11-03T14:08:00+05:30  
**Last Updated Datetime**: 2026-11-03T14:23:00+05:30  

## Pre-Release Acceptance Criteria

- [x] Immediate CLI instructions tested and confirmed working on codebase.
- [x] Granular timing models defined in `models.py` (`EdgarSubstageTiming`, `SectionSubsectionTiming`, `SectionTiming`, `ValidationSubsectionTiming`, `RenderingSubsectionTiming`, `ReportTelemetry`).
- [x] EDGAR extraction records sub-timings (CIK lookup, submissions metadata fetch, XBRL facts fetch, ledger population).
- [x] Retrieval and Groq role execution return latency metrics (`batch_search_with_timings`, `run_role_with_timings`).
- [x] Orchestrator captures per-section and per-round granular timings (retrieval, extract, gap check, draft narrative).
- [x] Orchestrator captures rendering sub-timings (footnote transform, markdown, docx, pdf).
- [x] Orchestrator captures validation agent sub-timings (deterministic checks, validation agent pass).
- [x] Single-instruction CLI runner (`backend/run_do_risk_report.py`) executes end-to-end and outputs formatted hierarchical timings.
- [x] Indented tree structure (`--format tree`) set as the default output view.
- [x] Concurrency speedup multiplier computed and displayed (`total_compute_ms / total_wall_clock_ms`).
- [x] Automated unit and integration tests passing (34/34 tests green).
- [x] All feature documentation (`plan.md`, `implementation.md`, `verification.md`, `qa-checklist.md`) and changelog updated.
