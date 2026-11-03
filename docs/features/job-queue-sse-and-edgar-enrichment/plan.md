# Feature Plan: Async Job Queue, SSE Push Channel, and EDGAR Filings Enrichment

**Datetime**: 2026-11-03T22:16:00+05:30  
**Feature Slug**: `job-queue-sse-and-edgar-enrichment`  
**Status**: Complete / Verified

---

## 1. Goal
Implement the two remaining critical workflow capabilities specified in `agent-instructions/workflow-review.md`:
1. **Async Job Queue & SSE Push Channel**:
   - Provide an asynchronous job execution manager with non-blocking submission (`POST /api/do-risk-report/jobs`).
   - Granular status polling (`GET /api/do-risk-report/jobs/{job_id}`).
   - Real-time Server-Sent Events (SSE) push streaming (`GET /api/do-risk-report/jobs/{job_id}/stream`) that streams progress milestones and completed markdown sections as soon as they finish validation so users can read live before final synthesis.
2. **SEC EDGAR Primary Filings Enrichment (Lane A)**:
   - Expand `EdgarFetcher` in `backend/app/workflows/do_risk_report/edgar.py` to extract primary evidence from recent 8-K filings (auditor changes 4.01, restatements 4.02, board/executive changes 5.02, material agreements 1.01, M&A 2.01) and DEF 14A proxy filings directly into the Evidence Ledger without search.

---

## 2. Scope

### In Scope
- **Job Manager (`jobs.py`)**:
  - `JobManager` singleton tracking job state, progress, completed sections, results, errors, and subscriber queues.
  - Background async execution via `asyncio.create_task()`.
  - SSE event generator formatting events (`progress`, `section_complete`, `completed`, `error`).
- **Orchestrator Callbacks (`orchestrator.py`)**:
  - Add `on_section_complete(section_name, section_title, section_text)` callback.
  - Invoke `on_section_complete` as each section finishes drafting in Stage 2.
- **REST & SSE Endpoints (`main.py`)**:
  - `POST /api/do-risk-report/jobs` (HTTP 202 Accepted, returns `job_id`).
  - `GET /api/do-risk-report/jobs/{job_id}` (JSON status and progress).
  - `GET /api/do-risk-report/jobs/{job_id}/stream` (SSE text/event-stream).
- **EDGAR Filings Extraction (`edgar.py`)**:
  - Extract recent 8-K items (4.01, 4.02, 5.02, 1.01, 2.01, 8.01) directly from `submissions.json`.
  - Populate Evidence Ledger rows for `board_and_governance`, `regulatory_and_accounting`, `key_disclosures`, and `ma_capital_allocation` with `source_type="filing"` and `confidence="high"`.
  - Extract latest DEF 14A proxy filing metadata.
- **Automated Tests**:
  - Unit tests for `JobManager` lifecycle, SSE queue delivery, and EDGAR 8-K / DEF 14A extraction.

---

## 3. Interfaces & Data Flow

```
[Client / Frontend]
       │
       ├─► POST /api/do-risk-report/jobs ─────────► [JobManager] ──► (Returns job_id immediately)
       │                                                 │
       │                                                 ▼ (asyncio background task)
       │                                            [Orchestrator]
       │                                                 │
       ├─► GET /api/do-risk-report/jobs/{id}/stream ◄───┤ (SSE push stream)
       │                                                 ├─ Stage progress events
       │                                                 ├─ Section markdown as validated
       │                                                 └─ Final report & artifacts
       │
       └─► GET /api/do-risk-report/jobs/{id} ────────────► [Job Status Poll]
```

---

## 4. Risks & Mitigations
- *Risk*: Disconnected SSE client causes memory leak in queues.
  - *Mitigation*: Unsubscribe listeners on client disconnect or queue closure; bounded queues with auto-removal.
- *Risk*: Missing 8-K items on foreign private issuers (20-F / 6-K).
  - *Mitigation*: Gracefully handle 6-K material reports alongside 8-Ks.
