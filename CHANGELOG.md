# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-10-29

### Added
- **Dedicated Agents Studio & Roster Page (`/agents`)**:
  - Full-stack agents studio elevating specialized agents as a foundational pillar alongside Chat and Workflows.
  - Interactive grid displaying both Swarm Core built-in specialists and custom user agents with Linear styling.
  - Category filtering (`All`, `Swarm Core`, `Custom Agents`), dynamic search, and capability counters (tools, skills, MCP).
  - Quick action connectors: Test in Playground, start Chat with preselected agent, Inspect capabilities, Edit, and Delete.
- **Agent Playground (`AgentPlaygroundModal`)**:
  - Isolated testing environment enabling users to test any agent with custom prompts.
  - Live execution telemetry tracking duration (ms) and token consumption.
  - Structured output inspector displaying formatted Markdown responses with one-click copy, tool execution traces, and raw JSON.
- **Custom Agent Editor (`AgentEditorModal`)**:
  - Visual editor for creating and updating custom agents with name, slug, role, description, and system prompt guidelines.
  - Model override dropdown (`gemini-2.5-flash`, `gemini-2.5-pro`, `sonar`, `sonar-pro`) and temperature slider (0.0 to 1.0).
  - Icon picker for personalized agent visual identity.
- **Generative AI Agent Architect (`AIAgentGeneratorModal`)**:
  - Synthesize complete custom agents from natural language requirements using Gemini (`POST /api/ai/generate-agent`).
  - Interactive review-before-save screen allowing users to refine the generated persona and instructions before committing to their library.
- **Backend Custom Agent Update Endpoint**:
  - Implemented `PUT /api/custom-agents/{agent_id}` supporting updates to custom agent profiles with synchronization to `agent_registry`.
  - Added Test 33 to automated test suite verifying custom agent updates.

- **Advanced Workflow Block Types (`condition`, `python_code`, `loop`, `artifact`)**:
  - **Condition Block**: Safe AST expression evaluation directing control flow to configurable `true_target_step_id` or `false_target_step_id`.
  - **Python Code Block**: Sandboxed in-process Python execution accepting `inputs`, `previous_outputs`, and `context`, with runtime timeouts and syntax validation.
  - **Loop Block**: Iteration cycles looping back to target steps with safety `max_loop_iterations` limits (1-10) and termination condition expressions.
  - **Artifact Block**: Persistent structured document generator producing Markdown, Code, JSON, and Executive Reports stored in workflow run records.
- **DAG Nearest-Edge Dynamic Snapping**:
  - Outfitted nodes with 4-directional perimeter connection handles (Top, Bottom, Left, Right).
  - Implemented dynamic nearest-edge calculation (`getOptimalEdgeHandles`) snapping edges to the closest perimeter faces of parent and child blocks.
  - Enhanced `DataFlowEdge` with branch badges (`True Branch` in emerald, `False Branch` in rose, `Loop Iteration` in cyan).
- **Interactive Click-to-Expand DAG Blocks**:
  - Clicking any node expands an inline configuration panel directly on the 2D canvas.
  - Provides inline code editors, expression inputs, target selectors, and unit testing without leaving the visual canvas.
  - Floating "+ Add Block" palette to add any of the 5 block types in 1 click.
- **Real Live Web Search & Perplexity Integration**:
  - Researcher agent upgraded with real live web searching using DuckDuckGo HTML scraping fallback + Perplexity Sonar API.
  - URL citation extraction and formatted Markdown sources.
  - Configured `PERPLEXITY_API_KEY` and `PERPLEXITY_MODEL` in `.env.example` and backend runner.
- **Base Conversational Agent (`general_assistant`)**:
  - Added general chat agent with friendly conversational profile.
  - Intelligent intent routing directing casual greetings to `general_assistant` without colliding with specialist domain keywords.
- **Model Selection Override**:
  - Enabled users to select specific models (`gemini-2.5-flash`, `gemini-2.5-pro`, `sonar`, `sonar-pro`) per workflow step and in the Chat screen header.

### Fixed
- Fixed runtime ReferenceError `onRunSystemTest is not defined` when loading workflow studio.

## [Unreleased] - 2026-10-28

