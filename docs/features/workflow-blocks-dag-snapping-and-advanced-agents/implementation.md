# Implementation Log: Advanced Workflow Blocks, DAG Edge Snapping, Expandable Nodes, Real Web Search, Perplexity API & Base Conversational Agent

*Created: 2026-10-28T20:58:00+05:30*  
*Status: Ready for Implementation upon Plan Approval*

## Implementation Checklist

### Phase 1: Data Models & Execution Engine for All Block Types
- [ ] Update `backend/app/workflows/models.py` with `step_type`, `code`, `condition_expr`, `true_target_step_id`, `false_target_step_id`, `loop_target_step_id`, `max_loop_iterations`, `artifact_title`, `artifact_type`.
- [ ] Update `backend/app/workflows/engine.py` with multi-block execution (conditions, python code, loops, artifacts).
- [ ] Add unit and system tests in `backend/test_endpoints.py` for all 5 block types.

### Phase 2: Real Web Search, Perplexity API & Base Conversational Agent
- [ ] Update `backend/.env.example` and `backend/.env` with Perplexity credentials.
- [ ] Implement live web search and Perplexity citations in `backend/app/agents/researcher/tools.py`.
- [ ] Create `backend/app/agents/general_assistant/` (config.json, prompt.md, skills.json, tools.py).
- [ ] Update `backend/app/main.py` chat dispatching for Perplexity `sonar` and Gemini model choices.
- [ ] Verify with automated tests in `backend/test_endpoints.py`.

### Phase 3: Frontend DAG Edge Snapping & Expandable Nodes
- [ ] Update `frontend/src/app/workflows/types.ts` with new block schemas.
- [ ] Implement nearest-edge dynamic snapping in `VisualGraphEditor.tsx` and `DataFlowEdge.tsx`.
- [ ] Implement click-to-expand interactive block nodes in React Flow DAG.
- [ ] Add Block Palette menu to add Condition, Python, Loop, Artifact, and Agent blocks.

### Phase 4: Workflow Studio Cards & Block Editor Integration
- [ ] Update `frontend/src/app/workflows/components/StepCardEditor.tsx` for all 5 block types.
- [ ] Update `StepUnitTestModal.tsx` and `WorkflowSystemTestModal.tsx` to inspect and test all block types.
- [ ] Update Agent Editor modal with model selection dropdown.

### Phase 5: Verification & Full Validation
- [ ] Run backend tests (`backend/test_endpoints.py`).
- [ ] Run frontend lint (`npm --prefix frontend run lint`).
- [ ] Run frontend build (`npm --prefix frontend run build`).
- [ ] Update `verification.md`, `qa-checklist.md`, and `CHANGELOG.md`.

---

## Execution Log

*(Entries will be appended after each phase execution upon plan approval.)*
