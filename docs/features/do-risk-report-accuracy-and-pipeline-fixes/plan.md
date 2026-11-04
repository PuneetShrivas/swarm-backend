# Feature: D&O Public Risk Report Accuracy, EDGAR XBRL Completeness, and Pipeline Anti-Contamination Fixes

**Created Datetime**: 2026-11-04T12:15:31+05:30  
**Last Updated Datetime**: 2026-11-04T14:05:40+05:30  
**Feature Slug**: `do-risk-report-accuracy-and-pipeline-fixes`  
**Status**: Complete

---

## Goal

Resolve all quality, factual, structural, and retrieval defects identified in the underwriter review of the NVIDIA report (`agent-instructions/review_for_generated_report.md`):
1. **Eliminate Cross-Company Data Contamination**: Completely eradicate silent mock fallback in live execution mode so data from Apple or other entities can never leak into an analyzed company's report.
2. **Complete SEC EDGAR US-GAAP XBRL Financial Extraction**: Directly extract Operating Cash Flow, Total Assets, Current Assets, Current Liabilities, Stockholders' Equity (Net Worth), Working Capital, and Auditor name from authoritative SEC filings, eliminating "Not found" retrieval gaps.
3. **Harmonize Company Snapshot & Negative Constraints**: Surface well-documented crypto exposure, resolve conflicting market cap figures into a single definitive date-stamped number, enforce a single risk band conclusion, and strictly exclude AI exposure from the Snapshot conclusion per prompt rules.
4. **Enforce 12-Month News Window & Claim-Trigger Focus**: Ensure all news items fall strictly within the 12 months preceding the analysis date and adhere to the prescribed D&O claim-trigger format.
5. **Enforce Prescribed Securities Class Action & Legal Context Structure**: Enforce exact underwriting subsections (Jurisdiction, Likelihood, Most Likely Allegation Theory, Severity, Side A / Side C Split, Tower Interaction), purge prohibited retention/pricing commentary, and guarantee Legal & Regulatory is never dropped or duplicated.
6. **Azure Concurrency & Rate Limit Resiliency**: Implement concurrency-bounded throttling (asyncio Semaphore) and tiered model selection (`claude-sonnet-4-6` for fast/medium, `claude-opus-4-8` for reasoning) to eliminate 429 TPM exhaustion on Azure Foundry.

---

## Scope

### In Scope
- **`backend/app/workflows/do_risk_report/roles.py`**:
  - Remove silent mock fallback when `TESTING != "true"`. Fail loudly or mark specific section as failed instead of substituting fake data.
  - Decouple mock generator from hardcoded Apple data, generating entity-aware mock data based on the active `EntityCard`.
  - Fix section matching in `_generate_mock_draft` to use exact `section_name`.
  - Configure sensible Azure model tiers in `PROVIDER_MODELS["azure"]` (`fast` / `medium` -> `claude-sonnet-4-6`, `reasoning` -> `claude-opus-4-8`).
  - Add `asyncio.Semaphore` to throttle concurrent Azure API calls and prevent 429 TPM spikes.
- **`backend/app/workflows/do_risk_report/edgar.py`**:
  - Add extraction for `NetCashProvidedByUsedInOperatingActivities` (Operating Cash Flow).
  - Add extraction for `AssetsCurrent` (Current Assets), `LiabilitiesCurrent` (Current Liabilities), and `StockholdersEquity` (Net Worth).
  - Compute deterministic `working_capital = AssetsCurrent - LiabilitiesCurrent`.
  - Populate `Assets` in both `financial_overview` and `company_snapshot`.
  - Add auditor resolution from 10-K metadata and `KNOWN_AUDITORS` dictionary.
- **`backend/app/workflows/do_risk_report/template_spec.py`**:
  - Add targeted queries for tech/semiconductor crypto mining GPU exposure.
  - Add targeted queries for 10-K debt maturity schedules, coupon ranges, and credit facilities.
  - Enforce explicit negative constraints in section prompts (e.g. "Do NOT include AI exposure in Company Snapshot conclusion", "Provide exactly ONE band").
