# QA Checklist: D&O Public Risk Report System & Default Workflow

Created At: 2026-11-03T12:44:30+05:30
Updated At: 2026-11-03T13:26:30+05:30
Status: Complete | All Checks Passed

## Pre-Release Acceptance Criteria

- [x] **Architecture & Control Flow Integrity**:
  - [x] Python owns the control flow DAG with parallel fan-out and bounded loops (no LLM "what should I do next").
  - [x] All LLM roles run exclusively on Groq models (`qwen/qwen3.8-27b`, `openai/gpt-oss-120b`). No Claude dependencies.
  - [x] Web search queues are dispatched through Perplexity Search with domain filters and snippet compaction.
  - [x] Evidence Ledger acts as the only data bus between retrieval and downstream roles.
  - [x] EDGAR filings and structured XBRL APIs are consumed directly in deterministic code (no LLM arithmetic).
  - [x] Raw search is compacted and consumed once by Extract; never passed downstream.
  - [x] "Not found / not publicly available" is a first-class result; model memory never invents missing facts.

- [x] **Template & Prompt Alignment**:
  - [x] Master research and report structure precisely implements `agent-instructions/web-search-prompt.txt` (14 sections, exact sub-fields, exact band vocabulary: Contained / Elevated / High-Volatility / Severe Tail Exposure).
  - [x] Validation template precisely implements `agent-instructions/validation-prompt.txt`.

- [x] **Dedicated Post-Generation Validation Agent**:
  - [x] `do_risk_validator` agent executes immediately after report generation with zero web access.
  - [x] News cutoff: items strictly before 12-month calendar cutoff from `{{currentDate}}` deleted; within-window items protected and sorted newest-first.
  - [x] Share price labeled "current/today" with older stated date relabeled "last close (<stated date>)".
  - [x] Revenue trend lines reordered to latest-year -> oldest.
  - [x] Unsourced culture claims deleted; unanchored trend claims replaced with "insufficient data to establish trend".
  - [x] Cross-section discrepancies resolved to cited source; empty headings receive "Data unavailable.".

- [x] **Evidence Ledger & Citations**:
  - [x] Deduplication on `(claim, source_url)` prevents duplicate ledger entries.
  - [x] Every claim has an `id` (`E001`, `E002`, ...), `section`, `claim`, `source_url`, and `confidence`.
  - [x] Every draft claim has a resolving `[E###]` citation; zero unresolved citations.
  - [x] Two-source rule is enforced for case outcomes, settlements, and restatements.

- [x] **Artifact Generation**:
  - [x] Markdown report contains valid markdown headers, risk summary table, and numbered footnotes.
  - [x] DOCX file is properly structured with cover styling, callouts, tables, and footnoted citations.
  - [x] PDF file compiles cleanly via ReportLab with cover page, risk badges, and formatting.

- [x] **Default Workflow & Agent Integration**:
  - [x] `DEFAULT_DO_RISK_REPORT_WORKFLOW_ID` (`0193e500-1111-7000-8000-000000000001`) is seeded and appears in `GET /api/workflows`.
  - [x] Workflow steps, dependencies, and edges render correctly in the visual DAG editor, including `step_validation_agent`.
  - [x] Both `do_risk_specialist` and `do_risk_validator` agent packages are registered in `agent_registry` with tools and skills.

- [x] **Automated Test Coverage**:
  - [x] Unit tests pass: `test_do_risk_report.py` (28/28 tests passed).
  - [x] Existing test suites pass without regression: `test_aggressive_researcher_orchestration.py`, `test_excel_specialist.py`, `test_pdf_report_artifact.py`.
  - [x] Zero syntax or lint errors.
