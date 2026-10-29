# Feature: Dedicated Agents Page & Custom Agent Studio

*Created: 2026-10-29T06:58:00+05:30*  
*Status: Complete*  
*Completed At: 2026-10-29T07:06:00+05:30*

## Goal

Provide a dedicated, cohesive **Agents Page & Studio** (`/agents`) within the Swarm platform that elevates agents to a first-class pillar alongside Chat and Workflows.
This allows users to:
1. Browse the complete roster of swarm agents (both built-in specialists and custom user agents) with rich metadata, capabilities, tools, and model information.
2. Create and edit custom specialized agents with customized personas, roles, system instructions, model selections (`gemini-2.5-flash`, `gemini-2.5-pro`, `sonar`, `sonar-pro`), and sampling temperature.
3. Interactively test agents with custom inputs in an isolated **Agent Playground**, inspecting live responses, latency, token consumption, and tool execution traces.
4. Generate custom agents from natural language requirements using the **AI Agent Architect** (`/api/ai/generate-agent`), reviewing and refining the generated specifications before saving.
5. Immediately launch chats with any selected agent (`/chat`) or employ them in workflow pipelines (`/workflows`).

---

## Scope

### In Scope
- **Backend API Additions**:
  - Add `PUT /api/custom-agents/{agent_id}` in `backend/app/main.py` allowing users to update existing custom agent configurations (name, role, description, system prompt, model, temperature, icon, tools).
  - Add update method in `backend/app/workflows/tool_runner.py` or `memory_store` for local persistence fallback and Supabase table update.
  - Add Test 33 to `backend/test_endpoints.py` covering updating custom agents and verifying persistence.
- **Frontend Architecture & Components**:
  - `frontend/src/app/agents/page.tsx`: Dedicated Agents Studio dashboard compliant with Linear design system (`#010102` canvas, `#0f1011` cards, `#23252a` hairline borders, `#5e6ad2` accents).
  - `frontend/src/app/agents/components/AgentCard.tsx`: Linear card presenting agent details, status badges, tools count, skills, and quick actions (Playground test, Chat, Edit, Delete).
  - `frontend/src/app/agents/components/AgentEditorModal.tsx`: Comprehensive modal for creating and updating custom agents with model selection and temperature controls.
  - `frontend/src/app/agents/components/AgentPlaygroundModal.tsx`: Interactive isolated testing sandbox with custom prompt inputs, live execution telemetry, markdown preview, and tool execution traces.
  - `frontend/src/app/agents/components/AIAgentGeneratorModal.tsx`: Generative agent architect modal enabling users to describe agent needs and review/edit generated configurations before saving.
  - Integration with `AppNavigationRail` (`currentTab="agents"`).

### Out of Scope
- Direct local Python execution without sandboxing (all agents and tools execute within sandbox environments).
- Altering existing Supabase database schema (`user_agents` table columns remain standard).

---

## Current Behavior

- The top navigation bar in `AppNavigationRail.tsx` contains a tab link to `/agents`, but accessing it returns a 404 Not Found error because the route directory does not exist.
- Users can view prebuilt agents in a small inspector modal in `/chat`, but cannot browse a full dedicated roster, create new custom agents via a visual UI, edit existing custom agents, test agents in an isolated playground, or use the backend AI agent generator endpoint from the UI.
- The backend has `POST /api/custom-agents` and `DELETE /api/custom-agents/{agent_id}`, but is missing a `PUT /api/custom-agents/{agent_id}` endpoint for updating an existing agent profile.

---

## Proposed Behavior

1. **Dedicated Route `/agents`**:
   - Clean, high-density dashboard displaying active Swarm agents (Orchestrator, Researcher, Coder, Reviewer, Data Analyst, Synthesizer, General Assistant) and custom user agents.
   - Filter tabs: `All Agents`, `Swarm Core (7)`, `Custom Agents`.
   - Search bar filtering by agent name, role, or description.
   - Quick header actions: `+ New Agent` and `✨ AI Agent Generator`.
