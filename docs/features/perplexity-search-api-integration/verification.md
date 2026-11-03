# Verification: Perplexity Search API Integration for D&O Workflow

**Datetime**: 2026-11-03T16:50:45+05:30  
**Feature Slug**: `perplexity-search-api-integration`

---

## 1. Unit & Integration Tests
- **Target File**: `backend/test_do_risk_report.py`
- **Command**:
  ```powershell
  backend\venv\Scripts\python.exe backend\test_do_risk_report.py
  ```
- **Tests Added**:
  1. `test_search_via_perplexity_search_api_empty_key`: Confirms `None` returned when API key is empty.
  2. `test_search_via_perplexity_search_api_mock`: Tests raw HTTP response parsing, `results_count`, snippet mapping, domain parsing, and source aggregation.
  3. `test_async_search_via_perplexity_search_api_mock`: Tests async invocation with backoff and retry handling.

---

## 2. Live API Direct Verification
- **Endpoint**: `https://api.perplexity.ai/search`
- **Test Query**: `NVIDIA DOJ antitrust inquiry Run:ai acquisition`
- **Result**:
  - HTTP Status: `200 OK`
  - Latency: `1.84s`
  - Results returned: 5 structured items
  - Snippet lengths: up to 3,096 characters per result
  - URLs: `news.bloomberglaw.com`, `dailyjournal.com`, `theregister.com`
  - Zero Perplexity completion tokens consumed

---

## 3. End-to-End Live Execution (NVIDIA)
- **Target**: NVIDIA Corporation (`NVDA`)
- **Mode**: `standard` (2 search rounds)
- **Command**:
  ```powershell
  backend\venv\Scripts\python.exe backend\run_do_risk_report.py NVDA --mode standard --format tree
  ```
- **Validation Criteria**:
  - Wall-clock time under 120s (vs. >400s previously)
  - 100% of queries successfully executed via Search API
  - Zero mock data injection
  - 11 complete sections retained
  - Running headers & `Page X of Y` footers on multi-page PDF
