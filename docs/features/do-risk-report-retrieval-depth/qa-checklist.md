# QA Checklist: Perplexity Retrieval Timeout Extension & Comprehensive Research Extraction

**Created Datetime**: 2026-11-03T15:55:00+05:30  
**Last Updated Datetime**: 2026-11-03T16:10:00+05:30  

## Pre-Release Acceptance Criteria

- [x] Perplexity timeout extended from 15s to 60s (`DEFAULT_PERPLEXITY_TIMEOUT = 60.0`).
- [x] Restrictive `site:` boolean filter removed; natural search queries passed to Perplexity.
- [x] Full grounded synthesis and structured source snippets passed to Groq `extract` role.
- [x] Groq fast/medium tiers upgraded to `openai/gpt-oss-20b`, resolving 1000 OTPM ceiling.
- [x] All 39 unit tests in `backend/test_do_risk_report.py` passing.
- [x] Live execution in standard mode completed end-to-end without unhandled crashes.
- [x] Deliverables generated with 5 pages, running headers/footers, and clean layout.