2. **Interactive Agent Playground**:
   - Clicking "Test" on any agent card opens `AgentPlaygroundModal`.
   - Users can input arbitrary prompts, run isolated tests via `POST /api/custom-agents/test`, and inspect the formatted markdown output, token count, execution latency, and tool invocations.
3. **Agent Editor Modal**:
   - Create or edit custom agents: Name, Role, Description, System Prompt instructions, Model (`gemini-2.5-flash`, `gemini-2.5-pro`, `sonar`, `sonar-pro`), Temperature slider (0.0 to 1.0), and Icon picker.
   - Validates input and persists to Supabase or in-memory store.
4. **AI Agent Architect**:
   - Clicking `✨ AI Agent Generator` opens `AIAgentGeneratorModal`.
   - Users prompt in natural language (e.g. "Create a database query optimization expert that analyzes SQL plans and indexes").
   - Gemini generates the profile, displaying a full review card before the user commits it to their library.
5. **Direct Actions**:
   - 1-click "Chat with Agent" button navigates directly to `/chat` with that agent preselected.

---

## Implementation Steps

1. **Phase 1: Backend Update Endpoint & Tests**:
   - Implement `PUT /api/custom-agents/{agent_id}` in `backend/app/main.py`.
   - Update `memory_store.update_user_agent` in `backend/app/workflows/engine.py` / `main.py`.
   - Add Test 33 in `backend/test_endpoints.py` testing update and verification.
   - Verify all 33 tests pass.
2. **Phase 2: Frontend Agent Components**:
   - Create `frontend/src/app/agents/components/AgentCard.tsx`.
   - Create `frontend/src/app/agents/components/AgentEditorModal.tsx`.
   - Create `frontend/src/app/agents/components/AgentPlaygroundModal.tsx`.
   - Create `frontend/src/app/agents/components/AIAgentGeneratorModal.tsx`.
3. **Phase 3: Agents Page Dashboard**:
   - Create `frontend/src/app/agents/page.tsx` integrating `AppNavigationRail`, filter tabs, search bar, agent grid, and modals.
4. **Phase 4: Full Verification & Documentation**:
   - Run `python backend/test_endpoints.py`.
   - Run `npm --prefix frontend run lint`.
   - Run `npm --prefix frontend run build`.
   - Update `verification.md`, `qa-checklist.md`, `implementation.md`, and `CHANGELOG.md`.

---

## Files to Change

| File | Change | Reason |
| :--- | :--- | :--- |
| `backend/app/main.py` | Add `PUT /api/custom-agents/{agent_id}` endpoint | Enable updating custom agent configurations |
| `backend/test_endpoints.py` | Add Test 33 for custom agent update | Automated regression coverage |
| `frontend/src/app/agents/components/AgentCard.tsx` | New component | Display agent card with Linear tokens and actions |
| `frontend/src/app/agents/components/AgentEditorModal.tsx` | New component | Visual modal to create/edit custom agents |
| `frontend/src/app/agents/components/AgentPlaygroundModal.tsx` | New component | Interactive testing console with telemetry |
| `frontend/src/app/agents/components/AIAgentGeneratorModal.tsx` | New component | Natural language agent generation and review |
| `frontend/src/app/agents/page.tsx` | New page route | Dedicated Agents Studio dashboard |
| `CHANGELOG.md` | Add changelog entry | Keep a Changelog documentation |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| Built-in agents accidentally edited or deleted | System instability | Built-in Swarm Core agents are immutable; Edit and Delete actions are strictly restricted to user custom agents (`is_custom: true`) |
| In-memory fallback desync if Supabase is offline | Data loss on restart | Maintain deterministic local memory store with fallback handling and helpful user notifications |
| Testing latency or token limits during playground runs | Poor user feedback | Display visual spinner, duration counter, and clear error banners in Playground modal |
