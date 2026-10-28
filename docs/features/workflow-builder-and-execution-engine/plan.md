# Feature: Workflow Builder, Visual React Flow Editor, Execution Engine & Debugging

*Created: 2026-10-28T18:15:00+05:30*

## Status

Completed (All Backend APIs, AST Sandbox, Visual React Flow Editor, Studio, Shared Pages, Chat Integration, and End-to-End Tests Implemented & Verified)

## Confirmed Design Decisions (2026-10-28T18:19:00+05:30)

1. **Python Script Tool Sandbox**: In-process sandbox with static AST safety validation prohibiting dangerous imports (`os`, `sys`, `subprocess`, `shutil`, `socket`), restricted builtins namespace, and a strict 5-second execution timeout.
2. **Chat Invocation UX**: Dual-trigger mechanism featuring both a `/workflow` slash command with autocomplete and a dedicated "Run Workflow" modal launcher in the chat interface, rendering an interactive step progress card in the conversation tree.
3. **Dual Workflow Studio Editor**: Seamless switching between the Structured Card Editor and the Visual React Flow Graph Editor (`@xyflow/react`), with two-way state synchronization.

## Goal

Provide a comprehensive, production-grade **Workflow Builder & Execution Engine** allowing users to design, test, debug, share, and invoke multi-agent autonomous workflows. 

Workflows are composed of:
1. **A Goal**: High-level objective with input parameters.
2. **Steps**: Directed sequence or DAG of steps, where each step utilizes an agent (prebuilt or custom user-created), prompt instructions with variable interpolation, step-level tools, and knowledge base files.
3. **Python Script Tools**: User-submitted Python scripts conforming to a defined `execute(input_data, context)` contract, inspectable in the UI and executed in a sandboxed runner.
4. **Knowledge Bases**: Document file attachments (txt, md, csv, json, pdf) with text extraction and context injection into agent prompts.
5. **Custom Agents**: Ability for users to create and manage their own specialized agents beyond the 6 globally available prebuilt agents (`orchestrator`, `researcher`, `coder`, `reviewer`, `data_analyst`, `synthesizer`).
6. **Dual-Mode Editor**: A switchable UI supporting both a structured Card/Form Editor and an interactive visual React Flow DAG Graph Editor.
7. **Two-Tier Testing**: Unit Testing (single-step isolation with mock inputs) and System Testing (full end-to-end DAG run).
8. **Runs & Debugging Telemetry**: Comprehensive audit log of all runs, step durations, token usage per step/agent, and tool output traces.
9. **Chat Invocation**: Ability to trigger tested workflows directly inside the `/chat` workspace and visualize execution progress in conversation messages.
10. **View-Only Sharing**: Read-only public/shared links allowing other users to inspect, test, or fork workflows without modifying the original author's definition.

---

## Scope

### In Scope
- **Database (Supabase & In-Memory Store)**:
  - 6 new tables: `workflows`, `workflow_tools`, `workflow_knowledge_files`, `workflow_runs`, `workflow_step_runs`, `user_agents`.
  - Comprehensive Row Level Security (RLS) enforcing user ownership, read-only shared access, and foreign keys to `auth.users`.
  - Full in-memory fallback implementation in `backend/app/supabase.py` (`MemoryStore`) ensuring zero-config local development and offline test execution.
- **Backend Architecture (`backend/app/workflows/`)**:
  - Pydantic models for workflows, steps, tools, runs, step runs, and test requests.
  - DAG execution engine (`engine.py`) with topological dependency resolution and variable substitution (`{{inputs.x}}`, `{{steps.y.output}}`).
  - Sandboxed Python tool runner (`tool_runner.py`) with AST syntax checks, execution timeouts, safe builtins, stdout/stderr capture, and structured dictionary returns.
  - Knowledge extraction & context injection (`knowledge.py`).
  - Custom agent management integrating directly with `AgentRegistry`.
  - Unit test runner (`/api/workflows/{id}/steps/{step_id}/test`) and system test runner (`/api/workflows/{id}/run`).
  - Workflow invocation inside `/api/chat`.
