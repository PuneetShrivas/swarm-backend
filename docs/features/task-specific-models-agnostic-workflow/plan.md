# Feature: Task-Specific Models in Agnostic Workflow

Datetime: 2026-11-05T16:26:00+05:30

## Status

Approved

## Goal

Allow users and orchestrators to specify different LLM models for different cognitive tasks (`plan`, `extract`, `gap`, `draft`, `synthesize`) in the prompt-driven agnostic research workflow. For example, high-speed, cost-effective models (e.g., `gpt-5-mini` or `gemini-2.5-flash`) can be used for search query planning and evidence claim extraction, while high-capacity frontier models (e.g., `gpt-5.4` or `claude-opus-4-8`) can be reserved for long-form narrative drafting and cross-section executive synthesis.

## Scope

- In scope:
  - Add task-specific model resolution in `roles.py` (`resolve_task_model`, `set_task_model`, `get_task_models`, `TASK_MODELS`).
  - Pass `task_models: Optional[Dict[str, str]]` through `AgnosticResearchOrchestrator.run()` and `_process_section()`.
  - Add CLI arguments in `backend/app/workflows/agnostic_research_report/cli.py` and `agnostic_workflow/run_workflow.py`:
    - `--plan-model`
    - `--extract-model`
    - `--gap-model`
    - `--draft-model`
    - `--synth-model` / `--synthesize-model`
    - `--task-models "plan=modelA,extract=modelA,draft=modelB,synthesize=modelC"`
  - Support environment variable configuration (`MODEL_PLAN`, `MODEL_EXTRACT`, `MODEL_GAP`, `MODEL_DRAFT`, `MODEL_SYNTHESIZE`).
  - Report task-to-model assignments in CLI startup banner and record per-task models in telemetry.
  - Maintain 100% synchronized behavior between `backend/app/workflows/agnostic_research_report/` and standalone `agnostic_workflow/`.
  - Update `agnostic_workflow.zip` archive.
  - Add comprehensive unit tests verifying task-specific model dispatch and fallback behavior.

- Out of scope:
  - Modifying external provider endpoint implementations.

## Current behavior

The orchestrator currently passes a single `model_override=model` parameter to `run_role()` across all stages. Every role (`plan`, `extract`, `gap`, `draft`, `synthesize`) is forced to execute on that single model, even though extraction and gap checking only require compact JSON parsing while drafting and synthesis demand high-parameter reasoning.

## Proposed behavior

1. Each role resolves its model using the priority hierarchy:
   - Explicit task override (CLI flag `--extract-model`, API `task_models={"extract": "gpt-5-mini"}`)
   - Task environment variable (`MODEL_EXTRACT` / `AZURE_EXTRACT_MODEL`)
   - Global model override (CLI `--model`)
   - Provider default tier model (`ROLE_TIER_MAPPING[role] -> PROVIDER_MODELS[provider][tier]`).
2. When executing across model families on Azure Foundry (e.g. OpenAI `gpt-5-mini` for extraction and Anthropic `claude-opus-4-8` for synthesis), the orchestrator automatically routes each request to its respective endpoint (`/openai/v1/responses` vs `/anthropic/v1/messages`) via dynamic endpoint resolution.
3. Telemetry and CLI startup banner display the exact task-to-model mapping.

## Implementation steps

1. Update `roles.py` (both backend and standalone):
   - Add `resolve_task_model(role, task_models, default_model, provider)`.
   - Add `set_task_models(mapping)` and `get_task_models()`.
   - Update `run_role` to resolve task model cleanly if `role` is specified.
2. Update `orchestrator.py` (both backend and standalone):
   - Add `task_models: Optional[Dict[str, str]] = None` to `run()` and `_process_section()`.
   - Dispatch role-specific model for `plan`, `extract`, `gap`, `draft`, and `synthesize`.
   - Track models used in subsection telemetry.
3. Update `cli.py` and `run_workflow.py`:
   - Add CLI arguments `--plan-model`, `--extract-model`, `--gap-model`, `--draft-model`, `--synth-model`, and `--task-models`.
   - Parse into a normalized dictionary and pass to `orchestrator.run()`.
   - Display task-model mapping in header.
4. Add unit test suites in `backend/test_agnostic_research_report.py` and `agnostic_workflow/test_standalone_workflow.py`.
5. Repack `agnostic_workflow.zip`.
6. Run full test suite and verify clean test passes.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/agnostic_research_report/roles.py` | Add task model resolution functions | Allow roles to determine model based on task |
| `backend/app/workflows/agnostic_research_report/orchestrator.py` | Accept and pass `task_models` dict | Dispatch assigned models per task |
| `backend/app/workflows/agnostic_research_report/cli.py` | Add task model CLI flags and display in banner | Enable CLI user configuration |
| `agnostic_workflow/roles.py` | Replicate task model resolution functions | Maintain standalone parity |
| `agnostic_workflow/orchestrator.py` | Replicate `task_models` handling | Maintain standalone parity |
| `agnostic_workflow/run_workflow.py` | Replicate task model CLI flags and display | Maintain standalone parity |
| `backend/test_agnostic_research_report.py` | Add unit tests for task-specific model routing | Verification and regression prevention |
| `agnostic_workflow/test_standalone_workflow.py` | Add unit tests for standalone task models | Verification and regression prevention |
| `agnostic_workflow.zip` | Re-bundle package archive | Keep standalone archive synchronized |

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Mixing OpenAI and Anthropic models on Azure Foundry in one run | Headers or payloads might mismatch | `resolve_foundry_endpoint` and `_execute_azure_chat_with_tokens` already branch based on model name family dynamically |
| Backward compatibility | Existing scripts passing `--model` might break | `--model` remains the default for any role not explicitly overridden |
| Invalid task name in `--task-models` | Typos like `pla=model` ignored | Validate task names against `{'plan', 'extract', 'gap', 'draft', 'synthesize', 'verify'}` and raise friendly parser error |
