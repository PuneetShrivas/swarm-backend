# Feature: Custom Agent Studio, Enhanced Workflow Testing, AI Generator Mode & Chat UI Sanitization

*Created: 2026-10-28T20:32:00+05:30*  
*Last Updated: 2026-10-28T20:38:00+05:30*

## Status

Draft (Awaiting User Review & Approval)

## Goal

1. **Sanitize Chat Screen & Unify Information Architecture**:
   - Eliminate clutter from the chat interface: decongest the sidebar, simplify the header, collapse verbose message traces, and provide a distraction-free, modern conversation workspace.
   - Establish a unified top navigation rail across the entire app with a centered switcher connecting the 3 foundational pillars: **💬 Chat**, **🤖 Agents**, and **⚡ Workflows**.
2. **Custom Agent Studio & Testing Playground**:
   - Allow users to create, configure, manage, and test custom agents with different input prompts and mock parameters, mirroring the high-craft studio experience of Workflows.
   - Provide an isolated Agent Testing Playground showing live outputs, reasoning, tool execution traces, execution latency, and token consumption.
   - Ensure custom agents are immediately accessible across Chat (`/chat`), Workflows (`/workflows/[id]`), and the active Swarm roster.
3. **Revamp Workflow Step Testing UX**:
   - Fix the current undefined step testing UX: automatically detect required template variables (`{{goal}}`, `{{inputs.<var>}}`, `{{steps.<id>.output.<field>}}`) from step instructions.
   - Provide an interactive, auto-populated variable form (with JSON mode toggle), a live resolved prompt preview, and a multi-tab output inspector (Markdown preview, raw text, telemetry, and tool calls).
4. **Workflow System Testing with Custom Inputs**:
   - Fix the overall system test limitation: replace the blind zero-input run with an interactive **Workflow System Test Modal**.
   - Discover all required inputs across the entire workflow graph and allow users to supply custom inputs, inspect live step-by-step execution progress, and view per-step results and final synthesis.
5. **AI Generation Mode ("AI Architect / AI Generator")**:
   - Introduce generative AI capabilities for both Workflows and Agents via Gemini structured generation:
     - **AI Workflow Generator**: Users input requirements in natural language; AI produces a complete multi-step DAG pipeline (title, goal, steps, agent assignments, instructions with interpolation variables, tools, and dependencies).
     - **AI Agent Generator**: Users describe agent requirements; AI generates an agent profile (persona, role, comprehensive system prompt, temperature, model, icon, suggested tools/skills).
   - Provide a review and diffing screen before saving, allowing users to tweak generated specs, test them, and commit them into their workspace.

---

## Scope

### In Scope
- **Chat Screen Sanitization & UX De-cluttering**:
  - **Unified App Header Bar**: Clean top navigation bar with a segmented pill toggle between `💬 Chat`, `🤖 Agents`, and `⚡ Workflows`, plus a minimalist telemetry badge and account menu.
  - **Decongested Sidebar**: Strip the crowded 200px agent card widget out of `SessionSidebar.tsx`, replacing it with a clean summary link to the Agents Studio. Keep the sidebar dedicated to conversation sessions history and new chats.
  - **Minimalist Chat Header**: Clean title with click-to-switch agent popover and minimal action icon buttons (Export, Clear, Run Workflow).
  - **Quiet Message Traces**: Collapse verbose tool execution badges and router traces by default into single-line expandable pills (`⚡ Executed 2 tools (42ms)`) to keep the dialogue readable.
  - **Modern Chat Empty State**: Distraction-free greeting with quick-start action pills.
- **Backend Endpoints**:
  - `POST /api/custom-agents/test`: Executes an agent in isolation with custom input prompt and optional variables/tools, returning content, latency, tokens, and tool calls.
  - `POST /api/ai/generate-workflow`: Generates complete workflow definition from user prompt using Gemini structured prompt generation with deterministic fallback.
  - `POST /api/ai/generate-agent`: Generates agent persona, role, and comprehensive system prompt from user prompt.
  - Automated tests covering agent testing and AI generation in `backend/test_endpoints.py`.
