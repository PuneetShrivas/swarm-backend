# QA Checklist: On-the-Fly Orchestrator Workflows & Granular Step Execution

**Datetime:** 2026-10-29T20:50:45+05:30  
**Status:** Verified & Complete

## Quality Assurance Checklist

### 1. On-the-Fly Workflow Synthesis & Execution
- [x] Composite user queries automatically decompose into multi-step workflows.
- [x] Single-agent queries execute gracefully as 1-step workflows.
- [x] Specialized models are preserved (e.g. Researcher always uses Perplexity Sonar).
- [x] Workflows are ephemeral by default and NOT saved in the database `workflows` table.
- [x] Any file artifacts produced during workflow steps are preserved in Artifacts Studio.

### 2. Live Granular In-Flight Progress (`/chat`)
- [x] In-flight console replaces the generic spinner while generation is running.
- [x] Live console shows active workflow title and total steps.
- [x] Current active step shows a pulsing animation, assigned agent, and model tag.
- [x] Completed steps show a green checkmark and execution duration.
- [x] Single-agent queries display granular lifecycle stages (Intent Analysis $\to$ Grounding $\to$ Reasoning $\to$ Tool Execution $\to$ Synthesis).

### 3. Completed Message Granular Step Trace
- [x] Assistant message card renders an expandable Granular Step Trace accordion.
- [x] Users can expand/collapse steps to inspect instructions, agent role, duration, tokens, and outputs.
- [x] Tool executions within steps display tool name, input arguments, and result status.

### 4. "Save as Workflow" Option
- [x] Messages generated via on-the-fly workflows display a "Save as Workflow" button.
- [x] Clicking "Save as Workflow" opens `SaveWorkflowModal` with pre-filled title, goal, and steps.
- [x] User can edit the title/goal and confirm saving.
- [x] `POST /api/workflows` creates the permanent workflow record in Supabase / memory store.
- [x] Message card provides functional save capability and user visual feedback.

### 5. Automated Tests & Build Verification
- [x] Backend test suite passes: `backend\venv\Scripts\python backend/test_endpoints.py` (all 68 tests).
- [x] Frontend builds with 0 errors: `npm --prefix frontend run build`.
- [x] No regression on existing 64 test cases.