- **Frontend Architecture (`frontend/src/app/workflows/`)**:
  - `/workflows`: Dashboard with workflow cards, status pills, search, filter, creation modal, and shared workflows tab.
  - `/workflows/[id]`: Workflow Studio with tab navigation (**Editor**, **Runs & Debugging**, **Knowledge Base**, **Tools**, **Unit Tests**).
  - Dual Editor Switcher:
    - **Structured Card Editor**: Clean step cards, agent selector, instruction prompt editor, tool attachments, and dependency pickers.
    - **Visual Graph Editor**: `@xyflow/react` interactive canvas with custom nodes (`GoalNode`, `StepNode`, `ToolNode`, `KnowledgeNode`), edge connections, drag-and-drop, and real-time synchronization with card state.
  - `/workflows/share/[shareSlug]`: View-only shared workflow page with a fork/clone action.
  - `/chat` Integration: Slash command `/workflow` and a "Run Workflow" modal in `ChatInput` / `ChatHeader`, rendering interactive workflow progress cards in `MessageItem.tsx`.

### Out of Scope
- Direct binary execution of compiled executables (tools are strictly pure Python scripts).
- Webhook/cron automated scheduling (standing cron jobs deferred to a dedicated automation release).

---

## Current Behavior

- Agents exist as static or filesystem-based modular packages loaded by `AgentRegistry` (`backend/app/agents/`).
- Users can chat with agents in `/chat` with single-agent turns or heuristic intent routing.
- There is no concept of multi-step workflows, step pipelines, Python script tool submission, knowledge document attachment, workflow testing, or shared workflow viewing.
- The only agents available are the 6 prebuilt filesystem agents (`orchestrator`, `researcher`, `coder`, `reviewer`, `data_analyst`, `synthesizer`); users cannot create persistent custom agents from the UI.

---

## Proposed Behavior

1. **Workflow Studio (`/workflows/[id]`)**:
   - Users define a **Goal** (e.g., "Analyze competitor pricing, extract key features, and generate comparison report").
   - Users add **Steps**; for each step, select an Agent (prebuilt or user-created), write Instructions with dynamic interpolation (`{{inputs.domain}}`, `{{steps.step_1.output}}`), attach Python script tools, and attach knowledge files.
   - Users switch at will between the **Structured Card Editor** and the **Visual React Flow Graph Editor**. Edits in one view immediately synchronize with the other.
2. **Standardized Python Script Tools**:
   - Users create custom tools by writing Python code defining:
     ```python
     def execute(input_data: dict, context: dict) -> dict:
         ...
         return {"result": ...}
     ```
   - Tools can be tested individually, inspected in a code viewer, and attached to steps.
   - Executed safely in a sandboxed runner with timeout limits and stdout/stderr capture.
3. **Knowledge Base Documents**:
   - Users upload reference files (`.txt`, `.md`, `.csv`, `.json`, `.pdf`).
   - Text is extracted and injected into the step agent's system prompt context automatically.
4. **Two-Tier Testing**:
   - **Unit Testing**: Test any single step in isolation by providing mock input arguments or mock outputs from prior steps.
   - **System Testing**: Execute the entire workflow DAG end-to-end, streaming step status updates and token counts in real time.
5. **Runs & Debugging Telemetry**:
   - Comprehensive log of every run: input arguments, final output, step status, execution latency, token usage, tool call logs, and errors.
6. **Chat Integration**:
   - In `/chat`, users can trigger any saved workflow via `/workflow <name>` or via a dedicated "Run Workflow" modal.
   - The workflow executes in the background, updates a message card in the conversation tree, and outputs the final synthesized result.
7. **View-Only Sharing**:
   - Workflows can be toggled to `shared` visibility with a unique shareable slug.
   - Shared viewers can inspect all goals, steps, graph diagrams, code, and run sample tests, but cannot edit the original workflow. A "Fork to My Workflows" button allows them to clone it into their account.

---

## Implementation Steps

### Phase 1: Database Schema & In-Memory Store
1. Create Supabase migration `supabase/migrations/20261028_workflows_and_custom_agents.sql` defining:
   - `user_agents`
   - `workflow_tools`
   - `workflows`
   - `workflow_knowledge_files`
   - `workflow_runs`
   - `workflow_step_runs`
   - Indexes and RLS policies (owner CRUD + shared view-only SELECT).
2. Extend `MemoryStore` in `backend/app/supabase.py` to support all 6 entities in offline/mock mode for automated testing without requiring live Supabase credentials.