- **Frontend Pages & Components**:
  - `frontend/src/app/agents/page.tsx`: Dedicated Agents Studio dashboard in Linear design system (`#010102` canvas, `#0f1011` cards, `#23252a` hairline borders, `#5e6ad2` accents).
  - `frontend/src/app/agents/components/AgentPlaygroundModal.tsx`: Interactive agent testing console with live prompt inputs, tool call tracing, and token telemetry.
  - `frontend/src/app/agents/components/AgentEditorModal.tsx`: Visual editor for custom agent profiles (name, role, system prompt, model, temperature, tools).
  - `frontend/src/app/agents/components/AIAgentGeneratorModal.tsx`: Natural language agent generator with review and editing screen.
  - `frontend/src/app/workflows/components/StepUnitTestModal.tsx`: Revamped step testing modal with auto-detected input fields, prompt preview, and structured output tabs.
  - `frontend/src/app/workflows/components/WorkflowSystemTestModal.tsx`: Dedicated modal allowing custom input parameters, live step progress, and full DAG execution output review.
  - `frontend/src/app/workflows/components/AIWorkflowGeneratorModal.tsx`: Natural language workflow generator with visual pipeline preview and review-before-save.

### Out of Scope
- Direct local python virtual environment creation (tools remain sandboxed python scripts executed via AST validation).
- Altering existing Supabase database tables (models conform to existing `user_agents`, `workflows`, and `workflow_runs` schemas).

---

## Current Behavior

1. **Cluttered Chat Screen**:
   - `SessionSidebar` is overloaded: it tries to manage sessions, act as a full agent capability inspector (squeezing 6+ agent cards into a 200px box), show telemetry, auth state, and links all at once.
   - `ChatHeader` contains redundant `<select>` dropdowns and competing action buttons.
   - Message bubbles show large open tool execution boxes and router banners that disrupt reading.
   - Chat, Agents, and Workflows are siloed without a unified navigation structure.
2. **Custom Agents**: The backend has basic CRUD endpoints (`/api/custom-agents`), but there is no dedicated frontend UI page or testing playground to create, configure, or test custom agents with custom inputs.
3. **Step Testing UX**: `StepUnitTestModal.tsx` provides two plain, unguided JSON textareas (`mockInputsJson` and `mockPrevOutputsJson`). Users must manually construct JSON keys without knowing what template variables (`{{inputs.query}}`, `{{steps.<id>.output.text}}`) the step actually expects. Output is displayed in a raw text area without structured tabs, telemetry, or tool call traces.
4. **Overall System Testing**: In `frontend/src/app/workflows/[id]/page.tsx`, clicking "System Test" immediately fires `POST /api/workflows/${workflowId}/run` with a hardcoded payload `{ inputs: { query: goal } }`. The user has no UI to provide custom inputs or test different parameters.
5. **AI Generation**: There is no capability to generate either workflows or agents from natural language descriptions; users must manually type every field from scratch.

---

## Proposed Behavior

1. **Clean, Cohesive Information Architecture**:
   - A unified navigation bar allows instant switching between **💬 Chat**, **🤖 Agents**, and **⚡ Workflows**.
   - The chat sidebar focuses purely on sessions history and quick search.
   - Agent cards are elevated to their own dedicated **Agents Studio** (`/agents`), giving them the room they deserve.
   - Chat message tool executions are collapsed into sleek, expandable Linear pills.
2. **Agents Studio (`/agents`)**:
   - Users browse prebuilt and custom agents in a sleek Linear dashboard.
   - Users create new agents, edit custom agents, or delete them.
   - An interactive **Agent Playground** lets users test agents with custom prompts and inspect output, tokens, latency, and tool invocations.
3. **Enhanced Step Testing**:
   - `StepUnitTestModal.tsx` automatically parses instructions for `{{...}}` tokens and displays intuitive input fields for each detected variable.
   - Displays a live "Resolved Prompt Preview" showing exactly what the agent will read.
   - Structured Output Inspector: status badge, metrics cards (duration, tokens), formatted markdown response, and tool execution traces.
4. **Workflow System Testing**:
   - Clicking "System Test" opens `WorkflowSystemTestModal.tsx`.
   - The modal discovers all required input parameters across all steps in the workflow and presents an auto-generated form.
   - Live execution progress displays status as steps complete.
   - Detailed results view shows the final synthesized outcome, per-step execution cards, and token metrics.
5. **AI Generation Mode**:
   - **AI Workflow Generator**: Users input natural language requirements. Gemini generates a complete multi-step workflow. The user reviews the title, goal, steps, and dependencies before accepting.
   - **AI Agent Generator**: Users describe what agent they need. Gemini generates a specialized agent with persona, role, and comprehensive system instructions. The user reviews, tests in the playground, and saves.

---

## Implementation Steps

