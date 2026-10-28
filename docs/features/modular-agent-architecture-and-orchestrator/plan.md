# Feature: Modular Agent Architecture, Standardized Assets, Enhanced Orchestrator, Tools, Skills & MCP Connectivity

## Status

Completed (Backend: 2026-10-28T17:36:00+05:30, Frontend Phases F1-F3: 2026-10-28T17:46:00+05:30)

## Goal

Refactor the backend agent architecture from hardcoded in-memory arrays into a modular, filesystem-based, and standardized agent directory structure (`backend/app/agents/<agent_id>/`). Each agent is encapsulated with its own standardized assets:
- `config.json` (agent metadata, model, temperature, icon, description, status)
- `prompt.md` (isolated system prompt and persona instructions)
- `tools.py` (tool definitions and execution schemas)
- `skills.json` (skill capabilities and triggers)
- `mcp.json` (Model Context Protocol server connectivity configurations)

Additionally:
1. Elevate the **Orchestrator** into its own first-class agent within this new structure, capable of intelligent planning, task decomposition, and delegation routing.
2. Introduce a roster of standard basic agents: `orchestrator`, `researcher`, `coder`, `reviewer`, `data_analyst`, and `synthesizer`.
3. Provide dynamic registry loading (`AgentRegistry`) with auto-discovery, hot-reloading capability, and backward-compatible FastAPI endpoints.
4. Implement all planned frontend improvements across 3 phases:
   - Phase F1: Data models, types & interfaces (`AgentTool`, `AgentSkill`, `AgentMCPServer`).
   - Phase F2: Pinned Orchestrator card, live capabilities badges, and domain-grouped target selection dropdown.
   - Phase F3: 4-tab `AgentDetailsModal` inspector and transparent delegation trace and MCP badges on message turns.

## Scope

- In scope (Backend Implementation):
  - Standardized agent folder architecture under `backend/app/agents/<agent_id>/`.
  - Core agent framework (`backend/app/agents/base.py`, `backend/app/agents/registry.py`).
  - Standardized asset files across all agents: `config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`.
  - 6 Built-in standardized agents:
    - `orchestrator`: Swarm coordinator, task planner, and intent dispatcher.
    - `researcher`: Deep investigative research, synthesis, and fact verification.
    - `coder`: Production-grade software development, debugging, and systems architecture.
    - `reviewer`: Code reviews, security audits, and compliance validation.
    - `data_analyst`: Numerical calculation, data transformations, and metric aggregation.
    - `synthesizer`: Technical documentation, executive reporting, and communication structuring.
  - Integration of `AgentRegistry` into `backend/app/main.py` (`/api/agents`, `/api/health`, `/api/chat`).
  - Tool execution harness for built-in tools (calculator, python evaluator stub, router delegate).
  - MCP connectivity schemas and client connection abstractions.
  - Backward compatibility with existing `/api/chat`, Supabase session persistence, and `test_endpoints.py`.
- In scope (Frontend Planning):
  - Comprehensive architectural plan for frontend data structures, UI components, and user flows.
- Out of scope:
  - Frontend code execution (explicitly restricted per user instruction: "required changes for the frontend need to be planned thoroughly, not implemented yet").
  - Database schema changes (Supabase tables `chat_sessions`, `chat_messages`, `user_usage` remain compatible).

## Current behavior

- All agents are defined in a static list `DEFAULT_AGENTS` in `backend/app/main.py`.
- Prompts are hardcoded strings inside Python code.
- Routing is a naive string-matching helper `route_agent()` in `main.py` with 10 hardcoded keywords.
- No concept of individual agent tools, skills, or Model Context Protocol (MCP) server definitions.
- The Orchestrator is not an agent—it is an implicit fallback branch in a Python function.

## Proposed behavior

1. **Filesystem-Driven Modular Architecture**:
   - Every agent lives in `backend/app/agents/<agent_id>/`.
   - Modifying an agent prompt is as simple as editing `prompt.md`.
   - Modifying model temperature or metadata is done in `config.json`.
   - Adding a new agent only requires creating a folder with the standard 5 asset files; `AgentRegistry` discovers it automatically on startup.
2. **Orchestrator as a First-Class Autonomous Agent**:
   - Has its own directory `backend/app/agents/orchestrator/`.
   - Equipped with delegation tools: `swarm_router` and `swarm_delegate`.
   - Decomposes complex queries and routes to specialists (`researcher`, `coder`, `reviewer`, `data_analyst`, `synthesizer`).
3. **Structured Tools, Skills & MCP Specifications**:
   - `tools.py`: Declares tool schemas in Gemini/OpenAI-compatible format with execution handlers.
   - `skills.json`: Declares high-level skill descriptors (e.g. `ast-parsing`, `benchmarking`, `statistical-modeling`).
   - `mcp.json`: Declares MCP server definitions (e.g., filesystem, memory, fetch, github, postgres).
