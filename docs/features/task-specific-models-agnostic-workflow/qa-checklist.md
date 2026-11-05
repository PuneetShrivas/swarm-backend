# QA Checklist: Task-Specific Models in Agnostic Workflow

Datetime: 2026-11-05T16:35:00+05:30

- [x] `resolve_task_model` correctly resolves models per task role (`plan`, `extract`, `gap`, `draft`, `synthesize`).
- [x] Explicit `task_models` dict overrides global `--model`.
- [x] Non-overridden tasks fall back gracefully to global `--model`.
- [x] CLI flags (`--plan-model`, `--extract-model`, `--gap-model`, `--draft-model`, `--synth-model`) are supported.
- [x] Compound CLI flag (`--task-models "plan=model1,extract=model2,draft=model3"`) is supported.
- [x] CLI header displays breakdown of assigned models when task overrides are active.
- [x] Progress messages report active model per task (`[PLAN] [SEC] (model)`).
- [x] Parity preserved across `backend/app/workflows/agnostic_research_report/` and `agnostic_workflow/`.
- [x] Zero imports from `backend/app/*` in `agnostic_workflow/`.
- [x] `agnostic_workflow.zip` updated with task models capability.
- [x] Backend test suite passes (23/23 tests).
- [x] Standalone test suite passes (15/15 tests).
