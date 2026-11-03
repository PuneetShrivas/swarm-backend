# Feature: D&O Public Risk Report System & Default Workflow

Created At: 2026-11-03T12:42:00+05:30
Updated At: 2026-11-03T12:56:00+05:30
Status: Draft | Awaiting User Approval

## Status

Draft | Awaiting User Approval

## Goal

Implement an automated, high-performance, token-efficient, and fully traceable D&O (Directors and Officers) Public Risk Report generation system based on `agent-instructions/do_risk_report_system_spec.md`, configured with:
1. `agent-instructions/web-search-prompt.txt` as the official report structure and research specification template.
2. `agent-instructions/validation-prompt.txt` as the post-generation validation and correction template.
3. A dedicated post-generation **Validation Agent** (`do_risk_validator`) that executes the validation prompt with zero web access, enforcing date cutoffs, news deduplication/ordering, share price date relabeling, financial order, unsourced claim removal, and cross-section harmonization.
4. LLM inference exclusively on **Groq models** (`llama-3.1-8b-instant`, `llama-3.3-70b-versatile`, `deepseek-r1-distill-llama-70b`).
5. Live web search queues executed via **Perplexity Search API** with domain filters and snippet compaction.
6. Primary source SEC EDGAR filings & XBRL facts extracted deterministically in Python.
7. Final delivery as publication-grade Markdown, DOCX, and PDF artifacts with footnotes and a Limitations Appendix.

## Scope

