# Architectural Decisions: Pipeline Anti-Contamination, XBRL Completeness, and Concurrency Throttling

**Datetime**: 2026-11-04T12:15:31+05:30  
**Slug**: `do-risk-report-accuracy-and-pipeline-fixes`  
**Status**: Accepted

---

## 1. Complete Elimination of Silent Mock Fallback in Production Mode
- **Context**: In previous versions, if an LLM provider call failed (e.g. HTTP 429 TPM exhaustion or timeout), `run_role()` silently returned `_generate_mock_role_output()`. Because the mock function contained hardcoded Apple Inc. sample data, failures during an analysis of NVIDIA resulted in iPhone, Foxconn, and Apple litigation disclosures contaminating the NVIDIA report.
- **Decision**:
  - `_generate_mock_role_output()` must ONLY be invoked if `os.environ.get("TESTING") == "true"` or `mock_response` is explicitly provided.
  - In production / live CLI mode (`TESTING != "true"`), any unrecoverable role error must either raise an informative exception or emit a structured error block (`<Section>: Retrieval/Generation failure due to upstream API error: <details>`) rather than silently fabricating third-party disclosures.
  - Furthermore, `_generate_mock_draft` is refactored to generate synthetic data derived dynamically from the active `EntityCard` (using `entity.legal_name`, `entity.ticker`, and `entity.industry`), preventing hardcoded Apple data from existing even in tests.

---

## 2. Comprehensive Primary SEC EDGAR US-GAAP XBRL Extraction
- **Context**: The underwriter review identified that fundamental financial figures (Operating Cash Flow, Total Assets, Current Assets, Current Liabilities, Stockholders' Equity, Working Capital, and Auditor name) were marked "Not found in public disclosures", despite being explicitly disclosed in NVIDIA's Form 10-K.
- **Decision**:
  - Expand `EdgarFetcher.extract_xbrl_metrics()` to check primary US-GAAP concepts:
    - `NetCashProvidedByUsedInOperatingActivities`
    - `AssetsCurrent`
    - `LiabilitiesCurrent`
    - `StockholdersEquity` (and alternative US-GAAP equity tags)
    - Compute `WorkingCapital` deterministically as `AssetsCurrent - LiabilitiesCurrent`.
  - Ensure `TotalAssets` is added to the Evidence Ledger under both `company_snapshot` and `financial_overview`.
  - Implement reliable auditor resolution from 10-K filing metadata and an authoritative `KNOWN_AUDITORS` dictionary.

---

## 3. Azure Foundry Concurrency Throttling & Model Tier Distribution
- **Context**: Azure Foundry imposes strict Tokens Per Minute (TPM) limits on `claude-opus-4-8`. Firing 11 parallel sections concurrently resulted in 30–50 simultaneous requests hitting Opus, immediately exhausting TPM quotas and triggering 429 errors.
- **Decision**:
  - Distribute roles across sensible model tiers in `PROVIDER_MODELS["azure"]`:
    - `fast`: `claude-sonnet-4-6` (used for `extract` and `gap`)
    - `medium`: `claude-sonnet-4-6` (used for `draft` and `repair`)
    - `reasoning`: `claude-opus-4-8` (reserved for high-value `synthesize` executive verdicts)
  - Introduce an `asyncio.Semaphore(2)` (concurrency limit of 2) for Azure Foundry calls to smooth token throughput and prevent instantaneous TPM spikes.

---

## 4. Deterministic Enforcement of Negative Constraints & Prohibited Commentary
- **Context**:
  - The Underwriting Guidelines explicitly forbid pricing, limits, or attachment commentary ("NO pricing, limits or attachments commentary"). The mock draft generated prohibited retention commentary (`$25M–$50M primary retention shields excess D&O insurance tower layers`).
  - The prompt explicitly forbids AI exposure analysis in the Company Snapshot conclusion ("Do NOT include AI exposure analysis in this conclusion") and requires exactly one band.
- **Decision**:
  - Enhance `validator.py` with deterministic pruning rules:
    - Automatically detect and purge prohibited retention, pricing, and limits commentary.
    - Validate that section conclusions specify exactly ONE band (`Contained`, `Elevated`, `High-Volatility`, `Severe Tail Exposure`).
    - Strip any AI exposure sentences that leak into the Company Snapshot conclusion.
