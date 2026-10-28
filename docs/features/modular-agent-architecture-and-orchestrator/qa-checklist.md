# QA Checklist: Modular Agent Architecture & Orchestrator

*Created: 2026-10-28T17:20:00+05:30*  
*Completed: 2026-10-28T17:36:00+05:30*

## Backend Architecture
- [x] Directory structure established:
  - [x] `backend/app/agents/base.py`
  - [x] `backend/app/agents/registry.py`
  - [x] `backend/app/agents/orchestrator/`
  - [x] `backend/app/agents/researcher/`
  - [x] `backend/app/agents/coder/`
  - [x] `backend/app/agents/reviewer/`
  - [x] `backend/app/agents/data_analyst/`
  - [x] `backend/app/agents/synthesizer/`
- [x] Each agent directory contains the standardized 5 asset files:
  - [x] `config.json`
  - [x] `prompt.md`
  - [x] `tools.py`
  - [x] `skills.json`
  - [x] `mcp.json`

## Agent Functionality
- [x] **Orchestrator**: Dispatches intent, decomposes goals, and synthesizes responses.
- [x] **Researcher**: Executes investigation, facts verification, and citations.
- [x] **Coder**: Writes clean code, generates test suites, and adheres to design standards.
- [x] **Reviewer**: Evaluates code quality, checks security flaws, and reports findings.
- [x] **Data Analyst**: Aggregates metrics, formats structured tables, and evaluates trends.
- [x] **Synthesizer**: Writes executive summaries, guides, and documentation.

## API Endpoints
- [x] `GET /api/health`: Reports 6 active agents online.
- [x] `GET /api/agents`: Returns all 6 agents with tools, skills, and MCP configurations.
- [x] `GET /api/agents/{agent_id}`: Returns single agent profile details.
- [x] `POST /api/agents`: Allows registering new custom agents at runtime.
- [x] `POST /api/chat`: Accurately routes to targeted or inferred agents and logs tool telemetry.

## Frontend Implementation (Phases F1 - F3)
- [x] **Phase F1: Data Models & Types**:
  - [x] Extended `Agent` interface with `tools`, `skills`, `mcp_servers`, `system_prompt`, `is_orchestrator`.
  - [x] Added `AgentTool`, `AgentSkill`, and `AgentMCPServer` interfaces in `types.ts`.
  - [x] Enriched `MessageMetadata` with `skills_invoked`, `agent_name`, and execution tracking.
- [x] **Phase F2: Navigation & Roster Controls**:
  - [x] Pinned Orchestrator at the top of the sidebar with distinct visual border.
  - [x] Displayed live capability badges (`⚡ tools`, `✦ skills`, `🔌 mcp`) on roster items.
  - [x] Structured target dropdown in `ChatHeader` with `<optgroup>` division for specialized agents.
  - [x] Added interactive status pill opening the inspector modal.
- [x] **Phase F3: Capability Inspector & Delegation Tracing**:
  - [x] Created `AgentDetailsModal` with 4 interactive tabs (Overview, Tools, Skills, MCP).
  - [x] Rendered tool parameters with formatted JSON schema inspection.
  - [x] Surfaced Orchestrator delegation trace banner in message responses.
  - [x] Displayed MCP server pill badges and skills chips on message turn cards.
  - [x] Verified zero ESLint errors and Next.js static build passing (7/7 routes).