### Phase 2: Backend Workflow Engine & Tool Sandbox
1. Create `backend/app/workflows/models.py` with Pydantic schemas for workflows, steps, tools, knowledge files, runs, and test requests.
2. Create `backend/app/workflows/tool_runner.py` with Python AST safety validation, execution timeout, stdout/stderr capture, and dictionary schema verification.
3. Create `backend/app/workflows/knowledge.py` for file text extraction and context prompt formatting.
4. Create `backend/app/workflows/engine.py` for DAG topological resolution, variable interpolation, agent dispatch (connecting to `AgentRegistry` and custom agents), and telemetry recording.
5. Extend `backend/app/agents/registry.py` and `backend/app/main.py` with custom agent persistence.
6. Implement all workflow REST API endpoints in `backend/app/main.py`.

### Phase 3: Frontend Types, API Client & Workflow Dashboard
1. Install `@xyflow/react` in `frontend/package.json`.
2. Define TypeScript types in `frontend/src/app/workflows/types.ts`.
3. Create `/workflows/page.tsx` dashboard:
   - Header with Create Workflow button, search/filter, and tabs (My Workflows, Shared Workflows).
   - Workflow cards showing Goal, Step count, Tool count, Knowledge count, Visibility badge, and quick actions (Edit, Run, Share, Delete).

### Phase 4: Workflow Studio & Dual-Mode Editor
1. Create `/workflows/[id]/page.tsx` studio:
   - Mode Toggle: **Structured View** vs **Visual Graph View**.
   - Structured View: Goal configuration card, step cards with reordering, agent selection dropdown, instructions textarea with variable helpers, tool selector, and knowledge selector.
   - Visual Graph View (`@xyflow/react`): Interactive canvas with custom `StepNode`, `ToolNode`, `KnowledgeNode`, connecting edges for dependencies, and a slide-out step configuration drawer.
2. Tools Manager tab: Python script editor with Monaco/syntax highlighting, input/output schema editor, and live tool script test runner.
3. Knowledge Base tab: File upload dropzone, text preview modal, and step attachment toggles.
4. Unit Testing tab/drawer: Pick any step, provide mock JSON input, and execute unit test with live output display.
5. Runs & Debugging tab: Table of historical runs, timeline breakdown, step logs, token metrics, and execution graphs.

### Phase 5: View-Only Shared Page & Forking
1. Create `/workflows/share/[shareSlug]/page.tsx`:
   - Read-only banner indicating author and view-only permissions.
   - Full inspection of Goal, Steps, Graph, Tools code, and Knowledge files with all editing controls disabled.
   - "Fork Workflow" action cloning the workflow into the visitor's account.

### Phase 6: Chat Invocation & Message Card Integration
1. In `frontend/src/app/chat/components/ChatInput.tsx`, add a Workflow launcher button and `/workflow` slash command autocomplete.
2. Add a `WorkflowRunModal` to configure runtime inputs before launching.
3. In `frontend/src/app/chat/components/MessageItem.tsx`, render an interactive Workflow Execution Card displaying live step progress, agent badges, tool call pill badges, and final synthesized output.
4. Add a navigation link to `/workflows` in `frontend/src/app/chat/components/SessionSidebar.tsx` and main navbar.

### Phase 7: Verification & Quality Assurance
1. Expand `backend/test_endpoints.py` to cover:
   - Custom agent creation and lookup.
   - Workflow tools creation and sandboxed execution.
   - Workflow CRUD and DAG validation.
   - Step unit testing and full workflow system testing.
   - Shared workflow retrieval and unauthorized edit blocking (403).
   - Chat workflow invocation endpoint.
2. Run `npm run lint` and `npm run build` on the frontend.
3. Complete `verification.md`, `qa-checklist.md`, and `CHANGELOG.md`.

---

## Files to Change

