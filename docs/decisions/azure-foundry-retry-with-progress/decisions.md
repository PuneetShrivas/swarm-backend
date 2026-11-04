# Architectural Decisions: Azure Foundry Multi-Round Retry & Visual Cooldown Progress

**Created Datetime**: 2026-11-04T14:48:55+05:30  
**Slug**: `azure-foundry-retry-with-progress`  
**Status**: Accepted

---

## 1. Outer Multi-Round Retry vs Immediate Exception
- **Context**: In high-load or parallel report generation, both primary and fallback models can encounter temporary 429 TPM exhaustion from Azure AI Foundry. Since TPM limits on Azure Foundry Anthropic models reset on a rolling 60-second window, aborting immediately forces manual re-runs and loses previously generated context.
- **Decision**: Wrap the model sequence execution in a multi-round loop (default: 5 rounds). If all models fail in a round, enter a structured cooldown pause before trying the primary model again.

---

## 2. Real-Time Terminal Visual Progress
- **Context**: Waiting 20–60 seconds silently gives the user an impression of a frozen process or dropped connection.
- **Decision**: Log real-time progress every 5 seconds with a visual progress bar, percentage completion, and countdown in seconds (`flush=True`), keeping the user fully informed that the system is actively waiting for quota replenishment and will automatically resume.

---

## 3. Transient vs Non-Transient Error Classification
- **Context**: If a request fails due to an invalid API key (HTTP 401) or bad request (HTTP 400), waiting for quota reset will never resolve the failure.
- **Decision**: Only enter the cooldown wait if the error message matches transient failure patterns (`429`, `rate limit`, `tpm`, `token`, `quota`, `500`, `502`, `503`, `504`, `timeout`, `connection`). Non-transient errors abort immediately.