### Added
- **Chat `/workflows` Slash Command & Command Palette**:
  - Interactive floating command menu in `ChatInput.tsx` triggered by typing `/`, with keyboard navigation (`ArrowUp`, `ArrowDown`, `Enter`, `Tab`, `Escape`).
  - Instant command execution: typing or selecting `/workflows` or `/workflow` immediately opens the `WorkflowPickerModal` to launch multi-agent pipelines directly from chat.
  - Added direct command interceptor in chat submission handler to prevent accidental prompt submissions.
- **Linear Design System Compliance (`DESIGN.md`)**:
  - Configured pure Linear palette tokens: `#010102` canvas, 4-step surface ladder (`#0f1011` to `#191a1b`), 1px `#23252a` hairline borders, and signature `#5e6ad2` Linear lavender-blue accent.
  - Set default theme to Linear dark canvas across `:root` and `.dark` in `globals.css` and extended `tailwind.config.ts`.
  - Reskinned Landing Page (`/`): Replaced atmospheric gradients with technical charcoal panels, hairline borders, negative display tracking, and direct workflows links.
  - Reskinned Chat Workspace (`/chat`): Charcoal sidebar, surface-2 active highlights, Linear header, and surface-lifted message bubbles with semantic ratings.
  - Reskinned Workflows Dashboard (`/workflows`) and Studio (`/workflows/[id]`): Linear pill toggles, card grid, and modal styling.
  - Reskinned Login Page (`/login`): Charcoal authentication container with matching Supabase ThemeSupa lavender variables.
- **Rich Visual DAG Studio & Data Flow Edges**:
  - `DataFlowEdge`: Custom React Flow edge rendering smooth Bezier curves in `#5e6ad2`, animated pulse, and centered data flow pills displaying exact variable bindings (`{{inputs.query}}` or `{{steps.<id>.output.text}}`), with hover disconnect action.
  - Upgraded `GoalNode`: Displays root objective, input parameters schema, and output data handles.
  - Upgraded `StepNode`: Displays agent avatar, step number pill, inline variable token syntax highlighting for `{{variable}}` bindings, attached tools & docs badges, and on-node unit test and deletion actions.
  - Topological DAG Auto-Layout ("Tidy Up"): Algorithmic depth ranking and centered layering that automatically organizes the workflow graph into clear hierarchical stages.
  - Floating Canvas Inserter ("+ Add Step"): One-click action to append new steps directly on the DAG canvas.
- **Multi-Agent Workflow Builder & Visual DAG Studio**:
  - Full-stack workflow creation and debugging platform accessible at `/workflows`.
  - Dual-mode editor switching between **Structured Card Editor** and **Visual React Flow DAG Editor** (`@xyflow/react`) with bidirectional state synchronization.
  - Custom React Flow node components (`GoalNode`, `StepNode`) with dynamic input/output handles and dependency edge connections.
  - Multi-tab workflow studio: Steps editor, Python Script Tools, Knowledge Base Documents, and Runs Debugger.
- **Sandboxed Python Script Tool Runner**:
  - In-process execution runner enforcing AST security validation preventing dangerous imports (`os`, `sys`, `subprocess`, `shutil`, `socket`).
  - Standardized tool interface: `def execute(input_data: dict, context: dict) -> dict`.
  - Strict 5-second timeout, memory protection, and stdout/stderr capture with live test console.
- **Workflow Knowledge Base Context Ingestion**:
  - Document attachment support for `.txt`, `.md`, `.csv`, `.json`, and `.pdf` files.
  - Automatic text extraction and context prompt formatting injected into step agents.
- **User Custom Agents**:
  - Ability for users to create and manage custom agents beyond the 6 prebuilt agents (`user_agents` table and dynamic registration in `AgentRegistry`).
- **Two-Tier Testing Framework**:
  - **Step Unit Testing**: Isolated single-step unit test drawer with mock variables and immediate latency/token feedback.
  - **System Testing**: Full topological DAG pipeline execution with variable interpolation (`{{inputs.*}}`, `{{steps.*.output}}`).
- **Workflow Runs & Telemetry Debugger**:
  - Detailed runs history, step-by-step latency timelines, per-agent token usage, and tool output traces.