- **`backend/app/workflows/do_risk_report/validator.py`**:
  - Broaden news header regex to match `### NEWS & RECENT DEVELOPMENTS`, `### UPDATES / PRESS RELEASES / NEWS`, etc.
  - Strictly enforce 12-month calendar cutoff against `current_date`.
  - Add deterministic check to eliminate prohibited retention, pricing, and limits commentary in SCA sections.
  - Add check resolving multiple conflicting market caps to the latest single date-stamped quote.
  - Enforce single-band formatting for section conclusions.
- **`backend/test_do_risk_report.py`**:
  - Add comprehensive automated unit tests covering all fixes.

### Out of Scope
- Modifying UI frontend components.
- Changing third-party search providers outside Perplexity.

---

## Current Behavior

1. **Silent Mock Fallback**: In `roles.py`, when Azure Foundry returns 429 or times out, `run_role()` catches the error and silently calls `_generate_mock_role_output()`. This function has hardcoded Apple data from 2023-2024 (smartphones, 2.2B install base, Foxconn/Luxshare, Ernst & Young, DOJ smartphone antitrust lawsuit).
2. **Duplicated / Dropped Sections**: In `_generate_mock_draft()`, keyword matching on `user_input.lower()` matches `news` inside the master prompt of `legal_regulatory_claims`, replacing the entire Legal & Regulatory section with a duplicate of the Apple News section.
3. **Financial "Not Found" Defect**: `edgar.py` only extracts Revenues, Assets, and Debt from XBRL facts. Operating Cash Flow, Current Assets, Current Liabilities, Stockholders' Equity, and Working Capital are omitted, despite being readily available in SEC EDGAR. Auditor name is hardcoded to "Independent Registered Public Accounting Firm" for all non-Apple companies.
4. **Snapshot Crypto & Market Cap Defects**: Crypto mining GPU exposure is missed because queries are generic, and cross-section evidence (e.g. `E122` SEC settlement) is not shared. Two conflicting market caps ($4.88T vs $5.25T) are printed without resolution. Conclusion violates the negative constraint by discussing AI concentration and gives a dual band ("Elevated to High-Volatility").
5. **12-Month Cutoff Bypass**: In `validator.py`, the regex only checks for `### UPDATES / PRESS RELEASES / NEWS`, completely missing headers formatted as `### NEWS & RECENT DEVELOPMENTS`.

---

## Proposed Behavior

1. **Zero Fake Data Contamination**:
   - In production (`TESTING != 'true'`), `run_role()` never silently substitutes mock data. If a provider fails after retries, it raises a transparent error or records an explicit retrieval failure note for that field.
   - `_generate_mock_draft` generates dynamic, entity-aware test fixtures using `EntityCard` metadata (legal name, ticker, SIC, industry).
   - Exact `section_name` matching eliminates section shadowing.
2. **Complete 10-K XBRL Extraction**:
   - `edgar.py` deterministically populates Operating Cash Flow, Total Assets, Current Assets, Current Liabilities, Total Equity, and Working Capital directly from SEC facts without LLM hallucination.
   - Accurate auditor resolution (e.g. PricewaterhouseCoopers LLP for NVIDIA).
3. **Snapshot Integrity & Negative Constraint Enforcement**:
   - Crypto mining GPU revenue exposure and 2022 SEC settlement are surfaced via targeted search and ledger sharing.
   - Single date-stamped market cap figure is resolved and validated.
   - Company Snapshot conclusion strictly excludes AI concentration and outputs exactly one band (`Contained`, `Elevated`, or `High-Volatility`).
4. **Strict 12-Month News Window & D&O Format**:
   - Validator regex matches all header variants and strips any event older than 12 months from `current_date`.
   - Formats items strictly as `DD-MMM-YYYY - event - [category] - D&O relevance - source`.
5. **Standardized SCA Underwriting Structure & Retention Cleanliness**:
   - Generates exact subsections: `JURISDICTION`, `LIKELIHOOD`, `MOST LIKELY ALLEGATION TYPE`, `SEVERITY IF BROUGHT`, `SIDE A / SIDE C EXPOSURE`, `TOWER INTERACTION`, `SCENARIO`, `CONCLUSION`.
   - Purges all prohibited retention, pricing, and attachment commentary.