| File | Change | Reason |
| ---- | ------ | ------ |
| `supabase/migrations/20261028_workflows_and_custom_agents.sql` | [NEW] | Database tables, indexes, and RLS policies for workflows, tools, runs, and custom agents. |
| `backend/app/supabase.py` | [MODIFY] | Extend `MemoryStore` with methods for workflows, tools, runs, knowledge, and custom agents. |
| `backend/app/workflows/__init__.py` | [NEW] | Workflows package init. |
| `backend/app/workflows/models.py` | [NEW] | Pydantic models for workflows, steps, script tools, knowledge files, and runs. |
| `backend/app/workflows/tool_runner.py` | [NEW] | Sandboxed Python script executor with AST checks, timeout, and stdout capture. |
| `backend/app/workflows/knowledge.py` | [NEW] | File text extraction and context prompt formatting. |
| `backend/app/workflows/engine.py` | [NEW] | Workflow execution engine with DAG resolution, variable interpolation, and step telemetry. |
| `backend/app/agents/registry.py` | [MODIFY] | Support user custom agent registration and lookup by user ID. |
| `backend/app/main.py` | [MODIFY] | Endpoints for workflows, custom agents, tools, runs, unit/system tests, and chat invocation. |
| `backend/test_endpoints.py` | [MODIFY] | Automated test suite verifying workflow endpoints, sandboxed tool execution, unit/system testing, and shared links. |
| `frontend/package.json` | [MODIFY] | Add `@xyflow/react` for visual DAG editor. |
| `frontend/src/app/workflows/types.ts` | [NEW] | TypeScript definitions for workflows, steps, nodes, tools, knowledge, and runs. |
| `frontend/src/app/workflows/page.tsx` | [NEW] | Workflow dashboard with search, filters, cards, and create modal. |
| `frontend/src/app/workflows/[id]/page.tsx` | [NEW] | Workflow Studio with structured card editor, React Flow visual editor, tools manager, knowledge base, unit test drawer, and runs telemetry. |
| `frontend/src/app/workflows/components/VisualGraphEditor.tsx` | [NEW] | React Flow interactive canvas with custom Step, Tool, and Knowledge nodes. |
| `frontend/src/app/workflows/components/StepCardEditor.tsx` | [NEW] | Structured form/card editor for workflow steps. |
| `frontend/src/app/workflows/components/ToolScriptEditor.tsx` | [NEW] | Python script code viewer/editor with live runner test. |
| `frontend/src/app/workflows/components/KnowledgeBaseManager.tsx` | [NEW] | File upload dropzone and document previewer. |
| `frontend/src/app/workflows/components/WorkflowRunsDebugger.tsx` | [NEW] | Runs history, latency, token telemetry, step breakdown, and error logs. |
| `frontend/src/app/workflows/components/StepUnitTestModal.tsx` | [NEW] | Step-level unit testing modal with mock input and live execution output. |
| `frontend/src/app/workflows/share/[shareSlug]/page.tsx` | [NEW] | View-only shared workflow page with fork action. |
| `frontend/src/app/chat/components/ChatInput.tsx` | [MODIFY] | Add workflow launcher trigger and `/workflow` slash command support. |
| `frontend/src/app/chat/components/WorkflowPickerModal.tsx` | [NEW] | Modal allowing user to select a workflow and pass input arguments into chat. |
| `frontend/src/app/chat/components/MessageItem.tsx` | [MODIFY] | Render interactive workflow progress and results card in chat feed. |
| `frontend/src/app/chat/components/SessionSidebar.tsx` | [MODIFY] | Add navigation link to `/workflows`. |

---

## Interfaces

### 1. Database Schema
- `user_agents`: `(id TEXT PK, user_id UUID, name, role, description, system_prompt, model, temperature, icon, tools JSONB, skills JSONB, is_public BOOL, created_at, updated_at)`
- `workflow_tools`: `(id UUID PK, user_id UUID, name, description, code TEXT, input_schema JSONB, output_schema JSONB, is_public BOOL, created_at, updated_at)`
- `workflows`: `(id UUID PK, user_id UUID, title, description, goal, steps JSONB, edges JSONB, visibility TEXT, share_slug TEXT UNIQUE, created_at, updated_at)`
- `workflow_knowledge_files`: `(id UUID PK, workflow_id UUID, user_id UUID, file_name, file_type, file_size, content_text, metadata JSONB, created_at)`
- `workflow_runs`: `(id UUID PK, workflow_id UUID, user_id UUID, session_id UUID, trigger_type, status, input_data JSONB, output_data JSONB, total_tokens, duration_ms, error, created_at, completed_at)`
- `workflow_step_runs`: `(id UUID PK, run_id UUID, step_id, step_index, agent_id, status, prompt_rendered, input_data JSONB, output_data JSONB, tool_calls JSONB, tokens_used, duration_ms, error, created_at, completed_at)`

