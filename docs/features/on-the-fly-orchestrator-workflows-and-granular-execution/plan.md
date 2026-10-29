# Feature: On-the-Fly Orchestrator Workflows & Granular Step Execution

**Datetime:** 2026-10-29T20:51:00+05:30  
**Status:** Completed & Verified

## Goal

Provide autonomous on-the-fly workflow synthesis and execution by the orchestrator agent for user queries in chat, treating single-agent executions as 1-step workflows and multi-agent coordination as multi-step DAGs. These dynamic workflows run ephemerally by default (without cluttering the user's permanent workflow library), with an interactive "Save as Workflow" UI action to persist them on demand. Additionally, implement real-time granular step updating (in-flight live console and completed execution trace) so users can clearly see every action, tool execution, and phase taken by the agent whether operating via a multi-step workflow or a single agent.

## Scope

### In scope:
- **On-the-Fly Workflow Synthesis (`synthesize_on_the_fly_workflow`)**:
  - Orchestrator evaluates user query complexity and decomposes it into either a multi-agent workflow (2–4 steps) or a single-agent workflow (1 step).
  - Step outputs are dynamically pipelined (`{{steps.<id>.output.text}}`).
  - Supported for all swarm agents (Groq Qwen 3.8, Perplexity Sonar for live research, Coder, Data Analyst, Synthesizer, File Creator, Reviewer).
- **Ephemeral Workflow Execution**:
  - Workflows execute end-to-end via `workflow_engine.execute_workflow` without saving permanent records in the `workflows` database table.
  - Downloadable file artifacts (CSVs, PDFs, DOCX, XLSX, scripts) generated during steps are saved to user artifacts.
- **Granular Step Updating & Streaming**:
  - Progressive Server-Sent Events (SSE) streaming endpoint (`POST /api/chat/stream` or `Accept: text/event-stream`) emitting granular milestones: intent analysis, planning, step start, step progress, step complete, and final payload.
  - Granular trace metadata (`step_runs`, `granular_trace`, durations, token counts, tool calls) preserved in message metadata.
- **Frontend Live Execution Console**:
  - Live animated console during `isLoading` displaying the active workflow title, active step indicator, pulsing agent badges, live timers, and completed step checkmarks.
- **Frontend Completed Granular Trace & "Save as Workflow"**:
  - Expandable granular step accordion inside `MessageItem.tsx` displaying step instructions, tool invocations, inputs/outputs, and metrics.
  - "Save as Workflow" card action opening `SaveWorkflowModal.tsx` to preview DAG and persist to `/api/workflows` with 1 click.
- **Automated Tests**: Tests 65–68 covering multi-step and 1-agent on-the-fly workflow execution, granular trace metadata, and save-to-library endpoint.

### Out of scope:
- Modifying offline scheduled background cron workflows.
- Requiring workflows to be permanently saved before they can be executed.

## Current behavior

- In `POST /api/chat`, `route_agent` selects an agent based on keyword heuristics. If the orchestrator is selected, it simply runs a single completion prompt turn.
- Running a workflow in chat currently requires an explicit `/workflow:<id>` trigger pointing to an already saved workflow record in database.
- The UI in-flight loading state is a static spinner with `"Swarm agent reasoning..."`.
- Completed message metadata only shows a basic banner if `/workflow:<id>` was triggered, without granular step inspection or an option to save dynamically synthesized pipelines.

## Proposed behavior

1. When a query is routed to the orchestrator (or no specific agent is forced), the orchestrator dynamically plans a workflow specification:
   - For composite queries (e.g. "Research market trends for NVDA and create an executive briefing with financial metrics"):
     Synthesizes an on-the-fly multi-agent workflow DAG (`step_1: researcher` with Perplexity Sonar $\to$ `step_2: data_analyst` with Groq Qwen $\to$ `step_3: synthesizer` or `file_creator`).
   - For single-purpose queries (e.g. "Write a Python script for binary search" or "What is quantum entanglement?"):
     Synthesizes a 1-agent workflow (`step_1: coder` or `step_1: general_assistant`).
2. The workflow executes ephemerally through `workflow_engine.execute_workflow` without writing to the `workflows` table.
3. During execution, granular updates stream in real time (or return in `granular_trace`), showing each phase:
   - Phase 1: Intent Analysis & RAG Context Assembly.
   - Phase 2: Orchestration Plan (Single Agent vs Multi-Agent DAG).
   - Phase 3: Step-by-step execution with live timers, tool calls, and agent switches.
   - Phase 4: Output Synthesis & Artifact Extraction.
4. The user sees a live pulsing console during generation, and upon completion, can expand the Granular Step Trace to inspect any step's prompt, duration, tokens, and tool results.
5. If the workflow was synthesized on the fly (`is_ephemeral_workflow: true`), the card displays an interactive **"Save as Workflow"** button allowing the user to name and persist the workflow into their library for future reuse.

## Implementation steps

1. **Step 1: Backend On-The-Fly Workflow Synthesis & Ephemeral Execution**:
   - In `backend/app/workflows/engine.py`, add support for step callbacks (`step_callback`) and ephemeral execution flag (`is_ephemeral`).
   - In `backend/app/ai_generator.py`, implement `synthesize_on_the_fly_workflow(prompt, target_agent_id, available_agents, available_tools, attached_artifacts)`.
   - In `backend/app/main.py`, update `chat` to invoke dynamic workflow execution when orchestrator is targeted or auto-routed, packaging `workflow_spec`, `step_runs`, and `granular_trace` into message metadata.
   - Add Tests 65 & 66 in `backend/test_endpoints.py`.

2. **Step 2: Backend Granular Progress Streaming (SSE)**:
   - In `backend/app/main.py`, implement streaming endpoint `POST /api/chat/stream` using FastAPI `StreamingResponse` emitting `text/event-stream` chunks for each granular lifecycle event (`phase`, `workflow_planned`, `step_start`, `step_progress`, `step_complete`, `complete`).
   - Add Test 67 in `backend/test_endpoints.py` verifying granular execution metadata and stream events.

3. **Step 3: Frontend In-Flight Granular Execution Console**:
   - Create `frontend/src/app/chat/components/LiveExecutionConsole.tsx` displaying active workflow title, active step indicator with pulsing animations, and live checklist of completed steps.
   - Update `requestSwarmResponse` in `frontend/src/app/chat/page.tsx` to read the SSE stream when available and update live progress state.

4. **Step 4: Frontend Completed Granular Trace & "Save as Workflow" Modal**:
   - Create `frontend/src/app/chat/components/GranularStepTrace.tsx` rendering an expandable step accordion showing duration, token count, tool calls, and inputs/outputs.
   - Create `frontend/src/app/chat/components/SaveWorkflowModal.tsx` allowing users to preview and save the ephemeral workflow to `/api/workflows`.
   - Update `frontend/src/app/chat/components/MessageItem.tsx` to mount `<GranularStepTrace />` and the "Save as Workflow" banner/modal.
   - Add Test 68 in `backend/test_endpoints.py` verifying saving an ephemeral workflow to the permanent library.

5. **Step 5: Verification, Quality Assurance & Deployment**:
   - Run full backend test suite (68 tests).
   - Run frontend build (`npm --prefix frontend run build`).
   - Update `verification.md` and `qa-checklist.md`.
   - Commit, push to `origin main`, and deploy to Vercel production.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/workflows/engine.py` | Add `step_callback` and `is_ephemeral` support in `execute_workflow` | Allow execution of unsaved workflows and streaming of granular step events |
| `backend/app/ai_generator.py` | Implement `synthesize_on_the_fly_workflow` | Decompose user queries into 1-agent or multi-agent workflow DAGs |
| `backend/app/main.py` | Add on-the-fly workflow routing, granular trace assembly, and `POST /api/chat/stream` | Route user queries through dynamic workflows and stream real-time progress |
| `backend/test_endpoints.py` | Add Tests 65–68 | Cover on-the-fly multi-agent workflow, 1-agent workflow, granular trace, and save-to-library |
| `frontend/src/app/chat/components/LiveExecutionConsole.tsx` | New component | Display live in-flight progress timeline while generation is active |
| `frontend/src/app/chat/components/GranularStepTrace.tsx` | New component | Provide expandable granular step trace inside completed message cards |
| `frontend/src/app/chat/components/SaveWorkflowModal.tsx` | New component | Allow 1-click persistence of on-the-fly workflows into the user library |
| `frontend/src/app/chat/components/MessageItem.tsx` | Mount `GranularStepTrace` and `SaveWorkflowModal` | Provide granular inspection and "Save as Workflow" action on message cards |
| `frontend/src/app/chat/page.tsx` | Wire streaming reader and live execution console | Handle real-time SSE stream events and render live progress updates |

## Interfaces

- **`POST /api/chat/stream`**:
  - Request: `ChatRequest` (same schema as `/api/chat`).
  - Response: `text/event-stream` SSE chunks:
    - `data: {"type": "phase", "phase": "...", "label": "..."}`
    - `data: {"type": "workflow_planned", "is_multi_step": true, "workflow": {...}}`
    - `data: {"type": "step_start", "step_id": "step_1", "step_name": "...", "agent_id": "..."}`
    - `data: {"type": "step_progress", "step_id": "step_1", "detail": "..."}`
    - `data: {"type": "step_complete", "step_id": "step_1", "duration_ms": 120, "output": "..."}`
    - `data: {"type": "complete", "message": Message}`
- **Message Metadata Schema**:
  ```typescript
  interface MessageMetadata {
    mode?: "on_the_fly_workflow" | "workflow_execution" | "direct_turn";
    is_ephemeral_workflow?: boolean;
    is_saved?: boolean;
    saved_workflow_id?: string;
    workflow_spec?: {
      title: string;
      goal: string;
      description?: string;
      steps: WorkflowStep[];
      edges: Array<{ source: string; target: string }>;
    };
    step_runs?: WorkflowStepRun[];
    granular_trace?: Array<{
      timestamp: string;
      phase: string;
      label: string;
      step_id?: string;
      agent_id?: string;
      duration_ms?: number;
      status: "running" | "completed" | "failed";
    }>;
  }
  ```

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| LLM workflow synthesis latency | Delay before first step begins | Fast deterministic template heuristics for common multi-agent combinations (Research + Code, Financial Data + Report) with instant fallback |
| Streaming disconnects / proxies | Stream drops mid-flight | Client falls back gracefully to standard `POST /api/chat`, and backend always persists completed message with full trace metadata in session history |
| User doesn't want workflow saved | Library clutter | On-the-fly workflows are NOT saved by default; only saved when the user explicitly clicks "Save as Workflow" |
| 1-agent queries feeling heavy | Overhead for simple questions | 1-agent workflows execute with minimal 1-step overhead and direct response formatting, displaying simple clean reasoning traces |

## Verification

- Automated Tests:
  - `Test 65`: Multi-step on-the-fly workflow synthesis and ephemeral execution.
  - `Test 66`: Single-agent on-the-fly workflow execution.
  - `Test 67`: Granular step execution trace and streaming event structure.
  - `Test 68`: Saving an ephemeral workflow to `/api/workflows`.
- Verification Commands:
  - `backend\venv\Scripts\python backend/test_endpoints.py`
  - `npm --prefix frontend run build`

## Rollout

- Zero database migration required: uses existing `WorkflowStep` schemas and adds metadata flags.
- Fully backward compatible with existing `/api/chat` consumers and saved workflows.
