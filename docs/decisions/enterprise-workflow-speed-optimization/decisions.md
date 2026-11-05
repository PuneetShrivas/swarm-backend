# Architecture Decisions: Enterprise Workflow Speed Optimization

**Created**: 2026-11-05T19:20:10+05:30  
**Slug**: `enterprise-workflow-speed-optimization`  
**Status**: Decided (Pending User Approval)

---

## Decision 1: Default Asymmetric Role-to-Model Tiering

### Context:
In previous iterations, passing `--model gpt-5.4` or `--model claude-opus-4-8` assigned that model globally to all roles (`plan`, `extract`, `gap`, `draft`, `synthesize`). Fact extraction and gap analysis represent 76.3% of total pipeline compute time (3,416 seconds out of 4,477 seconds). Premium reasoning models have lower token output throughput and strict rate limits (e.g. 8,000 output tokens/minute), which causes massive queue latency and frequent 429 backoff sleeps.

### Decision:
Implement **Smart Asymmetric Tiering** by default:
- When a user specifies `--model <name>`, it is assigned to the heavy cognitive roles: `draft` and `synthesize`.
- The structural transformation roles (`extract` and `gap`) default to the provider's `fast` tier (e.g., `gpt-5-mini`, `claude-sonnet-4-6`, `gemini-2.5-flash`), which process tokens 5x–15x faster with 10x higher rate limits.
- Operators who explicitly wish to force a single model across all roles can supply `--all-roles-model <name>`.
- Explicit task overrides (`--extract-model`, `--draft-model`, etc.) always retain highest precedence.

### Alternatives Considered:
1. *Require users to type all CLI flags every time (`--extract-model gpt-5-mini --draft-model gpt-5.4`)*: Rejected because typical users run with a single `--model` flag, leading to severe unexpected slowdowns and 429 rate limit errors.
2. *Always force fast models with no override*: Rejected because users must retain full control over exact model choices.

---

## Decision 2: Role-Segregated Dual Semaphores

### Context:
All LLM requests previously went through a single global semaphore: `AZURE_SEMAPHORE = asyncio.Semaphore(3)`. Across 10 parallel sections, 70+ requests queued up behind long 40-second drafting operations, creating severe head-of-line blocking.

### Decision:
Split concurrency into two separate pools:
1. `SEMAPHORE_FAST` (concurrency: 12) for lightweight tasks: `plan`, `extract`, `gap`, `verify`.
2. `SEMAPHORE_HEAVY` (concurrency: 4) for heavy generative tasks: `draft`, `synthesize`.

### Impact:
- Fast extraction tasks run immediately without waiting for draft tasks.
- Heavy draft tasks are safely metered to avoid bursting provider TPM/RPM limits.

---

## Decision 3: Adaptive Depth & Upfront Batch Planning

### Context:
The workflow unconditionally ran 3 rounds per section in `deep` mode. Telemetry analysis showed that Round 1 extracted 15–25 facts, while Rounds 2 and 3 yielded only 3–5 marginal facts while costing over 60 seconds per round.

### Decision:
1. Expand Round 1 planning to generate 4–6 comprehensive queries addressing all checklist fields simultaneously, executed in one parallel Perplexity batch.
2. Introduce an **Adaptive Sufficiency Gate**: If Round 1 achieves >= 10 verified claims and addresses required fields, terminate the iterative loop immediately and begin drafting.
3. Cap `deep` mode at 2 rounds when additional queries are needed, and keep `fast` mode at 1 round.

---

## Decision 4: In-Memory Session Query Caching for Perplexity

### Context:
Across 10 sections, multiple sections frequently issue overlapping queries (e.g. NVIDIA 10-K filings, Q3/Q4 earnings, board leadership).

### Decision:
Implement an in-memory session query cache in `PerplexitySearchQueue`. Normalized query strings are matched in memory. Cache hits return instant results with 0ms network latency. The cache is strictly session-scoped and does not persist across separate runs, avoiding stale data risks.
