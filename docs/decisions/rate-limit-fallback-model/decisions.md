# Architecture Decision Record: Rate Limit Failover to Secondary / Fallback Model

**Datetime**: 2026-11-03T21:19:00+05:30  
**Slug**: `rate-limit-fallback-model`  
**Status**: Accepted

---

## Context
High-parameter frontier models hosted on dedicated cloud deployments (such as `claude-opus-4-8` on Azure AI Foundry) often have strict Tokens Per Minute (TPM) quotas. During parallel section drafting (Stage 2 of the D&O pipeline, which runs multiple sections concurrently), token consumption can momentarily peak and trigger HTTP 429 rate limit errors (`TPM limit exceeded`).

Traditional exponential backoff pauses execution for 30–60 seconds, drastically increasing wall-clock latency. To circumvent this bottleneck, the user deployed `claude-sonnet-4-6` as a secondary deployment on the same Azure Foundry resource, which provides high throughput and separate TPM capacity.

---

## Decision
1. **Dynamic Model Failover Loop**:
   - For role executions, the system attempts the primary model (`selected_model`).
   - If an HTTP 429 error (or rate limit / capacity exhaustion) is detected:
     - If a fallback model is configured (`fallback_model_override`, `ACTIVE_FALLBACK_MODEL`, or `AZURE_FALLBACK_MODEL`), the role runner catches the 429, logs a notification, and immediately dispatches the prompt to the fallback model (`claude-sonnet-4-6`).
2. **Configuration Interfaces**:
   - **CLI Flag**: `--fallback-model` / `--secondary-model` (e.g. `--fallback-model claude-sonnet-4-6`).
   - **Environment Variable**: `AZURE_FALLBACK_MODEL="claude-sonnet-4-6"` (or generic `LLM_FALLBACK_MODEL`).
   - **Programmatic API**: `set_fallback_model(model)` and `get_fallback_model()`.
3. **Telemetry Transparency**:
   - The telemetry payload records the fallback model configured and which model was used.

---

## Consequences
- Prevents pipeline stalls when Opus 4.8 hits TPM thresholds: Sonnet 4.6 seamlessly takes over the impacted section draft.
- Retains 100% test reproducibility and offline safety (`TESTING=true`).
