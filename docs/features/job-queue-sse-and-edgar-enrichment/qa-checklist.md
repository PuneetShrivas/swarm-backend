# QA Checklist: Async Job Queue, SSE Push Channel, and EDGAR Primary Filings Enrichment

**Created Datetime**: 2026-11-03T21:56:00+05:30  
**Last Updated Datetime**: 2026-11-03T22:16:00+05:30  
**Feature Slug**: `job-queue-sse-and-edgar-enrichment`  
**Status**: Complete

---

## Pre-Release Acceptance Criteria

- [x] **8-K Items Extracted Directly**: SEC EDGAR `submissions.json` items are extracted into Evidence Ledger without web search.
- [x] **High-Stakes Preservation**: Critical 8-K items (4.01 auditor changes, 4.02 restatements, 5.01 change in control, 5.02 executive/director departures, 1.01 material contracts, 2.01 M&A) are preserved up to 10 filings.
- [x] **DEF 14A Proxy Statements**: Official proxy statement dates and accession numbers are extracted into `board_and_governance`.
- [x] **Periodic Filings Metadata**: Latest Form 10-K and 10-Q filing metadata are extracted into `company_snapshot`.
- [x] **Evidence Provenance**: All EDGAR extracted facts receive `source_type="filing"` and `confidence="high"` with direct SEC archive links.
- [x] **Non-Blocking REST Ingestion**: `POST /api/do-risk-report/jobs` returns HTTP 202 Accepted immediately with `job_id`, `stream_url`, and `status_url`.
- [x] **Status Polling Endpoint**: `GET /api/do-risk-report/jobs/{job_id}` returns status, stage progress, and completed sections.
- [x] **Section Early Reading**: As Stage 2 sections clear validation, `on_section_complete` emits full markdown text and titles into `completed_sections` and over SSE.
- [x] **SSE Push Channel**: `GET /api/do-risk-report/jobs/{job_id}/stream` streams `event: init`, `progress`, `section_complete`, `completed`, and `error`.
- [x] **Connection Heartbeats**: Idle SSE connections receive `: keep-alive` comments every 15 seconds.
- [x] **Disconnect Cleanup**: Disconnected subscribers automatically unregister queues from `_subscribers`.
- [x] **Automated Tests**: 57 automated unit and integration tests passing in `backend.test_do_risk_report`.
- [x] **Documentation Integrity**: Feature plan, implementation log, verification report, and ADR updated with Datetime timestamps.