### 2. Python Script Tool Standard Contract
```python
def execute(input_data: dict, context: dict) -> dict:
    """
    Standard interface for user-defined Python script tools.
    
    Args:
        input_data: Key-value arguments passed from the workflow step.
        context: Runtime state (goal, step_name, previous step outputs).
        
    Returns:
        JSON-serializable dictionary with tool execution results.
    """
    # Tool logic here
    return {"status": "success", "result": ...}
```

### 3. REST API Endpoints
- `GET /api/workflows`: List workflows for current user (plus shared/public ones).
- `POST /api/workflows`: Create a new workflow.
- `GET /api/workflows/{id}`: Get full workflow with steps, tools, and knowledge.
- `PUT /api/workflows/{id}`: Update workflow (owner only).
- `DELETE /api/workflows/{id}`: Delete workflow (owner only).
- `GET /api/workflows/shared/{share_slug}`: Read-only access to a shared workflow.
- `POST /api/workflows/{id}/fork`: Clone workflow to caller's library.
- `POST /api/workflows/{id}/run`: Execute full workflow (system test).
- `POST /api/workflows/{id}/steps/{step_id}/test`: Execute isolated step (unit test).
- `GET /api/workflows/{id}/runs`: Get execution history and telemetry.
- `GET /api/workflows/{id}/runs/{run_id}`: Get deep run details with step breakdown.
- `POST /api/workflows/{id}/knowledge/upload`: Upload and extract file content.
- `DELETE /api/workflows/{id}/knowledge/{file_id}`: Remove knowledge file.
- `GET /api/workflow-tools`: List available script tools.
- `POST /api/workflow-tools`: Create a new Python script tool.
- `POST /api/workflow-tools/{tool_id}/test`: Test script execution with sample input.
- `GET /api/custom-agents`: List user-created custom agents.
- `POST /api/custom-agents`: Create a custom agent.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Untrusted Python Code Execution | Malicious user scripts could attempt disk/network access or infinite loops. | Sandbox runner inspects AST for disallowed imports (`os`, `sys`, `subprocess`, `shutil`), restricts globals namespace, and enforces a strict 5-second execution timeout. |
| Large Knowledge Base Context Exceeding Limits | Uploaded files could overwhelm LLM token context windows. | Truncate and prioritize top document chunks with configurable character/token limits per step context injection. |
| Inconsistent State Between Dual Editors (Cards vs Graph) | Edits made in React Flow might desynchronize from the step cards. | Use a single canonical `Workflow` state with bidirectional transformation: step reordering/edge linking updates both representations simultaneously. |
| Concurrent Run Telemetry Latency | Long-running workflows blocking synchronous HTTP requests. | Support asynchronous run creation with status polling and step-level completion streaming. |

---

## Verification

- **Unit tests**:
  - Python AST tool runner validation (safe scripts succeed, unsafe/timeout scripts fail gracefully).
  - DAG topological sorter (detects cycles, orders linear and branching steps correctly).
  - Template variable interpolator (`{{inputs.x}}`, `{{steps.y.output}}`).
  - Unit test runner isolating a single step with mock input.
- **Integration tests**:
  - End-to-end workflow execution (system test) with custom agents and script tools.
  - Supabase persistence & `MemoryStore` fallback parity.
  - View-only shared workflow access and forbidden mutation verification (403 for non-owners).
  - Chat workflow invocation and message metadata persistence.
- **Manual checks**:
  - Switch between Structured Card Editor and React Flow Visual Graph Editor.
  - Upload a knowledge base file (.txt, .md, .csv) and verify text injection in prompt.
  - Trigger workflow inside `/chat` and observe step progress card in conversation.
  - Access shared workflow link in an incognito window and verify read-only restrictions.
- **Commands**:
  - `& "backend\venv\Scripts\python.exe" -u backend/test_endpoints.py`
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run build`

---

## Rollout

1. Apply database migration in Supabase SQL editor (`supabase/migrations/20261028_workflows_and_custom_agents.sql`).
2. Deploy backend workflow engine endpoints with full backward compatibility for existing chat and agent endpoints.
3. Deploy frontend workflows workspace and chat integration.
4. Verify all automated tests, lint, and build checks pass with zero regressions.
