# QA Checklist: D&O Public Risk Report Depth Parity & Claude-Quality Deliverables

**Created Datetime**: 2026-11-03T15:02:00+05:30  
**Last Updated Datetime**: 2026-11-03T15:35:00+05:30  

## Pre-Release Acceptance Criteria

- [x] All 12 sections dynamically extracted from `web-search-prompt.txt` at runtime without hardcoded Python section dictionaries.
- [x] Verbatim section instructions and Master Underwriting Guidelines injected into `run_role("draft")`.
- [x] Static and dynamic search queries generated for all sections (analyst consensus, short interest, executive litigation, governance drift, supply chain).
- [x] `_generate_mock_role_output` in `roles.py` emits distinct, rich, multi-paragraph mock outputs for all 11 drafted sections and executive synthesis.
- [x] Prompt leak (`REPORT TO VALIDATE AND CORRECT:`) completely eliminated from `validator.py`.
- [x] PDF renderer upgraded with ReportLab `NumberedCanvas` (running headers `COMPANY — D&O Underwriting Analysis — DATE`, footers `CONFIDENTIAL & PROPRIETARY — Page X of Y`, callout verdict boxes, structured markdown tables).
- [x] Generated report delivers 20,545 characters and 5 full pages in ReportLab PDF matching benchmark depth.
- [x] All 39 automated unit and regression tests passing.
- [x] Verification report updated and changelog documented.
