# Implementation Guide: Modular Agent Architecture & Orchestrator

*Created: 2026-10-28T17:20:00+05:30*

## Overview

This document tracks the tasks for transitioning backend agents into a modular directory structure with standardized asset files, enhancing the orchestrator as an autonomous agent, and providing tool/skill/MCP connectivity.

## Implementation Tasks

### 1. Framework Models & Base Agent
- [x] Create `backend/app/agents/__init__.py`.
- [x] Create `backend/app/agents/base.py` with `AgentConfig`, `ToolDefinition`, `SkillDefinition`, `MCPServerConfig`, `AgentProfile`, and `BaseAgent`.
- [x] Implement asset loading logic (`load_from_dir`) that parses `config.json`, `prompt.md`, `tools.py`, `skills.json`, and `mcp.json`.

### 2. Dynamic Agent Registry
- [x] Create `backend/app/agents/registry.py` with `AgentRegistry` singleton.
- [x] Implement directory scanning to discover all agent packages in `backend/app/agents/*/`.
- [x] Implement query methods: `get(agent_id)`, `get_all()`, `get_orchestrator()`, `reload()`.

### 3. Standardized Agent Packages
- [x] **Orchestrator** (`backend/app/agents/orchestrator/`):
  - `config.json`: Master dispatcher configuration (`is_orchestrator: true`).
  - `prompt.md`: Cognitive hub, intent decomposition, and delegation instructions.
  - `tools.py`: Routing and delegation tools (`swarm_router`, `swarm_delegate`).
  - `skills.json`: Skills (`intent_classification`, `task_decomposition`, `response_synthesis`).
  - `mcp.json`: MCP connectivity config.
- [x] **Researcher** (`backend/app/agents/researcher/`):
  - `config.json`: Research agent settings.
  - `prompt.md`: Structured deep research persona.
  - `tools.py`: Tools (`web_search_query`, `extract_citations`, `fact_check`).
  - `skills.json`: Skills (`literature_review`, `comparative_analysis`).
  - `mcp.json`: MCP fetch / search connections.
- [x] **Coder** (`backend/app/agents/coder/`):
  - `config.json`: Software engineering settings.
  - `prompt.md`: Production code, testing, and architecture persona.
  - `tools.py`: Tools (`syntax_validator`, `generate_test_suite`, `diff_patcher`).
  - `skills.json`: Skills (`refactoring`, `debugging`, `type_design`).
  - `mcp.json`: MCP filesystem / git connections.
- [x] **Reviewer** (`backend/app/agents/reviewer/`):
  - `config.json`: QA and code review settings.
  - `prompt.md`: Critical evaluation and security audit persona.
  - `tools.py`: Tools (`security_audit`, `complexity_analysis`).
  - `skills.json`: Skills (`vulnerability_scan`, `compliance_verification`, `test_gap_analysis`).
  - `mcp.json`: MCP linter / scanner connections.
- [x] **Data Analyst** (`backend/app/agents/data_analyst/`):
  - `config.json`: Data science and analytics settings.
  - `prompt.md`: Quantitative reasoning and statistical persona.
  - `tools.py`: Tools (`calculate_statistics`, `format_csv_table`).
  - `skills.json`: Skills (`trend_analysis`, `distribution_modeling`, `data_cleansing`).
  - `mcp.json`: MCP postgres / sqlite connections.
- [x] **Synthesizer** (`backend/app/agents/synthesizer/`):
  - `config.json`: Tech writer and executive reporting settings.
  - `prompt.md`: Technical documentation and executive briefing persona.
  - `tools.py`: Tools (`generate_executive_summary`, `format_readme`).
  - `skills.json`: Skills (`briefing_synthesis`, `documentation_design`, `narrative_refinement`).
  - `mcp.json`: MCP markdown / docs connections.

### 4. FastAPI Integration & Routing Overhaul
- [x] Update `backend/app/main.py`:
  - Initialize and load `AgentRegistry` on startup.
  - Connect `GET /api/agents` to return profiles from `AgentRegistry`.
  - Add `GET /api/agents/{agent_id}` endpoint for deep agent inspection.
  - Update `route_agent()` to leverage the `orchestrator` agent and registry lookup.
  - Update `POST /api/chat` to record tool calls and skills in message metadata.

