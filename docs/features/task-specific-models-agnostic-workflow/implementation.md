# Implementation: Task-Specific Models in Agnostic Workflow

Datetime: 2026-11-05T16:35:00+05:30

## Overview

Added the capability to configure different LLM models for different cognitive tasks (`plan`, `extract`, `gap`, `draft`, `synthesize`) in the prompt-driven agnostic research workflow.

## Key Changes

### 1. Hierarchical Task Model Resolver (`roles.py`)
Implemented `resolve_task_model()`, `set_task_model()`, `set_task_models()`, `get_task_models()`, and `ACTIVE_TASK_MODELS`:
```python
def resolve_task_model(
    role: str,
    task_models: Optional[Dict[str, str]] = None,
    model_override: Optional[str] = None,
    provider: Optional[str] = None,
) -> str:
    norm_role = "synthesize" if role.lower().strip() in ["synth", "synthesize"] else role.lower().strip()
    if task_models:
        cand = task_models.get(norm_role) or task_models.get(role)
        if cand and cand.strip():
            return cand.strip()

    if ACTIVE_TASK_MODELS.get(norm_role):
        return ACTIVE_TASK_MODELS[norm_role].strip()

    if model_override and model_override.strip():
        return model_override.strip()

    prov = (provider or ACTIVE_PROVIDER).lower()
    prov_models = PROVIDER_MODELS.get(prov, PROVIDER_MODELS.get("azure", {}))
    role_tier = ROLE_TIER_MAPPING.get(norm_role, "medium")
    return prov_models.get(role_tier, "claude-sonnet-4-6")
```

### 2. Orchestrator Task Model Dispatch (`orchestrator.py`)
- `_process_section()` and `run()` accept `task_models: Optional[Dict[str, str]] = None`.
- Dynamically resolves and logs specific models per task:
  - `plan_model = resolve_task_model("plan", task_models, model, provider)`
  - `extract_model = resolve_task_model("extract", task_models, model, provider)`
  - `gap_model = resolve_task_model("gap", task_models, model, provider)`
  - `draft_model = resolve_task_model("draft", task_models, model, provider)`
  - `synth_model = resolve_task_model("synthesize", task_models, model, provider)`
- Emits task model names in live progress badges:
  - `[*] [PLAN] [SECTION] (gpt-5-mini) Formulating targeted search queries...`
  - `[*] [EXTRACT] [SECTION] (gpt-5-mini) (R1/3) Extracting atomic evidence facts...`
  - `[*] [DRAFT] [SECTION] (gpt-5.4) Drafting narrative citing 14 evidence items...`
  - `[*] [SYNTH] [EXECUTIVE SUMMARY] (claude-opus-4-8) (1/2) Synthesizing cross-section insights...`
- Records `models` dictionary inside section telemetry and report metadata.

### 3. CLI Flags & Compound Mapping (`cli.py` & `run_workflow.py`)
- Added specific CLI arguments:
  - `--plan-model`
  - `--extract-model`
  - `--gap-model`
  - `--draft-model`
  - `--synth-model` / `--synthesize-model`
  - `--task-models "plan=gpt-5-mini,extract=gpt-5-mini,draft=gpt-5.4,synthesize=claude-opus-4-8"`
- Implemented `parse_task_models(args)` to normalize into a dictionary.
- Formatted CLI startup banner displaying active task model assignments.

### 4. Standalone Workflow Parity
- Replicated changes into `agnostic_workflow/roles.py`, `agnostic_workflow/orchestrator.py`, and `agnostic_workflow/run_workflow.py`.
- Re-bundled `agnostic_workflow.zip` (49,595 bytes).