6. **Azure Rate-Limit Protection**:
   - `asyncio.Semaphore(2)` limits concurrent calls to Azure Foundry.
   - Fast and medium roles use `claude-sonnet-4-6`; reasoning roles use `claude-opus-4-8` with fallback to `claude-sonnet-4-6`.

---

## Implementation Steps

1. **Step 1: Anti-Contamination & Azure Concurrency in `roles.py`**:
   - Add `asyncio.Semaphore` for Azure/provider concurrency control.
   - Adjust `PROVIDER_MODELS["azure"]` tiers (`fast`: `claude-sonnet-4-6`, `medium`: `claude-sonnet-4-6`, `reasoning`: `claude-opus-4-8`).
   - Remove silent mock fallback when `TESTING != "true"`.
   - Rewrite `_generate_mock_draft` to use exact section names and dynamic entity cards.
2. **Step 2: Full XBRL Financial Extraction & Auditor Resolution in `edgar.py`**:
   - Add `OperatingCashFlow`, `AssetsCurrent`, `LiabilitiesCurrent`, `StockholdersEquity`, and `WorkingCapital` to `extract_xbrl_metrics()`.
   - Populate `Assets` in both `financial_overview` and `company_snapshot`.
   - Add `KNOWN_AUDITORS` mapping and 10-K auditor extraction.
3. **Step 3: Query Expansion & Negative Constraints in `template_spec.py`**:
   - Add crypto GPU queries and 10-K debt schedule queries.
   - Reinforce negative prompt constraints in section instructions.
4. **Step 4: Deterministic Validation Enhancements in `validator.py`**:
   - Broaden news header regex for 12-month filtering.
   - Add market cap resolution and prohibited retention commentary purger.
   - Enforce single-band conclusion format.
5. **Step 5: Automated Testing & Verification in `backend/test_do_risk_report.py`**:
   - Add unit tests for all new XBRL metrics, anti-contamination guards, news cutoff regex, and SCA structure validation.

---

## Files to Change

| File | Change | Reason |
| :--- | :--- | :--- |
| `backend/app/workflows/do_risk_report/roles.py` | Add concurrency semaphore, update Azure model tiers, eliminate silent mock fallback in live mode, fix mock generator | Prevent 429 TPM exhaustion, prevent fake company data leakage |
| `backend/app/workflows/do_risk_report/edgar.py` | Extract OCF, Current Assets/Liabs, Equity, Working Capital, and Auditor | Eliminate "Not found" financial retrieval failures |
| `backend/app/workflows/do_risk_report/template_spec.py` | Add crypto GPU queries, debt queries, and negative constraints | Surface crypto exposure and enforce prompt rules |
| `backend/app/workflows/do_risk_report/validator.py` | Fix news header regex, purge retention commentary, enforce single band, resolve market cap | Enforce 12-month window, remove prohibited text, resolve data conflicts |
| `backend/test_do_risk_report.py` | Add comprehensive unit tests | Verify 100% test coverage and regression safety |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :---------- |
| Azure Foundry 429 rate limit recurrence | High latency or aborted calls | Bounded semaphore concurrency (`Semaphore(2)`) + Sonnet for fast/medium roles |
| Company has non-standard XBRL tags for cash flow or equity | Missing financial metrics | Check multiple common US-GAAP alternative tags (`NetCashProvidedByUsedInOperatingActivities`, `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations`, etc.) |
| Removing silent mock fallback breaks test suite | Unit test failures | Retain mock output strictly when `TESTING == "true"` or `mock_response` is provided |

---

## Verification

- **Unit tests**:
  - `test_xbrl_extraction_mandatory_metrics`: Verify OCF, Assets, Current Assets/Liabs, Equity, Working Capital.
  - `test_no_silent_mock_fallback_in_live_mode`: Verify exceptions/degradation in live mode instead of mock.
  - `test_news_header_regex_variants_and_cutoff`: Verify 12-month cutoff across diverse header strings.
  - `test_retention_commentary_purged`: Verify prohibited retention statements are removed.
- **Commands**:
  ```powershell
  $env:PYTHONPATH="backend"; $env:TESTING="true"; backend\venv\Scripts\python.exe -m unittest backend.test_do_risk_report
  ```
