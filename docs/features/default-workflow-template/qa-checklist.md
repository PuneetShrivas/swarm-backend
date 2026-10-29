# QA Checklist: Default Workflow Template

**Created**: 2026-10-29T16:19:30+05:30
**Updated**: 2026-10-29T16:19:30+05:30

## Acceptance Criteria

- [x] **Multi-Agent Usage**: Default workflow utilizes 5 distinct agents (`researcher`, `data_analyst`, `coder`, `reviewer`, `synthesizer`/orchestrator).
- [x] **Diverse Block Types**: Workflow includes all 5 supported block types:
  - [x] `agent` (LLM prompt dispatch with live Perplexity Sonar for researcher)
  - [x] `python_code` (Sandboxed AST Python code execution)
  - [x] `condition` (Boolean dynamic expression evaluation)
  - [x] `loop` (Conditional iteration controller with max iteration guard)
  - [x] `artifact` (Persistent structured report generation)
- [x] **Unit Testing**:
  - [x] Python Code step unit test passes and outputs structured metric dictionary.
  - [x] Condition block unit test passes and resolves expected branch.
  - [x] Artifact step unit test passes and generates templated output.
- [x] **E2E Workflow Run**: Entire workflow DAG executes end-to-end, recording step run records, token consumption, and generating persistent artifacts.
- [x] **Availability to All Users**:
  - [x] Seeded automatically at startup into memory store.
  - [x] Set to `visibility: "public"`.
  - [x] Included in `GET /api/workflows` for all authenticated users.
  - [x] Dedicated discovery endpoint at `GET /api/workflows/defaults`.
- [x] **No Regressions**: All 46 existing endpoint tests continue to pass (total 50/50 tests passing).
- [x] **Documentation**: Full set of plan, implementation, verification, QA checklist, ADR, and changelog entries.