4. **API Compatibility**:
   - `/api/agents` returns rich agent profiles including `tools`, `skills`, `mcp_servers`, and `is_orchestrator`.
   - `/api/agents/{agent_id}` provides deep inspection of an individual agent's prompt, tools, and MCP state.
   - `/api/chat` coordinates with `AgentRegistry` for execution and telemetry.

## Implementation steps

1. **Framework & Base Classes (`backend/app/agents/base.py`)**:
   - Define Pydantic models: `AgentConfig`, `ToolDefinition`, `SkillDefinition`, `MCPServerConfig`, `AgentProfile`.
   - Implement `BaseAgent` class with asset loader, system prompt builder, and tool execution dispatcher.
2. **Dynamic Agent Registry (`backend/app/agents/registry.py`)**:
   - Implement `AgentRegistry` with filesystem auto-discovery, singleton caching, and CRUD methods.
3. **Build Standardized Agent Folders & Assets**:
   - `backend/app/agents/orchestrator/`: `config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`
   - `backend/app/agents/researcher/`: `config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`
   - `backend/app/agents/coder/`: `config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`
   - `backend/app/agents/reviewer/`: `config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`
   - `backend/app/agents/data_analyst/`: `config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`
   - `backend/app/agents/synthesizer/`: `config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`
4. **Backend API Integration (`backend/app/main.py`)**:
   - Replace `DEFAULT_AGENTS` with `AgentRegistry.get_all()`.
   - Add `/api/agents/{agent_id}` endpoint.
   - Refactor `route_agent()` to leverage orchestrator intelligence and registry lookups.
   - Keep all Supabase session, message, and usage telemetry endpoints 100% intact.
5. **Detailed Frontend Architectural Plan**:
   - Document complete UI specifications in `docs/features/modular-agent-architecture-and-orchestrator/frontend-plan.md`.
6. **Backend Verification**:
   - Update `backend/test_endpoints.py` to test all 6 agents, agent asset loading, orchestrator delegation, and individual agent detail endpoints.
   - Run tests and verify 100% pass rate.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/agents/base.py` | [NEW] | Core domain models (`AgentConfig`, `ToolDefinition`, `SkillDefinition`, `MCPServerConfig`, `BaseAgent`) |
| `backend/app/agents/registry.py` | [NEW] | Dynamic filesystem scanner and singleton registry for all swarm agents |
| `backend/app/agents/orchestrator/*` | [NEW] | Standardized assets for Orchestrator (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`) |
| `backend/app/agents/researcher/*` | [NEW] | Standardized assets for Research Agent |
| `backend/app/agents/coder/*` | [NEW] | Standardized assets for Coder Agent |
| `backend/app/agents/reviewer/*` | [NEW] | Standardized assets for Reviewer / QA Agent |
| `backend/app/agents/data_analyst/*` | [NEW] | Standardized assets for Data Analyst Agent |
| `backend/app/agents/synthesizer/*` | [NEW] | Standardized assets for Synthesizer / Tech Writer Agent |
| `backend/app/main.py` | [MODIFY] | Connect `AgentRegistry`, add `/api/agents/{agent_id}`, update routing to use registry |
| `backend/test_endpoints.py` | [MODIFY] | Validate new agent roster, individual inspection endpoints, and orchestrator routing |
| `docs/features/modular-agent-architecture-and-orchestrator/frontend-plan.md` | [NEW] | Exhaustive frontend architecture plan for future implementation |
| `docs/architecture/decisions.md` | [MODIFY] | Add ADR 003: Filesystem-Based Modular Agent Architecture & Asset Standard |

## Interfaces

```python
class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    handler_name: Optional[str] = None

class SkillDefinition(BaseModel):
    id: str
    name: str
    description: str
    triggers: List[str]

class MCPServerConfig(BaseModel):
    name: str
    transport: str  # "stdio" | "sse"
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    tools: List[str] = Field(default_factory=list)

class AgentProfile(BaseModel):
    id: str
    name: str
    role: str
    status: str
    system_prompt: str
    model: str
    temperature: float
    is_orchestrator: bool
    icon: str
    description: str
    tools: List[ToolDefinition] = Field(default_factory=list)
    skills: List[SkillDefinition] = Field(default_factory=list)
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list)
```

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Backwards compatibility break with existing frontend | Medium | Ensure `/api/agents` returns the exact fields previously consumed (`id`, `name`, `role`, `status`, `system_prompt`) while enriching with optional fields (`tools`, `skills`, `mcp_servers`, `is_orchestrator`). |
| Missing asset files on filesystem | Low | `BaseAgent` provides resilient defaults if optional files (`tools.py`, `mcp.json`, `skills.json`) are absent. |
| Gemini API error when passing tools | Low | Tool declarations use Gemini-compatible schema formats; fallback mock responses remain active when no API key is set. |

## Verification

- Backend Automated Tests: `& "backend\venv\Scripts\python.exe" -u backend/test_endpoints.py` (Must pass all tests).
- Agent Registry Test: Verify all 6 agents load dynamically with non-empty prompts, valid configs, and registered tools.
- API Checks: Test `GET /api/agents`, `GET /api/agents/orchestrator`, `GET /api/agents/coder`, `POST /api/chat`.
