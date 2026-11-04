# QA Checklist: D&O Public Risk Report Accuracy, EDGAR XBRL Completeness, and Pipeline Anti-Contamination Fixes

**Created Datetime**: 2026-11-04T14:05:30+05:30  
**Last Updated Datetime**: 2026-11-04T14:05:30+05:30  
**Feature Slug**: `do-risk-report-accuracy-and-pipeline-fixes`  
**Status**: Complete

---

## Pre-Release Acceptance Criteria

- [x] **Anti-Contamination Guard**: When `TESTING != 'true'`, role exhaustion or upstream API failure raises an explicit `RuntimeError` rather than silently injecting foreign mock disclosures.
- [x] **Azure Concurrency Throttling**: `AZURE_SEMAPHORE = asyncio.Semaphore(2)` bounds concurrent Azure requests to avoid 429 TPM exhaustion.
- [x] **Role Tiering for Azure**: Fast/medium roles (`draft`, `verify`, `repair`, `plan`, `evidence_search`) execute on `claude-sonnet-4-6`, reserving `claude-opus-4-8` exclusively for synthesis.
- [x] **Generic Dynamic Mock Interpolation**: `_generate_mock_draft()` uses deterministic `SECTION SLUG:` / `SECTION HEADER:` parsing and interpolates `{co_name}`, `{ticker}`, `{cik}`, `{exchange}`. All legacy Apple/Foxconn disclosures are purged.
- [x] **Honest Upstream Failure Handling**: In `orchestrator.py`, section drafting failures produce localized, honest error notes without contaminating adjacent sections.
- [x] **Full XBRL Cash Flow Extraction**: Deterministically extracts Cash Flow from Operations (`NetCashProvidedByUsedInOperatingActivities` spanning ~360 days) with both latest annual and prior year comparative values.
- [x] **Full XBRL Balance Sheet Extraction**: Deterministically extracts Current Assets (`AssetsCurrent`), Current Liabilities (`LiabilitiesCurrent`), Total Stockholders' Equity (`StockholdersEquity`), and computes Net Working Capital.
- [x] **Authoritative Auditor Resolution**: `KNOWN_AUDITORS` correctly resolves `NVDA` to `PricewaterhouseCoopers LLP`, `MSFT` to `Deloitte & Touche LLP`, and `AAPL` to `Ernst & Young LLP`.
- [x] **Targeted Query Expansion**: Expanded search queries for `company_snapshot` (cryptocurrency mining GPU demand, SEC settlement history, official market cap) and `financial_overview` (debt maturities, revolving facilities, commercial paper, covenants).
- [x] **News Regex Broadening**: Regex detects `### UPDATES / PRESS RELEASES / NEWS`, `### NEWS & RECENT DEVELOPMENTS`, and all related variants using horizontal whitespace `[ \t]*` to prevent cross-line bleeding.
- [x] **Strict 12-Month News Cutoff**: Events prior to the 12-month calendar window from `current_date` and unresolvable date bullets are purged; standing governance verification notes are preserved.
- [x] **Prohibited Retention Commentary Purging**: Dollar retention figures (`$25M–$50M retention`) and pricing commentary in `SECURITIES CLASS ACTION RISK` are purged and replaced with compliant tower attachment framing.
- [x] **Single-Band Snapshot Conclusion**: Dual bands like `Elevated to High-Volatility` are collapsed to the single dominant band (`High-Volatility`), and AI exposure commentary is purged from the conclusion bullet.
- [x] **Market Cap Resolution**: Conflicting market cap quotes (`$4.88T vs $5.25T`) collapse to a single date-stamped quote.
- [x] **Automated Regression Suite**: All 87 unit and integration tests passing in `backend.test_do_risk_report` and full discover suite.
- [x] **Documentation Integrity**: Feature plan, implementation log, verification report, and ADR updated with Datetime timestamps.