### 5. Detailed Frontend Architectural Planning
- [x] Document all needed frontend changes in `docs/features/modular-agent-architecture-and-orchestrator/frontend-plan.md` covering:
  - Extended TypeScript interfaces.
  - Swarm Roster UI updates.
  - Chat Header target selector updates.
  - Message feed tool/skill visualization.
  - Interactive Agent Details Drawer/Modal.

### 6. Automated Verification & Definition of Done
- [x] Update `backend/test_endpoints.py` to test all 6 agents and new endpoints.
- [x] Run backend tests and verify 100% pass rate.
- [x] Update `docs/architecture/decisions.md` (ADR 003).
- [x] Update `verification.md` and `qa-checklist.md`.
- [x] Add entry to `CHANGELOG.md`.

---

## Execution Log

### Step 1: Framework Models & Base Agent (2026-10-28T17:25:00+05:30)
- **Files Changed:**
  - `backend/app/agents/__init__.py`: Package init exporting `BaseAgent`, `AgentConfig`, `AgentProfile`, `ToolDefinition`, `SkillDefinition`, `MCPServerConfig`.
  - `backend/app/agents/base.py`: Domain models for agent configuration, tools schema, skills triggers, and MCP transport connectivity; implemented `BaseAgent` with automatic file resolution for `config.json`, `prompt.md`, `tools.py` (via dynamic module spec), `skills.json`, and `mcp.json`.
- **Reason:** Establish the core architectural foundation and deserialization logic for standardized, filesystem-based agents.
- **Tests Added/Updated:** Verified Python module import and model schema definitions via test command.
- **Commands Run:**
  - `& "backend\venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, 'backend'); import app.agents.base as b; print('base.py imported successfully')"`: Exit code 0 (`base.py imported successfully`).
- **Result:** Success. Base models and asset loading engine implemented cleanly.

### Step 2: Dynamic Agent Registry (2026-10-28T17:26:00+05:30)
- **Files Changed:**
  - `backend/app/agents/registry.py`: Implemented `AgentRegistry` singleton featuring directory auto-discovery, package validation, case-insensitive ID lookups, runtime custom agent storage, orchestrator selection, and asset reload.
  - `backend/app/agents/__init__.py`: Exported `AgentRegistry` and `agent_registry` singleton.
- **Reason:** Provide unified discovery, caching, and management of filesystem and runtime agents across the application lifecycle.
- **Tests Added/Updated:** Verified initialization and discovery via standalone Python command.
- **Commands Run:**
  - `& "backend\venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, 'backend'); from app.agents import agent_registry; agent_registry.initialize(); print(f'AgentRegistry initialized cleanly, agents loaded: {len(agent_registry.get_all())}')"`: Exit code 0 (`AgentRegistry initialized cleanly, agents loaded: 0`).
- **Result:** Success. Registry initialized and ready for standardized agent asset packages.

### Step 3: Standardized Agent Packages (2026-10-28T17:30:00+05:30)
- **Files Changed:**
  - `backend/app/agents/orchestrator/` (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`): Implemented Swarm Orchestrator with `swarm_router` and `swarm_delegate` tools, intent classification, task decomposition, and swarm gateway MCP.
  - `backend/app/agents/researcher/` (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`): Implemented Research Agent with `web_search_query` and `fact_check` tools, literature review skills, and fetch/search MCP servers.
  - `backend/app/agents/coder/` (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`): Implemented Coder Agent with `syntax_validator` and `diff_patcher` tools, refactoring/debugging skills, and filesystem/git MCP servers.
  - `backend/app/agents/reviewer/` (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`): Implemented Reviewer Agent with `security_audit` and `complexity_analysis` tools, vulnerability scanning skills, and Sentry audit MCP.
  - `backend/app/agents/data_analyst/` (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`): Implemented Data Analyst Agent with `calculate_statistics` and `format_csv_table` tools, trend analysis skills, and SQLite/Postgres MCP.
  - `backend/app/agents/synthesizer/` (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`): Implemented Synthesizer Agent with `generate_executive_summary` and `format_readme` tools, documentation design skills, and markdown MCP.