### Phase 1: Backend Agent Testing & AI Generation Services
1. Create `backend/app/ai_generator.py`:
   - Implement `generate_workflow_spec(prompt: str, ...)` returning structured workflow definition with steps, instructions, dependencies, and agent mappings.
   - Implement `generate_agent_spec(prompt: str, ...)` returning structured agent profile with name, role, system prompt, and settings.
   - Implement deterministic fallback for offline/demo mode without API key.
2. Update `backend/app/main.py`:
   - Add `POST /api/custom-agents/test`: Isolated agent execution endpoint.
   - Add `POST /api/ai/generate-workflow`: AI workflow generation endpoint.
   - Add `POST /api/ai/generate-agent`: AI agent generation endpoint.
3. Update `backend/test_endpoints.py`:
   - Add test cases covering agent testing, AI workflow generation, and AI agent generation.

### Phase 2: Chat Screen Sanitization & Unified App Navigation
1. Create `frontend/src/app/components/AppNavigationRail.tsx`:
   - Minimalist top bar with brand mark, segmented pill switcher (`💬 Chat` · `🤖 Agents` · `⚡ Workflows`), token telemetry pill, and user account menu.
2. Sanitize `frontend/src/app/chat/components/SessionSidebar.tsx`:
   - De-clutter sidebar: remove cramped 200px agent card widget; replace with clean link to Agents Studio.
   - Keep sidebar focused on session history, new chat button, and search.
3. Sanitize `frontend/src/app/chat/components/ChatHeader.tsx`:
   - Remove redundant `<select>` dropdown and competing buttons.
   - Implement clean agent badge with popover selector and minimalist action group.
4. Sanitize `frontend/src/app/chat/components/MessageItem.tsx`:
   - Collapse verbose tool executions and router traces into quiet, expandable single-line pills.
5. Update `frontend/src/app/chat/page.tsx` with clean empty state and integrated navigation.

### Phase 3: Workflow Step & System Testing UX Revamp
1. Revamp `frontend/src/app/workflows/components/StepUnitTestModal.tsx`:
   - Add instruction variable parser (`extractVariables(instructions)`).
   - Render visual input form for detected variables with JSON toggle.
   - Add resolved prompt preview and multi-tab output inspector.
2. Create `frontend/src/app/workflows/components/WorkflowSystemTestModal.tsx`:
   - Scan all steps for `{{inputs.*}}` variables and render dynamic input form.
   - Add execution stepper, step latency timelines, and final result preview.
3. Wire modal into `frontend/src/app/workflows/[id]/page.tsx` and `VisualGraphEditor.tsx`.

### Phase 4: AI Workflow Generator Modal
1. Create `frontend/src/app/workflows/components/AIWorkflowGeneratorModal.tsx`:
   - Prompt input with inspiration templates.
   - Review and diffing screen displaying generated steps, agents, and dependencies.
   - Save / Open in Studio button creating the workflow via API.
2. Add "✨ Generate with AI" triggers in `workflows/page.tsx` and `workflows/[id]/page.tsx`.

### Phase 5: Agents Studio, Testing Playground & AI Agent Generator
1. Create `frontend/src/app/agents/components/AgentPlaygroundModal.tsx`:
   - Live prompt input, mock context, model settings, and execution inspector.
2. Create `frontend/src/app/agents/components/AgentEditorModal.tsx`:
   - Full configuration form (name, role, system prompt, model, temperature, script tools).
3. Create `frontend/src/app/agents/components/AIAgentGeneratorModal.tsx`:
   - Prompt input, AI generation, review screen, and one-click save.
4. Create `frontend/src/app/agents/page.tsx`:
   - Linear design system dashboard listing all agents with filter tabs and action triggers.

### Phase 6: Full Verification & Documentation
1. Run backend tests (`backend/test_endpoints.py`).
2. Run `npm --prefix frontend run lint` and `npm --prefix frontend run build`.
3. Update `verification.md`, `qa-checklist.md`, and `CHANGELOG.md`.

---

