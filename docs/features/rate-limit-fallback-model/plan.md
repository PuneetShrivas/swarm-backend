# Feature Plan: Rate Limit Fallback Model (`--fallback-model`, `AZURE_FALLBACK_MODEL`)

**Datetime**: 2026-11-03T21:18:00+05:30  
**Feature Slug**: `rate-limit-fallback-model`  
**Status**: Approved / In progress

---

## 1. Goal
Provide a resilient secondary / fallback model mechanism (configurable via `--fallback-model`, `--secondary-model`, or environment variable `AZURE_FALLBACK_MODEL` / `LLM_FALLBACK_MODEL`) that automatically circumvents 429 TPM (tokens per minute) rate limit errors on primary models like `claude-opus-4-8` by dynamically failing over to `claude-sonnet-4-6` without halting the pipeline.

---

## 2. Scope

### In Scope
1. **Configuration**:
   - Add `AZURE_FALLBACK_MODEL="claude-sonnet-4-6"` to `backend/.env`.
   - Add support for `LLM_FALLBACK_MODEL` as a generic environment fallback.
2. **Provider Engine (`roles.py`)**:
   - Add `ACTIVE_FALLBACK_MODEL`, `set_fallback_model()`, and `get_fallback_model()`.
   - Update `run_role()` and `run_role_with_timings()` to attempt the primary model, and upon detecting a 429 (rate limit) or transient capacity error, fail over immediately to the configured fallback model.
   - Support `fallback_model_override` in role execution.
3. **Orchestrator Integration (`orchestrator.py`)**:
   - Accept `fallback_model: Optional[str] = None` in `DORiskReportOrchestrator.run()`.
   - Pass fallback model to `set_fallback_model()`.
   - Record `fallback_model` in execution telemetry.
4. **CLI Integration (`cli.py`)**:
   - Add `--fallback-model` / `--secondary-model` arguments to `build_parser()`.
   - Display active fallback model in banner.
   - Pass fallback model to `orchestrator.run()`.
5. **Testing**:
   - Unit test fallback model resolution, CLI argument parsing, and simulated 429 failover.
   - Verify unit test suite with mock execution (`TESTING=true`).

### Out of Scope
- Running the overall live report generation test (per explicit user instruction: "do not run the overall test, that i will do myself").

---

## 3. Architecture & Failover Flow

```
[Section Task]
       │
       ▼
[Execute Role with Primary Model (e.g. claude-opus-4-8)]
       │
   ┌───┴───────────────────────────┐
   │                               │
Success (HTTP 200)         Rate Limit (HTTP 429) / TPM Exceeded
   │                               │
   ▼                               ▼
Return Parsed Result       [Check Fallback Model Available?]
                           (e.g. claude-sonnet-4-6)
                                   │
                           ┌───────┴───────┐
                           │               │
                          Yes              No
                           │               │
                           ▼               ▼
                 [Execute Role with   [Standard Retry /
                  Fallback Model]     Mock Fallback]
                           │
                           ▼
                  Return Parsed Result
                  (Zero downtime)
```
