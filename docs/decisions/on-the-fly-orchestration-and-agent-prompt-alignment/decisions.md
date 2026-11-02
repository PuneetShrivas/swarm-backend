# Architectural Decisions: On-the-Fly Workflow Orchestration & Agent Prompt Alignment

**Datetime:** 2026-11-02T12:26:00+05:30  
**Status:** Decided / In Review

## Context

When users ask questions in the chat window, the system must accurately analyze intent, select appropriate agents, and orchestrate either a single-step or multi-step directed acyclic graph (DAG) workflow on the fly. Previously:
1. Queries requiring fresh or real-time internet information failed to automatically select the `researcher` agent (Perplexity Sonar), leading to static fallbacks and potential hallucinations.
2. Several agent prompts imposed persona-specific "flavours" (e.g. unsolicited Big-O analysis, mandatory changelogs/release notes, intrusive statistical metrics) that distorted the user's explicit goal.
3. On-the-fly workflows only used `agent` blocks for all tasks, neglecting deterministic non-agent blocks (`python_code`, `artifact`, `condition`) that execute with zero tokens and sub-millisecond latency.
4. Gaps in the default agent roster forced creative writing, communications, and strategic roadmapping awkwardly into technical agents.

## Decisions

### 1. Fresh Internet Information Detection & Automated Sonar Routing
- **Decision**: Introduce a comprehensive fresh internet information classification mechanism in the Orchestrator.
- **Criteria**: Semantic cues covering temporal recency ("today", "yesterday", "now", "current", "latest", "upcoming", "2025/2026"), real-time domain entities (weather, live stock/crypto quotes, sports results, breaking news, flight status), and web lookup intents ("who is the current", "what happened to", "search web", "fact-check").
- **Action**: When detected, the orchestrator automatically assigns the `researcher` agent with model `sonar` (Perplexity Sonar) for live, cited internet retrieval.

### 2. Goal-Agnostic System Prompts Across All Agents
- **Decision**: Revamp all agent system instructions (`backend/app/agents/*/prompt.md`) to be domain-agnostic and strictly goal-aligned.
- **Enforcement**:
  - The agent must adhere 100% to the user's explicit objective, constraints, and format.
  - No unsolicited secondary agendas or persona tangents:
    - `coder`: No unsolicited Big-O lectures or unrequested boilerplate test suites.
    - `reviewer`: Calibrated, constructive reviews without alarmist vulnerability tables for simple code.
    - `synthesizer`: Direct consolidation answering the user's prompt without unrequested changelogs or release notes.
    - `data_analyst`: General numerical rigor across any domain without forcing financial ratios or complex inferential tests.
    - `file_creator`: Clean file outputs without schema meta-chatter.
    - `researcher`: Grounded citations without philosophical cross-examinations.

### 3. Non-Agent Block Optimization
- **Decision**: Instruct the Orchestrator and enhance on-the-fly workflow synthesis to prioritize non-agent blocks (`python_code`, `artifact`, `condition`) wherever operations are deterministic.
- **Rationale**:
  - `python_code` executes in ~1ms in a sandboxed runner with 0 LLM tokens and 100% mathematical precision.
  - `artifact` blocks assemble, format, and save structured reports/files without spending LLM tokens on an extra agent turn.
  - `condition` blocks provide 0ms logical branching and quality gates.
  - Preserves LLM agent calls strictly for tasks requiring cognitive reasoning, deep language comprehension, or web research.

### 4. Addition of Default Agents: `writer` and `planner`
- **Decision**: Add two new modular default agents:
  - `writer` (Content & Editorial Specialist): Specialized in essays, articles, blog posts, professional communications, and copywriting.
  - `planner` (Strategic Planning & Decomposition Specialist): Specialized in project roadmaps, milestone planning, and phased execution.
- **Packaging**: Standardized filesystem packages (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`) in `backend/app/agents/` dynamically registered by `agent_registry`.

## Consequences & Alternatives Considered

- *Alternative*: Rely purely on LLM prompt generation for every chat query on the fly.
  - *Rejected*: Pure LLM generation introduces 1.5–3.0 seconds of planning latency before step 1 can start. Using fast, intelligent heuristic decomposition with an LLM fallback combines instant sub-10ms response times with full flexibility.
- *Alternative*: Force all multi-step workflows to save permanently to the database.
  - *Rejected*: Ephemeral execution keeps user workflow libraries clean, with an interactive "Save as Workflow" button to persist on demand.