## Files to Change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/ai_generator.py` | [NEW] AI generation logic for workflows & agents | Provides structured prompt generation via Gemini API |
| `backend/app/main.py` | [MODIFY] Add agent test & AI generation endpoints | Exposes API routes for frontend modals |
| `backend/test_endpoints.py` | [MODIFY] Add automated test cases | Verifies new endpoints and prevents regressions |
| `frontend/src/app/components/AppNavigationRail.tsx` | [NEW] Unified 3-pillar app top navigation bar | Establishes cohesive Chat / Agents / Workflows switcher |
| `frontend/src/app/chat/components/SessionSidebar.tsx` | [MODIFY] De-clutter and streamline sidebar | Removes crowded agent cards from sidebar |
| `frontend/src/app/chat/components/ChatHeader.tsx` | [MODIFY] Minimalist header with agent popover | Eliminates dropdown clutter |
| `frontend/src/app/chat/components/MessageItem.tsx` | [MODIFY] Collapse verbose traces into quiet pills | Keeps conversation readable and noise-free |
| `frontend/src/app/chat/page.tsx` | [MODIFY] Clean empty state & navigation integration | Professional, modern chat UX |
| `frontend/src/app/workflows/components/StepUnitTestModal.tsx` | [MODIFY] Revamp step testing UX with detected variables | Resolves UX flaws in step testing |
| `frontend/src/app/workflows/components/WorkflowSystemTestModal.tsx` | [NEW] System test modal with custom inputs | Resolves limitation of missing custom inputs in system test |
| `frontend/src/app/workflows/[id]/page.tsx` | [MODIFY] Wire system test modal and AI generator | Connects studio UI to new test modal |
| `frontend/src/app/workflows/components/AIWorkflowGeneratorModal.tsx` | [NEW] AI workflow generator modal | Implements AI mode for generating workflows |
| `frontend/src/app/workflows/page.tsx` | [MODIFY] Add AI generator trigger and AppNavigationRail | Enhances workflows dashboard |
| `frontend/src/app/agents/page.tsx` | [NEW] Dedicated Agents Studio page | Enables user to view, create, and manage custom agents |
| `frontend/src/app/agents/components/AgentPlaygroundModal.tsx` | [NEW] Interactive agent test console | Enables testing agents with custom inputs & inspecting outputs |
| `frontend/src/app/agents/components/AgentEditorModal.tsx` | [NEW] Custom agent creation & edit form | Configures agent profiles, system prompts, and tools |
| `frontend/src/app/agents/components/AIAgentGeneratorModal.tsx` | [NEW] AI agent generator modal | Implements AI mode for generating agents |
| `frontend/src/app/page.tsx` | [MODIFY] Connect AppNavigationRail | Seamless global navigation |
| `CHANGELOG.md` | [MODIFY] Document new features | Keep a Changelog compliance |

---

## Interfaces

### API: POST `/api/custom-agents/test`
- **Request Body**:
  ```json
  {
    "agent_id": "agent-financial-auditor",
    "system_prompt": "You are a financial auditing specialist...",
    "input_prompt": "Audit this quarterly report for EBITDA discrepancies",
    "model": "gemini-2.5-flash",
    "temperature": 0.2,
    "tool_ids": ["tool-word-count"]
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "content": "Audited output text...",
    "tokens_used": 185,
    "latency_ms": 240.5,
    "tool_calls": []
  }
  ```

### API: POST `/api/ai/generate-workflow`
- **Request Body**:
  ```json
  {
    "prompt": "Build a competitive threat intelligence pipeline with 2 steps"
  }
  ```
- **Response**: Complete `WorkflowCreateUpdatePayload` object.

### API: POST `/api/ai/generate-agent`
- **Request Body**:
  ```json
  {
    "prompt": "Create an automated database query optimization agent"
  }
  ```
- **Response**: `UserAgentProfile` object.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Gemini API unavailable or quota exceeded | High | Built-in deterministic generator fallback producing complete, valid specifications offline |
| User enters malformed variables in testing form | Medium | Client-side validation with real-time JSON and token parsing |
| Custom agent name conflicts with prebuilt agents | Low | Strict validation in `POST /api/custom-agents` preventing overwriting prebuilt agent IDs |

---

## Verification

- **Unit Tests**:
  - `python -u backend/test_endpoints.py` covering agent test, AI workflow generation, and AI agent generation.
- **Frontend Checks**:
  - `npm --prefix frontend run lint` (0 errors)
  - `npm --prefix frontend run build` (Next.js production build exits 0)
- **Manual Verification**:
  - Check sanitized Chat interface: clean sidebar without agent congestion, collapsed message traces, minimal header.
  - Test top navigation switching smoothly between `/chat`, `/agents`, and `/workflows`.
  - Test custom agent creation and live testing in `AgentPlaygroundModal`.
  - Test step unit test modal with auto-detected input fields.
  - Test workflow system test modal with custom inputs and verify execution.
  - Test AI workflow generator and AI agent generator with review and save flow.

---

## Rollout

- Non-breaking addition: all existing prebuilt agents, chat sessions, and workflows continue to function normally.
- Backward compatibility maintained for all existing endpoints.