- In scope:
  - **Default Templates Integration (`backend/app/workflows/do_risk_report/prompts/` and `template_spec.py`)**:
    - **Web Search & Structure Template (`web-search-prompt.txt`)**:
      - Company Snapshot (CPI score from Transparency International, ticker, market cap, share price, assets for latest reported quarter, revenue, capital structure, AI exposure).
      - Updates / Press Releases / News (12-month window, max 12 items, newest-first, claim triggers only, litigation duplication allowed).
      - Financial Overview (revenue trend descending, debt maturities consolidated into 1 line, credit rating, material weaknesses).
      - Analysts (bullish/neutral/bearish, peer beta & 52-week range).
      - Governance & Culture (board independence, 5-yr drift, CEO/CFO turnover).
      - Director & Officer History (max 8 individuals, mandatory officers first, 10-year horizon, identity match discipline `[matched: ...]`).
      - Strategic & Operational Profile.
      - Securities Class Action Risk (Likelihood, most likely allegation type, Severity, Side A / Side C, Tower interaction, Scenario max 2 lines, scale: Contained / Elevated / High-Volatility / Severe Tail Exposure).
      - Legal, Regulatory & Claims Context (ongoing & last 1 year lawsuits newest to oldest, nature of claim, parties, jurisdiction, outcome).
      - ESG, Cyber & Operational Exposure.
      - Forward-Looking Strategic Risk.
      - Overall D&O Underwriter Verdict (No new facts, Headline 2 bullets, dominant driver, tensions, unknowns, verbatim Band Register).
    - **Validation Rules Template (`validation-prompt.txt`)**:
      - Zero web access validation pass working strictly on report text.
      - Interpolates `{{currentDate}}` dynamically.
      - Enforces:
        - News 12-month calendar cutoff, newest-first ordering, within-window news protection, duplicate elimination.
        - Share price recency relabeling: if labeled "current/today" but date is older than latest trading day, relabel "last close (<stated date>)".
        - Revenue trend descending order check.
        - Superlative removal if not tied to dated event; uncompleted projects labeled "planned".
        - Removal of unsourced culture claims; trend claims on <2 data points replaced with "insufficient data to establish trend".
        - Cross-section date/name harmonization; empty headings filled with "Data unavailable.".
  - **Dedicated Validation Agent (`backend/app/agents/do_risk_validator/` & Workflow Step)**:
    - Registered as a full agent in `backend/app/agents/do_risk_validator/` (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`).
    - Executes as the post-generation verification step (`step_validation_agent`) in the workflow DAG before rendering artifacts.
    - Powered by Groq `llama-3.3-70b-versatile` or `deepseek-r1-distill-llama-70b` with temperature 0.0.
  - **LLM Engine Exclusively on Groq Models (`backend/app/workflows/do_risk_report/roles.py`, `backend/app/groq_client.py`)**:
    - `extract`, `gap`: `llama-3.1-8b-instant`.
    - `plan`, `draft`, `repair`: `llama-3.3-70b-versatile` or `qwen-2.5-32b`.
    - `synthesize`, `verify`: `llama-3.3-70b-versatile` or `deepseek-r1-distill-llama-70b`.
  - **Web Search Retrieval Queues via Perplexity (`backend/app/workflows/do_risk_report/retrieval.py`)**:
    - Dispatched through Perplexity Search with domain filters (courtlistener, sec.gov, justice.gov, credit agencies).
    - Snippet compaction (800 chars) and deduplication.
  - **Evidence Ledger Core (`backend/app/workflows/do_risk_report/ledger.py`)**:
    - `Evidence` Pydantic model (`id`, `section`, `claim`, `value`, `as_of`, `status`, `source_url`, `source_type`, `published`, `confidence`, `quote`).
    - Deduplication on `(claim, source_url)`.
  - **Primary Source SEC EDGAR Fetcher (`backend/app/workflows/do_risk_report/edgar.py`)**:
    - CIK resolution, Submissions API, and Company Facts XBRL API.
    - Populates financial facts into Evidence Ledger in deterministic Python code without LLM arithmetic.
  - **Publication Renderer (`backend/app/workflows/do_risk_report/renderer.py`)**:
    - Converts `[E###]` citations to styled footnotes.
    - Generates downloadable Markdown, DOCX (via `python-docx`), and PDF (via `reportlab`) artifacts.
    - Appends automated Limitations and Low-Confidence Appendix.
  - **Swarm Default Workflow Integration (`backend/app/workflows/default_workflows.py`)**:
    - Prebuilt default workflow `DEFAULT_DO_RISK_REPORT_WORKFLOW_ID` = `0193e500-1111-7000-8000-000000000001`.
    - Includes `do_risk_specialist` and `do_risk_validator` agents.

- Out of scope:
  - Claude models (eliminated per user request).
  - Web browsing within the Validation Agent (must have zero web access).

## Current behavior

- Current default workflow template (`0193e182-5af1-5bf1-bfe2-970663d16eb8`) is a generic 8-step competitive research pipeline.
- No D&O underwriting report structure matching `web-search-prompt.txt` exists.
- No automated post-generation validation agent enforcing `validation-prompt.txt` rules exists.
- No integrated Evidence Ledger data bus exists.

## Proposed behavior

1. **Entity Resolution & EDGAR Primary Extraction**:
   - Resolves ticker to CIK, extracts legal name, exchange, and financial facts from SEC XBRL.
2. **Pipelined Per-Section Research via Perplexity**:
   - Executes queries structured around `web-search-prompt.txt` sections via Perplexity search queues.
   - Groq `llama-3.1-8b-instant` extracts atomic claims into the Evidence Ledger.
3. **Traceable Section Drafting**:
   - Groq `llama-3.3-70b-versatile` drafts each section with `[E###]` citations.
4. **Executive Synthesis & Overall Verdict**:
   - Compiles Executive Summary and Overall D&O Underwriter Verdict with Band Register.
5. **Post-Generation Validation Agent**:
   - `do_risk_validator` runs the exact rules from `validation-prompt.txt` with `{{currentDate}}` interpolated.
   - Enforces news 12-month window cutoff, share price date relabeling, revenue-trend ordering, unsourced claim removal, and cross-section harmonization.
6. **Publication Rendering**:
   - Renderer converts citations to footnotes and exports validated Markdown, DOCX, and PDF artifacts.

## Implementation steps

1. **Store Default Prompt Templates**:
   - Save `web-search-prompt.txt` and `validation-prompt.txt` under `backend/app/workflows/do_risk_report/prompts/`.
   - Compile them into `template_spec.py` with section definitions, field checklists, and date interpolation.
2. **Build `backend/app/workflows/do_risk_report/` Subsystem**:
   - `models.py`: Pydantic data schemas.
   - `ledger.py`: Deduplicating Evidence Ledger.
   - `edgar.py`: SEC EDGAR fetcher.
   - `retrieval.py`: Perplexity Search queue client.
   - `roles.py`: Groq single worker `run_role`.
   - `validator.py`: Layer 1 deterministic checks + Validation Agent execution wrapper.
   - `renderer.py`: Markdown, DOCX, and PDF renderers.
   - `orchestrator.py`: Asyncio pipeline coordinator.
3. **Create Agents**:
   - `backend/app/agents/do_risk_specialist/`: Underwriting research and drafting.
   - `backend/app/agents/do_risk_validator/`: Dedicated post-generation validation and correction pass.
4. **Register Default Workflow Template**:
   - In `backend/app/workflows/default_workflows.py`, define and seed `DEFAULT_DO_RISK_REPORT_WORKFLOW_ID`.
5. **Add API Endpoints**:
   - Add `/api/do-risk-report/generate`, `/api/do-risk-report/templates`, `/api/do-risk-report/validate` in `backend/app/main.py`.
6. **Add Automated Test Suite**:
   - Create `backend/test_do_risk_report.py`.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/do_risk_report/__init__.py` | Create | Package initialization and module exports |
| `backend/app/workflows/do_risk_report/prompts/web_search_prompt.txt` | Create | Store default D&O Underwriting research & structure template |
| `backend/app/workflows/do_risk_report/prompts/validation_prompt.txt` | Create | Store default D&O Validation rules template |
| `backend/app/workflows/do_risk_report/models.py` | Create | Pydantic data models for Evidence, EntityCard, SectionSpec, and Report |
| `backend/app/workflows/do_risk_report/ledger.py` | Create | Evidence Ledger implementation with deduplication, querying, and JSONL persistence |
| `backend/app/workflows/do_risk_report/edgar.py` | Create | SEC EDGAR Submissions & XBRL API fetcher and Entity Card generator |
| `backend/app/workflows/do_risk_report/retrieval.py` | Create | Perplexity Search API queue client with domain filtering, caching, and result compactor |
| `backend/app/workflows/do_risk_report/template_spec.py` | Create | Pre-compiled D&O template from web_search_prompt.txt, static query library, and checklists |
| `backend/app/workflows/do_risk_report/roles.py` | Create | Groq single worker `run_role`, structured JSON schemas, and model tier mappings |
| `backend/app/workflows/do_risk_report/validator.py` | Create | Layer 1 deterministic and Validation Agent execution logic |
| `backend/app/workflows/do_risk_report/renderer.py` | Create | Markdown, DOCX (`python-docx`), and PDF (`reportlab`) document renderers |
| `backend/app/workflows/do_risk_report/orchestrator.py` | Create | Asyncio DAG orchestrator with pipelined execution and telemetry logging |
| `backend/app/agents/do_risk_specialist/config.json` | Create | Agent configuration metadata |
| `backend/app/agents/do_risk_specialist/prompt.md` | Create | D&O underwriting and forensic evaluation system instructions |
| `backend/app/agents/do_risk_specialist/tools.py` | Create | Agent tool call handlers for EDGAR, Ledger, Validation, and Rendering |
| `backend/app/agents/do_risk_specialist/skills.json` | Create | Agent skill definitions |
| `backend/app/agents/do_risk_specialist/mcp.json` | Create | MCP server configuration |
| `backend/app/agents/do_risk_validator/config.json` | Create | Validation Agent configuration metadata |
| `backend/app/agents/do_risk_validator/prompt.md` | Create | Validation Agent persona and rules based on validation-prompt.txt |
| `backend/app/agents/do_risk_validator/tools.py` | Create | Agent tool call handlers for date filtering, news ordering, and text verification |
| `backend/app/agents/do_risk_validator/skills.json` | Create | Validation skill definitions |
| `backend/app/agents/do_risk_validator/mcp.json` | Create | MCP server configuration |
| `backend/app/workflows/default_workflows.py` | Modify | Add D&O Public Risk Report default workflow definition and seeding |
| `backend/app/main.py` | Modify | Register D&O risk report endpoints and artifact persistence |
| `backend/test_do_risk_report.py` | Create | Comprehensive automated test suite for the D&O risk report system |

## Interfaces

- **API Endpoints**:
  - `POST /api/do-risk-report/generate`:
    - Request: `{"ticker": "AAPL", "mode": "standard", "template_id": "default_do_v1", "user_id": "..."}`
    - Response: `{"report_id": "...", "status": "completed", "ticker": "AAPL", "risk_tier": "Moderate", "artifacts": [...], "telemetry": {...}}`
  - `GET /api/do-risk-report/templates`:
    - Returns list of compiled section specs and validation checklists.
  - `POST /api/do-risk-report/validate`:
    - Request: `{"draft_text": "...", "current_date": "2026-11-03"}`
    - Response: `{"validated_report": "...", "modifications_applied": [...]}`

## Verification

- Unit tests:
  - `test_evidence_ledger_deduplication_and_citations`: Tests adding duplicates, resolving citations, and section-scoped reads.
  - `test_edgar_entity_and_xbrl_parsing`: Tests parsing SEC submissions and XBRL facts into typed financial claims.
  - `test_perplexity_search_queue_compaction`: Tests snippet length capping and domain filtering per workstream.
  - `test_validation_agent_rules`: Tests date cutoffs (12 months), newest-first news sorting, share price date relabeling, and unsourced culture claim removal.
  - `test_report_rendering_docx_pdf`: Verifies generation of Markdown, DOCX, and PDF artifacts with valid footnotes.
- Commands:
  - `cd backend && .\venv\Scripts\python.exe -m unittest test_do_risk_report.py`
  - `cd backend && .\venv\Scripts\python.exe -m unittest discover -p "test_*.py"`

## Rollout

1. Save prompt templates and build core modules under `backend/app/workflows/do_risk_report/`.
2. Implement specialized agents `do_risk_specialist` and `do_risk_validator`.
3. Add default workflow definition to `default_workflows.py`.
4. Register API endpoints in `backend/app/main.py`.
5. Run test suite to verify 100% test pass rate.
6. Verify workflow appears in UI DAG workflow dashboard.
