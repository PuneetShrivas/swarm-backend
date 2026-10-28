# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-10-28

### Added
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
