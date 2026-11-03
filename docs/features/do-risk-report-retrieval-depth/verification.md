# Verification Report: Perplexity Retrieval Timeout Extension & Comprehensive Research Extraction

**Created Datetime**: 2026-11-03T15:55:00+05:30  
**Last Updated Datetime**: 2026-11-03T16:10:00+05:30  

## Test Strategy & Results Summary

| Test Area | Expected Target | Actual Result | Status |
| :--- | :--- | :--- | :--- |
| **Perplexity Timeout** | Extended to 60s | `DEFAULT_PERPLEXITY_TIMEOUT = 60.0` active | PASS |
| **Natural Query Search** | No restrictive boolean `site:` operators | Clean natural language queries sent to Perplexity | PASS |
| **Snippet Capacity** | Full answer synthesis up to 1,500 chars | Snippet delivers up to 1,500 chars to Groq extract role | PASS |
| **Groq Model Tier** | No 429 OTPM token ceiling errors | Switched to `openai/gpt-oss-20b` (0 OTPM limit errors) | PASS |
| **Automated Tests** | 39 of 39 tests passing | 39 of 39 tests passing in 4.3s | PASS |
| **Live Standard Execution** | Full end-to-end report generation | Delivered MD (15.6 KB), DOCX (39.6 KB), PDF (13.8 KB, 5 pages) | PASS |

## Live Execution Details

- **Target Company**: Apple Inc. (`AAPL`, CIK: `0000320193`)
- **Execution Mode**: `standard`
- **Total Wall-Clock**: 376.12s (6.2 minutes)
- **Total Compute**: 2,342.10s (6.23x concurrency speedup)
- **Verified Facts in Ledger**: 15 citations
- **Risk Verdict**: `Elevated`
- **Output Artifacts**:
  - `backend/artifacts/DO_Risk_Report_AAPL_54e1f291.md`
  - `backend/artifacts/DO_Risk_Report_AAPL_54e1f291.docx`
  - `backend/artifacts/DO_Risk_Report_AAPL_54e1f291.pdf`
