# Feature: Advanced Workflow Blocks, DAG Edge Snapping, Expandable Nodes, Real Web Search, Perplexity API & Base Conversational Agent

*Created: 2026-10-28T20:58:00+05:30*  
*Status: Draft (Awaiting Approval)*

## Status

Draft

## Goal

1. **Diverse Workflow Block Types**: Enable workflows and the DAG execution engine to support 5 rich block primitives:
   - **Agent Steps** (LLM prompt execution with tool calling & knowledge base context)
   - **Conditionals** (If/Else branching expressions directing execution to True or False branches)
   - **Basic Python Code** (Pure sandboxed Python script execution for deterministic data transformation)
   - **Conditional Loop Back** (Conditionally repeat back to an earlier step with max-iteration guardrails)
   - **Create Artifact** (Produce persistent structured reports, markdown documents, or code files)
2. **Interactive DAG Canvas**:
   - **Dynamic Nearest-Edge Snapping**: Snap connection edges to the closest geometric boundary (Top, Bottom, Left, Right) between parent and child nodes instead of static top/bottom handles.
   - **Expandable Elements on Click**: Clicking any node in the DAG expands it into a rich visual editor showing full block details, code/prompts, inputs, and isolated unit test triggers; clicking again collapses it back.
3. **Advanced Agents & Real Web Search**:
   - **Real Web Searching**: Replace mock web search in the researcher agent with live search capabilities (DuckDuckGo live HTTP search + Google Search grounding).
   - **Perplexity API Integration**: Configure `PERPLEXITY_API_KEY` in `.env`, integrating `sonar` and `sonar-pro` models for live research citations.
   - **Base Conversational Agent (`general_assistant`)**: Add a general conversational agent for everyday dialogue without specialized multi-agent routing overhead.
   - **User Model Selection**: Allow users to explicitly choose underlying models (`gemini-2.5-flash`, `gemini-2.5-pro`, `sonar`, `sonar-pro`) per agent and per workflow step.

## Scope

### In scope:
- Data model extensions in `backend/app/workflows/models.py` (`step_type`, `code`, `condition_expr`, `true_target_step_id`, `false_target_step_id`, `loop_target_step_id`, `max_loop_iterations`, `artifact_title`, `artifact_type`).
- Workflow execution engine updates in `backend/app/workflows/engine.py` to handle conditionals, python code evaluation, loop iteration counters, and artifact generation.
- Perplexity API client helper and `.env` configuration (`PERPLEXITY_API_KEY`, `PERPLEXITY_MODEL`).
- Real web search service in `backend/app/agents/researcher/tools.py` with live web queries and citations.
- Creation of `backend/app/agents/general_assistant/` (base conversational agent).
- Support for Perplexity `sonar` and Gemini models in `backend/app/main.py`.
- Dynamic multi-handle edge snapping algorithm in `frontend/src/app/workflows/components/VisualGraphEditor.tsx` and `DataFlowEdge.tsx`.
- Expandable node components in React Flow DAG with block-specific editors.
- UI Block Palette in Workflow Studio to add Conditions, Python Code, Loops, Artifacts, and Agent steps.
- Unit and system testing support for all 5 block types.

### Out of scope:
- Arbitrary terminal shell access on the host system (all Python execution remains securely sandboxed).
- Modifying authentication providers outside Supabase.

## Current Behavior

- All workflow steps are treated as LLM agent steps (`WorkflowStep` has only `instructions` and `agent_id`).
- Workflow execution is strictly linear or topological without branching, loops, or inline Python scripts.
- React Flow edges only connect to static `Position.Top` and `Position.Bottom` handles, causing crossed or overlapping lines when nodes are arranged horizontally or in loops.
- DAG blocks are fixed cards with no inline expansion on click.
- Researcher's `web_search_query` tool returns hardcoded mock strings (`"Source 1 for: ..."`).
- Perplexity API is not integrated; no `PERPLEXITY_API_KEY` in environment.
- No general conversational base agent exists; prompts either hit the orchestrator or auto-route to specialized agents.
- Agents default to `gemini-2.5-flash` with limited UI ability to select specific models.

## Proposed Behavior

1. **Workflow Engine & Models**:
   - `WorkflowStep.step_type` supports `"agent"`, `"condition"`, `"python_code"`, `"loop"`, and `"artifact"`.
   - Condition steps evaluate expressions (e.g. `{{steps.check.output.status}} == 'passed'`) and conditionally activate downstream branches.
   - Python code steps execute pure Python in a sandboxed runner, returning structured dictionaries.
   - Loop steps check iteration counts against `max_loop_iterations` and loop back to target steps.
   - Artifact steps construct persistent markdown, code, or JSON assets.
2. **DAG Canvas Interaction**:
   - Nodes feature 4-way dynamic handles (`top`, `bottom`, `left`, `right`). Edges dynamically select the closest pair between source and target bounding boxes.
   - Clicking a node toggles its expanded state, rendering an inline block editor with syntax highlighting, parameter inputs, and unit test triggers.
3. **Agent Roster & Search**:
   - `general_assistant` package created under `backend/app/agents/general_assistant/`.
   - Real web search engine implemented with live DuckDuckGo querying and Perplexity API integration.
   - Model selection enables picking `gemini-2.5-flash`, `gemini-2.5-pro`, `sonar`, and `sonar-pro`.

## Implementation Steps

