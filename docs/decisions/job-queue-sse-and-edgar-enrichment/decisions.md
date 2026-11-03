# Architectural Decisions: Job Queue, SSE Push Channel, and EDGAR Primary Filings Enrichment

**Datetime**: 2026-11-03T21:56:45+05:30  
**Slug**: `job-queue-sse-and-edgar-enrichment`  
**Status**: Accepted

---

## 1. Async Job Queue with Non-Blocking REST Ingestion
- **Context**: Full D&O public risk report generation takes 1–4 minutes depending on the execution mode (fast vs standard) and LLM provider. Synchronous HTTP request-response ties up HTTP connections, risks gateway 504 timeouts (especially on Vercel/proxies), and prevents the user from receiving real-time progress.
- **Decision**: 
  - Expose `POST /api/do-risk-report/jobs` returning HTTP 202 Accepted with a generated `job_id` immediately.
  - Execute report generation in the background using an asyncio worker task.
  - Manage in-memory job state via a centralized `JobManager` singleton with thread-safe and async-safe state transitions.

---

## 2. Server-Sent Events (SSE) Push Stream with Section-Level Early Reading
- **Context**: In traditional pipelines, users wait until the final synthesis and rendering finish before reading anything. However, sections complete drafting and validation progressively during Stage 2.
- **Decision**:
  - Expose `GET /api/do-risk-report/jobs/{job_id}/stream` returning `text/event-stream`.
  - Push granular events:
    1. `progress`: Stage and subsection updates (`stage_1`, `stage_2`, etc.).
    2. `section_complete`: Emits the full markdown text and title of each section as soon as it clears Layer 2 validation. This allows the user to begin reading sections while remaining sections are still processing.
    3. `completed`: Emits the final report result, telemetry tree, and artifact URLs.
    4. `error`: Emits formatted failure details if execution fails.

---

## 3. SEC EDGAR Primary Source Filings Enrichment (Lane A)
- **Context**: Primary regulatory filings (8-Ks, DEF 14As) are authoritative and legally binding. Searching for material events (e.g. accounting restatements, executive departures) via web search introduces token cost, third-party noise, and potential hallucination.
- **Decision**:
  - Parse the `items` array directly from SEC EDGAR `submissions.json`:
    - `Item 4.01`: Auditor Resignations / Changes
    - `Item 4.02`: Financial Restatements (Non-Reliance on Prior Statements)
    - `Item 5.02`: Departure / Appointment of Directors & Principal Officers
    - `Item 1.01`: Material Definitive Agreements
    - `Item 2.01`: Acquisitions & Dispositions
  - Directly construct and insert high-confidence `Evidence` rows into the `EvidenceLedger` under the relevant sections with `source_type="filing"` and official `sec.gov` archive accession links.
  - Identify and extract latest DEF 14A proxy filing dates and executive governance facts.
