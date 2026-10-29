# Feature: Revamp Default Agent Tools, Skills, and MCP Execution Engine

- **Feature Slug**: `revamp-agent-tools-skills-mcp`
- **Datetime**: 2026-10-29T15:46:00+05:30

## Status

Draft | In progress

## Goal

1. **Complete & Usable Tools for All 9 Default Agents**:
   - Audit and revamp `tools.py` for all 9 default agents (`orchestrator`, `coder`, `data_analyst`, `researcher`, `reviewer`, `synthesizer`, `general_assistant`, `file_creator`, `file_parser`).
   - Fix missing `TOOLS` definitions and `TOOL_HANDLERS` in `file_creator` and `file_parser`.
   - Implement functional, robust Python handlers for all declared tools (e.g., code execution sandbox, correlation calculation, table of contents generator, markdown linter, citation extractor, OWASP scanner, AST syntax validator, etc.).
2. **Revamped & Comprehensive Skills**:
   - Audit and revamp `skills.json` across all 9 agents, defining rich domain capabilities with explicit semantic triggers for intent classification and swarm routing.
3. **MCP Runtime, Server Usability & Fallback Handlers**:
   - Build `backend/app/mcp/` module with a unified `MCPManager` and `app.mcp.gateway`.
   - Provide native in-process executors for all declared MCP tools (`filesystem`, `git`, `sqlite-analytics`, `postgres`, `fetch`, `brave-search`, `sentry-audit`, `markdown-tools`, `swarm-gateway`, `filesystem_exporter`, `schema_validator`, `knowledge-base`) ensuring 100% reliability in serverless environments (like Vercel) while supporting external CLI transports (`npx`, `uvx`) when available.
   - Add `execute_mcp_tool` to `BaseAgent`.
   - Expose backend execution endpoints: `POST /api/agents/{agent_id}/tools/{tool_name}/execute` and `POST /api/agents/{agent_id}/mcp/{server_name}/tools/{tool_name}/execute`.
4. **Interactive Frontend Usability**:
   - Upgrade `AgentDetailsModal.tsx` to allow users to interactively test and run any Python tool or MCP tool directly with sample inputs and real-time output preview.

## Scope

- In scope:
  - All 9 agent packages under `backend/app/agents/*/`: `tools.py`, `skills.json`, `mcp.json`.
  - `backend/app/agents/base.py`: Add `execute_mcp_tool` and tool metadata methods.
  - `backend/app/mcp/`: Create `manager.py`, `gateway.py`, and `__init__.py`.
  - `backend/app/main.py`: Add REST endpoints for direct tool execution and MCP execution.
  - `backend/test_endpoints.py`: Add comprehensive unit & integration tests covering tools and MCP execution across agents.
  - `frontend/src/app/chat/components/AgentDetailsModal.tsx`: Add interactive tool and MCP runner testing UI.
- Out of scope:
  - Modifying Supabase authentication schema.

## Proposed Behavior

- All 9 agents will have at least 3-5 production-grade functional tools with fully implemented Python handlers.
- `execute_tool` will execute safe, deterministic Python logic returning structured dicts.
- `execute_mcp_tool` will seamlessly execute MCP tools, returning standard Model Context Protocol response blocks (`{"content": [{"type": "text", "text": "..."}]}`).
- Users in the UI can open any agent profile, browse their tools and MCP servers, and trigger live test executions.

## Implementation Steps

1. **Step 1**: Audit and Revamp Tools & Skills for all 9 Default Agents:
   - Fix `file_creator/tools.py` and `file_parser/tools.py`.
   - Expand `coder`, `data_analyst`, `researcher`, `reviewer`, `synthesizer`, `orchestrator`, `general_assistant` tools and handlers.
   - Update `skills.json` across all agents with triggers and descriptions.
2. **Step 2**: Implement the Core MCP Runtime (`backend/app/mcp/`):
   - Create `manager.py` implementing native, sandboxed, high-performance handlers for all standard MCP tools (`filesystem`, `git`, `sqlite-analytics`, `fetch`, `markdown-tools`, `sentry-audit`, `swarm-gateway`).
   - Create `gateway.py` for swarm gateway MCP integration.
   - Integrate `execute_mcp_tool` into `BaseAgent`.
3. **Step 3**: Expose Tool & MCP Execution REST Endpoints in `main.py`:
   - `POST /api/agents/{agent_id}/tools/{tool_name}/execute`
   - `POST /api/agents/{agent_id}/mcp/{server_name}/tools/{tool_name}/execute`
   - `GET /api/mcp/servers`
4. **Step 4**: Interactive Tool & MCP Runner UI in `AgentDetailsModal.tsx`.
   - Add interactive parameter input forms and output inspectors for tools and MCP servers.
5. **Step 5**: Automated Backend Tests & Production Build:
   - Add comprehensive tests in `test_endpoints.py` testing tool execution and MCP execution across agents.
   - Run `npm --prefix frontend run build`.
6. **Step 6**: Documentation, Git Sync, and Vercel Deployment.
