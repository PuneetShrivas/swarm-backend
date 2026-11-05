# Decision: Task-Specific Models Architecture in Agnostic Workflow

Datetime: 2026-11-05T16:26:00+05:30

## Context

In complex multi-agent research pipelines, cognitive tasks vary drastically in token volume, required reasoning depth, and latency tolerance:
- **`plan`**: Needs concise formulation of 3–5 targeted search queries.
- **`extract`**: Processes high volumes of raw search snippets into atomic facts adhering to schema. Executed dozens of times per report. High TPM usage; benefits immensely from faster, cost-effective models (e.g. `gpt-5-mini` or `gemini-2.5-flash`).
- **`gap`**: Compares extracted facts with checklists; lightweight validation.
- **`draft`**: Generates institutional-grade analytical narratives citing evidence tokens. Requires high parameter count and nuanced long-form writing (e.g. `gpt-5.4` or `claude-sonnet-4-6`).
- **`synthesize`**: Multi-section executive reasoning and risk verdicts. Requires frontier reasoning capability (e.g. `claude-opus-4-8` or `gpt-5.4`).

Previously, specifying `--model` applied the single model universally across all tasks, causing either TPM rate limits during high-volume extraction or mediocre prose if a mini model was used everywhere.

## Considered Options

### Option 1: Static Role-to-Tier Mapping Only
- Hardcode model tiers in `ROLE_TIER_MAPPING` and force users to change env vars (`AZURE_FAST_MODEL`, `AZURE_MEDIUM_MODEL`, `AZURE_MODEL`).
- Pros: Simple.
- Cons: Inflexible; cannot be customized per run via CLI flags or programmatic API; cannot mix cross-provider models easily.

### Option 2: Unified Task-Model Registry with Hierarchical Resolution (Chosen)
- Provide explicit task model flags (`--plan-model`, `--extract-model`, `--gap-model`, `--draft-model`, `--synth-model`, `--task-models`), environment variable fallbacks, and dictionary API support (`task_models={"extract": "gpt-5-mini", "draft": "gpt-5.4"}`).
- Fall back gracefully: `Explicit Task Model > Task Env Var > Global Model (--model) > Provider Tier Default`.
- Automatically route endpoints dynamically based on model family for each task invocation.
- Pros: Complete flexibility, zero regressions, cost/speed optimization for extraction while preserving top-tier quality for drafting.

## Decision

Adopt **Option 2**.
Implement hierarchical model resolution for each role, pass `task_models` dict through the orchestrator pipeline, and expose both individual CLI flags and compound string mappings.
