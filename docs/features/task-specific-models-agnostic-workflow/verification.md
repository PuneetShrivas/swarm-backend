# Verification: Task-Specific Models in Agnostic Workflow

Datetime: 2026-11-05T16:35:00+05:30

## Verification Strategy

Verify that:
1. `resolve_task_model()` respects the hierarchy: `task_models > ACTIVE_TASK_MODELS / env > model_override > provider tier default`.
2. CLI flags (`--plan-model`, `--extract-model`, `--draft-model`, `--synth-model`, `--task-models`) parse into a normalized dictionary.
3. Standalone workflow package maintains 0 imports from `backend/app/*`.
4. Orchestrator accurately passes task models down to section workers and overarching synthesis.
5. All automated unit tests in `backend/test_agnostic_research_report.py` and `agnostic_workflow/test_standalone_workflow.py` pass.

## Test Results

### 1. Backend Test Suite
Command:
```powershell
& '.\backend\venv\Scripts\python.exe' -m unittest backend/test_agnostic_research_report.py -v
```
Result:
```
Ran 23 tests in 0.425s
OK
```
Covered new tests:
- `test_resolve_task_model_hierarchy`
- `test_parse_task_models_cli`

### 2. Standalone Package Test Suite
Command:
```powershell
& '.\backend\venv\Scripts\python.exe' agnostic_workflow/test_standalone_workflow.py -v
```
Result:
```
Ran 15 tests in 0.328s
OK
```
Covered:
- `test_01_zero_app_imports`: 0 external imports from `app.*`
- `test_14_task_specific_models_hierarchy_and_cli`: Task models hierarchy & CLI parser validation

### 3. CLI Help Inspection
Validated both CLI entrypoints:
- `backend/run_agnostic_research_report.py --help`
- `agnostic_workflow/run_workflow.py --help`
Both display `--plan-model`, `--extract-model`, `--gap-model`, `--draft-model`, `--synth-model`, and `--task-models`.

### 4. Standalone Archive
Re-bundled: `agnostic_workflow.zip` (49,595 bytes).