- **Reason:** Provide fully encapsulated, standardized modular packages for all 6 core swarm agents with independent assets.
- **Tests Added/Updated:** Tested multi-agent registry discovery and tool execution via Python CLI.
- **Commands Run:**
  - Discovered 6 agents with tools, skills, and MCP configurations: Exit code 0.
  - Executed `syntax_validator` tool on `coder` agent: Exit code 0 (`valid: True`).
- **Result:** Success. All 6 standardized agent packages loaded dynamically and verified.

### Step 4: FastAPI Integration & Routing Overhaul (2026-10-28T17:32:00+05:30)
- **Files Changed:**
  - `backend/app/main.py`: Connected `AgentRegistry` singleton; updated `Agent` to `AgentProfile`; added `GET /api/agents/{agent_id}` for granular agent inspection; updated `route_agent()` to support multi-skill intent routing with default fallback to `orchestrator`; updated `POST /api/chat` to include agent tools, skills, and MCP telemetry in message metadata.
- **Reason:** Integrate the modular agent packages into the live FastAPI web service and provide backward compatibility with existing chat sessions and Supabase telemetry.
- **Tests Added/Updated:** Validated `/api/agents/orchestrator`, `/api/agents/reviewer`, and 404 for unknown IDs.
- **Commands Run:**
  - `& "backend\venv\Scripts\python.exe" -u backend/test_endpoints.py`: Exit code 0 (All 13 existing endpoint tests pass).
  - Test client verification on `GET /api/agents/orchestrator`: Exit code 0 (200 OK, 2 tools, 3 skills, 1 mcp server).
- **Result:** Success. Modular architecture fully integrated into the API layer.

### Step 5: Detailed Frontend Architectural Planning (2026-10-28T17:33:00+05:30)
- **Files Changed:**
  - `docs/features/modular-agent-architecture-and-orchestrator/frontend-plan.md`: Created detailed architectural document including data models (`AgentTool`, `AgentSkill`, `AgentMCPServer`), UI layout wireframes for `SessionSidebar` roster with orchestrator pinning, `ChatHeader` domain-grouped dropdowns, `MessageItem` delegation trace banners, and a comprehensive 4-tab `AgentDetailsModal` specification with phasing rollout strategy.
- **Reason:** Satisfy prompt requirements to thoroughly plan required frontend adaptations without writing implementation code ahead of explicit user approval.
- **Tests Added/Updated:** N/A (Documentation & architectural specification).
- **Commands Run:** N/A.
- **Result:** Success. Frontend plan completed and documented.

### Step 6: Automated Verification & Definition of Done (2026-10-28T17:36:00+05:30)
- **Files Changed:**
  - `backend/test_endpoints.py`: Expanded test suite from 13 to 17 automated endpoint checks validating all 6 agents (`orchestrator`, `researcher`, `coder`, `reviewer`, `data_analyst`, `synthesizer`), deep inspection via `GET /api/agents/{agent_id}`, 404 for unknown agents, multi-domain heuristic routing (coding, security audit, statistics, generic orchestrator), and custom agent creation.
  - `docs/architecture/decisions.md`: Updated ADR 003 status to Accepted.
  - `docs/features/modular-agent-architecture-and-orchestrator/verification.md`: Logged test outcomes and edge cases.
  - `docs/features/modular-agent-architecture-and-orchestrator/qa-checklist.md`: Marked all validation items verified.
  - `docs/features/modular-agent-architecture-and-orchestrator/plan.md`: Updated status to Complete.
  - `CHANGELOG.md`: Added entry for modular agent architecture and standardized asset packages.
- **Reason:** Satisfy the Definition of Done across automated testing, architectural tracking, and quality assurance.
- **Tests Added/Updated:** 4 new automated tests added to `backend/test_endpoints.py` (total 17/17 passed).
- **Commands Run:**
  - `& "backend\venv\Scripts\python.exe" -u backend/test_endpoints.py`: Exit code 0 (ALL 17 MODULAR ENDPOINT TESTS PASSED SUCCESSFULLY).
  - `npm --prefix frontend run lint`: Exit code 0 (✔ No ESLint warnings or errors).
  - `npm --prefix frontend run build`: Exit code 0 (Compiled successfully, 7/7 static routes generated).
