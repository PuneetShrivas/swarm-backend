# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-10-28

### Added
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
