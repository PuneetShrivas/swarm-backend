# Verification: Advanced Workflow Blocks, DAG Edge Snapping, Expandable Nodes, Real Web Search, Perplexity API & Base Conversational Agent

*Created: 2026-10-28T20:58:00+05:30*  
*Status: Pending Execution*

## Test Strategy

1. **Backend Automated Tests (`backend/test_endpoints.py`)**:
   - Verification of `step_type == "condition"` (evaluating true/false branching).
   - Verification of `step_type == "python_code"` (executing sandboxed python and returning transformed dict).
   - Verification of `step_type == "loop"` (looping back to step with iteration limit guardrail).
   - Verification of `step_type == "artifact"` (creating persistent structured markdown/code artifact).
   - Verification of real web search tool execution with citations.
   - Verification of Perplexity API client handling and fallback.
   - Verification of `general_assistant` agent registration and model selection.
2. **Frontend Type Checking & Linting**:
   - Run `npm --prefix frontend run lint` (0 errors, 0 warnings).
3. **Frontend Production Build**:
   - Run `npm --prefix frontend run build` (Next.js production build exits code 0).
4. **Manual & Interactive Scenarios**:
   - Create and execute a workflow containing Condition, Python, Loop, and Artifact blocks.
   - Verify DAG nearest-edge snapping when moving blocks around the 2D canvas.
   - Verify clicking DAG blocks toggles inline expansion and collapse.
   - Test real web search in Chat and Workflow testing.

## Execution Outcomes

*(To be recorded during Phase 5 verification.)*