### Phase 1: Data Models & Execution Engine for All Block Types
1. Update `backend/app/workflows/models.py` to support `step_type`, `code`, `condition_expr`, `true_target_step_id`, `false_target_step_id`, `loop_target_step_id`, `max_loop_iterations`, `artifact_title`, and `artifact_type`.
2. Update `backend/app/workflows/engine.py` to execute each block type:
   - Condition evaluation & branch resolution.
   - Sandboxed Python code execution.
   - Loop iterations with safety counter.
   - Artifact generation and collection.
3. Add backend unit tests in `backend/test_endpoints.py` verifying all 5 block types.

### Phase 2: Real Web Search, Perplexity API & Base Conversational Agent
1. Update `backend/.env.example` and `backend/.env` with `PERPLEXITY_API_KEY` and `PERPLEXITY_MODEL`.
2. Implement real web search in `backend/app/agents/researcher/tools.py` using live HTTP querying + Perplexity API citations.
3. Create `backend/app/agents/general_assistant/` (config.json, prompt.md, skills.json, tools.py).
4. Update `backend/app/main.py` chat and test endpoints to support Perplexity `sonar` models via REST completions.
5. Add backend tests for real search, Perplexity fallback, and `general_assistant`.

### Phase 3: Frontend DAG Edge Snapping & Expandable Nodes
1. Update `frontend/src/app/workflows/types.ts` with new block fields.
2. Implement dynamic closest-edge snapping calculation in `frontend/src/app/workflows/components/VisualGraphEditor.tsx` and `DataFlowEdge.tsx`.
3. Build expandable node components in `VisualGraphEditor.tsx` with dedicated editors for Condition, Python Code, Loop, Artifact, and Agent.
4. Add block creation menu allowing users to add any of the 5 block types.

### Phase 4: Workflow Studio Cards & Block Editor Integration
1. Update `frontend/src/app/workflows/components/StepCardEditor.tsx` to edit all 5 block types.
2. Update `frontend/src/app/workflows/components/StepUnitTestModal.tsx` and `WorkflowSystemTestModal.tsx` to preview and test new block types.
3. Update agent editor modal in frontend to allow selecting models (`gemini-2.5-flash`, `gemini-2.5-pro`, `sonar`, `sonar-pro`).

### Phase 5: Verification & Full Validation
1. Run backend tests (`backend/test_endpoints.py`).
2. Run frontend lint (`npm --prefix frontend run lint`) and build (`npm --prefix frontend run build`).
3. Update `verification.md`, `qa-checklist.md`, and `CHANGELOG.md`.

## Files to Change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/models.py` | [MODIFY] | Add fields for condition, python code, loop, artifact blocks |
| `backend/app/workflows/engine.py` | [MODIFY] | Implement execution engine for 5 block types, branching, loops, artifacts |
| `backend/app/agents/researcher/tools.py` | [MODIFY] | Implement real web search and Perplexity API citation extraction |
| `backend/app/agents/general_assistant/*` | [NEW] | Base conversational agent package |
| `backend/app/main.py` | [MODIFY] | Add Perplexity API dispatching, model routing, and agent support |
| `backend/.env.example` | [MODIFY] | Add Perplexity configuration keys |
| `backend/test_endpoints.py` | [MODIFY] | Add comprehensive tests for new blocks, search, and models |
| `frontend/src/app/workflows/types.ts` | [MODIFY] | Add block types and fields to TypeScript definitions |
| `frontend/src/app/workflows/components/VisualGraphEditor.tsx` | [MODIFY] | Nearest-edge dynamic snapping and expandable click-to-edit nodes |
| `frontend/src/app/workflows/components/DataFlowEdge.tsx` | [MODIFY] | Support dynamic edge connection coordinates |
| `frontend/src/app/workflows/components/StepCardEditor.tsx` | [MODIFY] | Support all 5 block types in card editor |
| `frontend/src/app/workflows/components/StepUnitTestModal.tsx` | [MODIFY] | Test condition, python, loop, artifact blocks |
| `frontend/src/app/workflows/components/WorkflowSystemTestModal.tsx` | [MODIFY] | Display multi-block runs, branch execution, and artifacts |
| `frontend/src/app/agents/components/AgentEditorModal.tsx` | [MODIFY] | Add model dropdown selection |

## Interfaces

- `POST /api/workflows/{id}/run`: returns updated run with `artifacts`, `branch_traces`, and step outputs.
- `POST /api/workflows/{id}/steps/{step_id}/test`: runs isolated unit test on condition, python code, loop, or artifact blocks.
- `GET /api/agents`: includes `general_assistant` in roster.
- `POST /api/chat`: supports Perplexity `sonar` models when requested.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Infinite loops in workflow execution | High | Enforce strict `max_loop_iterations` (default 3, hard limit 10) in engine |
| Malicious code in Python script block | Medium | Sandbox execution in `tool_runner.py` with restricted builtins and execution timeout |
| Missing `PERPLEXITY_API_KEY` | Low | Graceful fallback to live DuckDuckGo web search or Gemini Google search grounding |
| Edge snapping layout jitter in React Flow | Low | Compute closest bounding-box edge using memoized geometric angle heuristics |

## Verification

- **Unit tests**: `& "backend\venv\Scripts\python.exe" -u backend/test_endpoints.py`
- **Frontend lint**: `npm --prefix frontend run lint`
- **Frontend build**: `npm --prefix frontend run build`
- **Manual checks**: Test Condition branching, Python code execution, Loopback iterations, Artifact generation, DAG click expansion, edge snapping, real web search, and Perplexity API.

## Rollout

- Add backward-compatible field defaults in `WorkflowStep` so existing workflows continue executing without modification.
- Add `PERPLEXITY_API_KEY` to `.env` with documentation in `.env.example`.