- **View-Only Sharing & Workflow Forking**:
  - Shareable URLs (`/workflows/share/<shareSlug>`) enforced with read-only database policies.
  - 1-click **Fork Workflow** action cloning workflows into user's personal studio.
- **Chat Workflow Invocation**:
  - Dedicated "Run Workflow" modal launcher and `/workflow` slash command in `/chat`.
  - Interactive workflow execution card in conversation message history showing real-time step badges and execution summary.
- **Modular Agent Package Architecture**: Standardized filesystem-based agent packages (`backend/app/agents/<agent_id>/`) with isolated asset files (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`).
- **Autonomous Swarm Orchestrator**: Refactored the orchestrator into a first-class agent (`orchestrator`) with goal decomposition and delegation tools (`swarm_router`, `swarm_delegate`).
- **Expanded Core Swarm Roster (6 Agents)**:
  - `orchestrator`: Central cognitive coordinator and task dispatcher.
  - `researcher`: Deep investigative research, evidence gathering, and citation verification.
  - `coder`: Production-grade software development, testing, and system design.
  - `reviewer`: Security auditing, code review, and QA compliance validation.
  - `data_analyst`: Numerical calculations, statistical aggregations, and tabular intelligence.
  - `synthesizer`: Technical documentation, executive briefings, and cross-agent synthesis.
- **Dynamic Agent Registry**: Filesystem scanner (`AgentRegistry`) providing auto-discovery, case-insensitive ID lookups, custom agent registration, and hot-reload.
- **Agent Detail API**: `GET /api/agents/{agent_id}` for granular inspection of prompts, tools, skills, and MCP connectivity.
- **Frontend Modular Swarm UI & Inspector Modal**:
  - `AgentDetailsModal`: 4-tab interactive modal inspecting agent personas, markdown system prompts, tool JSON schemas, domain skills, and MCP server transports.
  - Pinned Orchestrator card in `SessionSidebar` with distinct glowing border and real-time capability badges (`⚡ tools`, `✦ skills`, `🔌 mcp`).
  - Hierarchical routing dropdown in `ChatHeader` with `<optgroup>` groupings for specialized swarm agents and interactive status badge.
  - Transparent Orchestrator delegation trace banner (`Swarm Orchestrator dispatched to Coder Agent`) and MCP server pills in message history.
- **Comprehensive Frontend Architecture Plan**: Detailed specification in `docs/features/modular-agent-architecture-and-orchestrator/frontend-plan.md` outlining data models, sidebar roster, header dropdowns, and interactive agent details modal.
- **Dynamic Multi-Palette Theming**: Support for 5 curated aesthetic palettes (`slate`, `nebula`, `emerald`, `amber`, `frost`) with zero-FOUC persistence in `localStorage`.
- **Mode Switching**: Full `light`, `dark`, and `system` mode support via `next-themes` and semantic CSS variables.
- **Interactive Theme Switcher**: Accessible, animated popover component (`ThemeSwitcher.tsx`) with real-time palette swatches, mode toggles, and Framer Motion micro-interactions.
- **Modern Landing Page**: Complete redesign with sticky glassmorphism navbar, hero mesh glow matching the active palette, live status pills, and capability cards.
- **Synced Login Page**: Revamped auth container with glassmorphic backdrop, back-to-home link, and synchronized `@supabase/auth-ui-react` appearance theme.
- **Polished Chat Workspace**:
  - `SessionSidebar`: Modern conversation list items, active selection pills, inline edit controls, deletion confirmations, and collapsible agent roster.
  - `ChatHeader`: Sticky navbar with embedded `ThemeSwitcher`, active agent badge, model dropdown, token usage counter, and action buttons.
  - `MessageItem`: Styled user and agent bubbles, syntax-highlighted code block formatting, tool call disclosure accordion, and sibling branch switcher (`< 1 / 2 >`).
  - `ChatInput`: Floating input dock with auto-resize textarea, focus ring glow, and keyboard shortcut tips.
  - `UsageModal`: Themed telemetry modal with glowing token/query metric cards, breakdown by agent and model, and execution latency logs.

### Changed
- Refactored `frontend/tailwind.config.ts` and `frontend/src/app/globals.css` to use semantic HSL tokens (`background`, `foreground`, `card`, `primary`, `muted`, `accent`, `border`, `ring`).
