# Architecture Decisions: On-the-Fly Orchestrator Workflows & Granular Step Execution

**Datetime:** 2026-10-29T20:07:04+05:30  
**Status:** Approved  

## Key Architectural Decisions

### 1. Unified Workflow Model for Both Multi-Agent and Single-Agent Execution
- **Context:** Previously, single-agent execution in `/api/chat` followed a separate code path from `/workflow` executions.
- **Decision:** Unify the mental and structural model: every query handled by the orchestrator executes as a Workflow DAG. Simple queries and targeted agent selections run as a 1-step workflow (`step_1`), while composite queries decompose into multi-step DAGs (2–4 steps).
- **Consequences:** Ensures consistent execution metrics (`step_runs`, `duration_ms`, `tokens_used`), uniform granular step tracing, and identical tooling/RAG capabilities across all queries.

### 2. Ephemeral In-Memory Execution vs Database Persistence
- **Context:** User requested: "These workflows won't be saved by default. Instead UI will give an option to save the workflow after execution."
- **Decision:** The backend executes the synthesized workflow specification directly in-memory via `workflow_engine.execute_workflow` with an ephemeral flag. It does not insert rows into the `workflows` table. The synthesized workflow specification and execution runs are attached to the `Message.metadata` payload.
- **Consequences:** Keeps the user's workflow library clean and uncluttered. Only user-selected workflows are persisted to the database.

### 3. Server-Sent Events (SSE) Streaming for Live In-Flight Step Updates
- **Context:** User requested: "gracefully display Very granular step updating for what is happening by the agent. both while orchestrator works via a workflow or without it."
- **Decision:** Implement `POST /api/chat/stream` yielding Server-Sent Events (`text/event-stream`). Events notify the frontend of granular lifecycle transitions:
  - `phase`: Planning / Intent Analysis.
  - `workflow_planned`: Generated DAG overview.
  - `step_start`: Step index, name, agent, model.
  - `step_progress`: Inner tool / API status.
  - `step_complete`: Step duration, tokens, outputs.
  - `complete`: Final message payload with full metadata.
- **Consequences:** Allows the chat UI to display an animated live progress console showing each step pulsing and completing in real-time, while gracefully falling back to standard JSON if streaming is disconnected.

### 4. Interactive "Save as Workflow" Workflow Persistence Flow
- **Context:** After an on-the-fly workflow completes, users may want to save the synthesized pipeline.
- **Decision:** Attach `is_ephemeral_workflow: true` and `workflow_spec: {...}` to the message metadata. When the user clicks "Save as Workflow", the frontend opens a modal allowing them to adjust the title and description, then sends `POST /api/workflows` to create a permanent record. The message card updates to show "Saved to Workflows" with a direct link to `/workflows/[id]`.
- **Consequences:** Enables zero-friction curation of valuable AI-generated workflows.
