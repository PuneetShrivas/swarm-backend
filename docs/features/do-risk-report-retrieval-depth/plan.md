# Feature: Perplexity Retrieval Timeout Extension & Comprehensive Research Extraction

**Datetime**: 2026-11-03T15:55:00+05:30  
**Feature Slug**: `do-risk-report-retrieval-depth`  

## Status

Approved

## Goal

Resolve the data omission issue where the live D&O underwriting report generated extensive "Not found in public disclosures" statements due to Perplexity HTTP timeouts (15s) and restrictive domain site filtering. Deliver comprehensive, rich real-world facts from Perplexity across all 11 sections so that Groq can extract dozens of verified claims and produce exhaustive institutional-grade report sections.

## Scope

- In scope:
  - Increase Perplexity API HTTP timeout from 15.0s to 60.0s (`PERPLEXITY_TIMEOUT_SECONDS = 60.0`).
  - Eliminate restrictive `(site:domain1 OR site:domain2)` query query-string filters that cause Perplexity to fail on paywalled domains; convert domain guidance into system prompt domain prioritization.
  - Fix Perplexity snippet extraction in `retrieval.py` to deliver full grounded answer content (up to 1,500 chars) and per-citation findings to Groq `extract` role, rather than single sliced lines (`lines[i]`).
  - Optimize Groq extraction prompt and concurrency handling so that Groq extracts 5–15 atomic claims per section from rich Perplexity content.
  - End-to-end verification of live standard run to confirm data richness across Snapshot, News, Governance, Analysts, Strategic Profile, and ESG.
- Out of scope:
  - Modifying SEC EDGAR XBRL extraction (already working with 100% accuracy).
  - Modifying ReportLab `NumberedCanvas` or PDF styling (already verified).

## Current behavior

1. `retrieval.py` hardcodes `timeout=15.0` in `httpx.AsyncClient`. During concurrent execution across 11 sections, Perplexity queries exceeded 15.0s, throwing `httpx.ReadTimeout` (logged as `Perplexity live search error: `).
2. `enhanced_query` injected hard boolean filters like `(site:reuters.com OR site:wsj.com)`. Because financial consensus and legal dockets on those specific domains are frequently paywalled or blocked, Perplexity returned empty or near-empty results.
3. `_execute_live_search` paired citation `i` with `lines[i]` of the answer. When the answer began with a header or table border, `snippet` was truncated to a single non-substantive line, leaving Groq's `extract` role with zero extractable facts.

## Proposed behavior

1. Configurable timeout with default `PERPLEXITY_TIMEOUT_SECONDS = 60.0` (with 1 retry for transient timeouts).
2. Clean, unconstrained search queries sent to Perplexity `sonar`, allowing it to retrieve and synthesize from all public indexes (Yahoo Finance, Bloomberg, MarketWatch, CourtListener, S&P, SEC).
3. Primary research synthesis snippet provided with full context (up to 1,500 characters) plus individual cited source entries, ensuring Groq receives comprehensive text for fact extraction.
4. Groq extract role will extract dozens of verified claims, populating all 11 sections with rich data.

## Implementation steps

1. Update `backend/app/workflows/do_risk_report/retrieval.py`:
   - Set `DEFAULT_PERPLEXITY_TIMEOUT = 60.0`.
   - Remove hard `(site:...)` boolean filter in `enhanced_query`; pass natural search queries while providing source guidance in the system prompt.
   - Refactor `_execute_live_search` response parsing: always include a full-synthesis primary result (up to 1,500 characters) and structured cited source items with adequate context.
   - Add timeout retry in `search()`.
2. Update `backend/test_do_risk_report.py`:
   - Add unit tests verifying `clean_snippet` with multi-paragraph text and timeout configuration.
   - Verify all 39 tests pass.
3. Execute end-to-end live test in standard mode (`--mode standard`) and evaluate real data coverage across all 11 sections.
4. Update feature documentation and commit.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/do_risk_report/retrieval.py` | Timeout to 60s, remove restrictive `site:` filter, deliver full answer snippets | Fix search timeouts and snippet truncation |
| `backend/test_do_risk_report.py` | Add tests for new retrieval configurations | Ensure test coverage |
| `CHANGELOG.md` | Document retrieval depth and timeout extension | Keep a Changelog compliance |

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Longer timeout could increase total wall-clock time if an endpoint hangs | Pipeline takes longer | The 60s timeout applies per-request; successful requests finish in 4–8s. Semaphore of 5 prevents request flooding. |
| High token count in compacted text | Exceeds Groq context window | `clean_snippet` caps each snippet at 1,500 chars, well within Groq's 32k/128k context window. |

## Verification

- Unit tests: Run `backend/test_do_risk_report.py` with 100% pass rate.
- Live test: Run `run_do_risk_report.py AAPL --mode standard` and confirm:
  - 0 Perplexity timeout errors.
  - Multi-claim extraction across sections (Analysts, Governance, News, Strategic Profile).
  - Vast reduction in "Not found in public disclosures" placeholders.
