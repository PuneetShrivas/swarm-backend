# QA Checklist: Stage 2 Real-Time Visual Progress & Granular CLI Telemetry

Datetime: 2026-11-05T16:25:00+05:30

- [x] Planning milestone triggers `[PLAN]` event and `[PLAN DONE]` upon query completion.
- [x] Perplexity search milestone triggers `[SEARCH]` with round `(R{rnd}/{total})` and `[SEARCH DONE]` with snippet counts.
- [x] Fact extraction triggers `[EXTRACT]` and `[EXTRACT DONE]` with running section & global ledger fact totals.
- [x] Gap analysis triggers `[GAP]` and `[GAP DONE]` with follow-up query counts.
- [x] Narrative drafting triggers `[DRAFT]` with evidence citations and `[DRAFT DONE]` with elapsed time & tokens.
- [x] Completed sections print an ASCII progress bar `[████░░░░░░░░] P%` and running global ledger total.
- [x] Stage 3 synthesis sections emit granular `[SYNTH]` and `[SYNTH DONE]` progress messages.
- [x] Stage 5 renders footnote linkage count.
- [x] CLI entrypoints (`backend/run_agnostic_research_report.py` and `agnostic_workflow/run_workflow.py`) avoid duplicate `[*]` prefixes.
- [x] Parity preserved across `backend/app/workflows/agnostic_research_report/` and `agnostic_workflow/`.
- [x] `agnostic_workflow.zip` contains updated files.
- [x] All 21 backend unit tests pass.
- [x] All 14 standalone unit tests pass.
- [x] Git diff is clean and targeted.