- **Result:** Complete success. All test suites and builds passed with zero errors.

### Phase F1: Frontend Data Models & Types Integration (2026-10-28T17:41:00+05:30)
- **Files Changed:**
  - `frontend/src/app/chat/types.ts`: Extended TypeScript definitions with `AgentTool`, `AgentSkill`, and `AgentMCPServer` interfaces; augmented `Agent` interface with `model`, `temperature`, `is_orchestrator`, `icon`, `description`, `system_prompt`, `tools`, `skills`, and `mcp_servers`; updated `MessageMetadata` with `skills_invoked`, `agent_name`, and execution metrics.
- **Reason:** Align the client-side data contracts with the modular agent profiles provided by the backend registry.
- **Tests Added/Updated:** N/A (Type definition augmentation).
- **Commands Run:**
  - `npm --prefix frontend run lint`: Exit code 0 (✔ No ESLint warnings or errors).
- **Result:** Success. Data models updated with zero lint regressions.

### Phase F2: Swarm Roster & Header Target Dropdown (2026-10-28T17:42:00+05:30)
- **Files Changed:**
  - `frontend/src/app/chat/components/SessionSidebar.tsx`: Updated active swarm roster to automatically pin the Orchestrator at the top with a distinct glowing border; rendered live capabilities chips (`⚡ tools`, `✦ skills`, `🔌 mcp`) for every agent; added an info inspection trigger.
  - `frontend/src/app/chat/components/ChatHeader.tsx`: Structured target dropdown with `Swarm Orchestrator (Auto Routing)` and `<optgroup label="Specialized Agents">`; added interactive status pill that opens the agent inspector.
- **Reason:** Surface the expanded 6-agent roster, capabilities metrics, and orchestrator hierarchy clearly to the user.
- **Tests Added/Updated:** N/A.
- **Commands Run:**
  - `npm --prefix frontend run lint`: Exit code 0 (✔ No ESLint warnings or errors).
- **Result:** Success. Roster and header controls updated with zero lint regressions.

### Phase F3: Inspection Modal & Delegation Tracing (2026-10-28T17:46:00+05:30)
- **Files Changed:**
  - `frontend/src/app/chat/components/AgentDetailsModal.tsx`: Created 4-tab interactive agent inspection modal covering Overview (icon, persona description, model, temperature, raw markdown system prompt), Tools (tool names, descriptions, and full JSON parameter schema view), Skills (skill keywords and invocation triggers), and MCP Servers (transport types, commands/URLs, and associated server tools).
  - `frontend/src/app/chat/components/MessageItem.tsx`: Implemented Orchestrator delegation trace banner ("Swarm Orchestrator dispatched to Coder Agent"), tool call telemetry badges with MCP server pill, and skills invoked chips.
  - `frontend/src/app/chat/page.tsx`: Integrated `AgentDetailsModal` state and `handleInspectAgent` handlers; wired `onInspectAgent` into `SessionSidebar` and `ChatHeader`.
- **Reason:** Complete Phase F3 of the modular agent frontend implementation, enabling full inspection of agent capabilities and transparent visualization of orchestrator delegation traces and MCP tool activity.
- **Tests Added/Updated:** Validated Next.js TypeScript compilation and ESLint checks.
- **Commands Run:**
  - `npm --prefix frontend run lint`: Exit code 0 (✔ No ESLint warnings or errors).
  - `npm --prefix frontend run build`: Exit code 0 (Compiled successfully, 7/7 static routes generated).
  - `& "backend\venv\Scripts\python.exe" -u backend/test_endpoints.py`: Exit code 0 (ALL 17 MODULAR ENDPOINT TESTS PASSED SUCCESSFULLY).
- **Result:** Complete success. All 3 phases of the frontend implementation successfully completed with zero lint or build errors.
