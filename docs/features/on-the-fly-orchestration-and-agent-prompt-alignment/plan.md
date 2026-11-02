# Feature: On-the-Fly Workflow Orchestration & Goal-Agnostic Agent Prompt Alignment

**Datetime:** 2026-11-02T12:25:00+05:30  
**Status:** Draft (Awaiting User Approval)

## Goal

Fix and optimize on-the-fly workflow orchestration for user queries submitted in the chat window by:
1. Dynamically recognizing any question requiring fresh information from the internet (e.g. current events, live prices, weather, sports scores, recent developments) and automatically selecting the `researcher` agent with Perplexity Sonar (`sonar`).
2. Introducing required default agents (`writer` for content/editorial drafting and `planner` for strategic project decomposition) to complete the multi-agent roster.
3. Making all agent prompts domain-agnostic and strictly goal-aligned, preventing agents from injecting unsolicited secondary agendas or persona-specific biases (e.g., unsolicited Big-O lectures, unrequested changelogs/release notes, unprompted security tables, or intrusive financial metrics).
4. Instructing the orchestrator to leverage non-agent blocks (`python_code`, `artifact`, `condition`) whenever deterministic computations, data formatting, or quality gates can eliminate unnecessary, slow, and expensive LLM agent calls.

## Scope

### In scope:
- **Fresh Internet Information Detection & Automated Researcher Routing**:
  - Semantic and temporal cue recognition ("today", "yesterday", "current", "latest", "now", "recent", "weather", "scores", "prices", "news", "2025/2026", "who is the current", "what happened to").
  - Automated selection of `researcher` agent using Perplexity Sonar (`sonar`) for live web discovery.
- **On-the-Fly Workflow Planning & Execution**:
  - Ensuring the Swarm Orchestrator actively plans execution (1-agent or multi-step DAG) when no specific specialist is explicitly selected in chat.
  - Pipelining step outputs cleanly and concluding composite workflows with goal-aligned synthesis.
- **Non-Agent Block Optimization**:
  - Incorporating `python_code` blocks for deterministic math, statistical calculations, and string transformations instead of burning LLM inference tokens.
  - Incorporating `artifact` blocks for assembling and saving structured file/report deliverables directly from template interpolation without extra LLM overhead.
  - Incorporating `condition` blocks for validation and branching gates.
  - Updating orchestrator system instructions and AI workflow generator directives to enforce non-agent block optimization across all workflow designs.
- **New Default Agents**:
  - `writer`: Content, editorial, and copywriting specialist for articles, essays, documentation, and communications.
  - `planner`: Strategic roadmap, task decomposition, and milestone sequencing specialist.
  - Full modular packages (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`) dynamically loaded by `agent_registry`.
- **Goal-Agnostic Agent Prompt Alignment**:
  - Auditing and updating all agent `prompt.md` files (`orchestrator`, `researcher`, `coder`, `reviewer`, `data_analyst`, `synthesizer`, `file_creator`, `file_parser`, `general_assistant`, `writer`, `planner`).
  - Enforcing strict adherence to the assigned task and workflow goal without personal "flavour" or unsolicited secondary tasks.
- **Frontend Roster Integration**:
  - Distinct icons, badges, and color themes for `writer` and `planner` across `AgentCard`, `LiveExecutionConsole`, `GranularStepTrace`, and `AgentDetailsModal`.
- **Automated Tests**:
  - New test cases in `backend/test_endpoints.py` verifying fresh internet detection, non-agent block execution, goal-agnostic prompt adherence, and new default agents.

### Out of scope:
- Modifying the underlying database schema in Supabase (the existing JSON step/run structures fully accommodate all block types and agent profiles).
- Replacing external LLM provider SDKs (Groq, Gemini, and Perplexity Sonar are preserved).

## Current behavior

- **Chat Routing Short-Circuiting**: In `backend/app/main.py`, `route_agent` uses rigid keyword regexes that intercept queries with words like "code", "data", "csv", "file", "review" and route them directly to a single agent for a 1-turn completion, bypassing the Swarm Orchestrator's on-the-fly workflow planning completely.
- **Failure to Trigger Researcher for Fresh Information**: Queries asking for live, real-time, or fresh internet facts (e.g. "What is today's weather in Tokyo?", "Who won the game last night?", "Did SpaceX launch Starship?", "What happened to SVB?") miss the narrow `research_keywords` in `route_agent` and `has_search` in `synthesize_on_the_fly_workflow`, falling back to `general_assistant` which lacks internet access and hallucinates or uses outdated knowledge.
- **Agent Prompts Adding Persona "Flavour"**:
  - `synthesizer` forces "concise change logs and release notes" and terminology reconciliation even on general non-software questions.
  - `coder` forces Big-O algorithmic complexity lectures and boilerplate tests even for simple one-line functions.
  - `reviewer` generates alarmist OWASP tables with [Critical] tags even for trivial scripts.
  - `data_analyst` forces complex statistical tests (Pearson correlation, IQR, Z-scores) even for basic math or general tables.
- **Orchestrator Ignores Non-Agent Blocks**: In `synthesize_on_the_fly_workflow`, 100% of generated steps have `"step_type": "agent"`. Deterministic math (such as compound interest) triggers two full LLM agent calls (`data_analyst` $\to$ `synthesizer`) rather than a 1-millisecond `python_code` block.
- **Missing Default Agent Roles**: Users requesting creative articles, blog posts, essays, or strategic roadmaps are awkwardly routed to `synthesizer` or `general_assistant`.

## Proposed behavior

1. **Intelligent Fresh Internet Detection & Automated Researcher Routing**:
   - Any query requiring real-time, current, time-sensitive, or web-grounded information is automatically routed to `researcher` using `sonar` (Perplexity Sonar) for live citations and authoritative sources.
2. **Orchestrator-First Chat Planning**:
   - When a user enters a query in the chat window without targeting a specific agent, the Swarm Orchestrator evaluates the query complexity and plans an on-the-fly workflow (single-agent or multi-step DAG) with real-time SSE streaming and granular inspection.
3. **Non-Agent Block Optimization**:
   - Deterministic calculations, math formulas, and string transformations are delegated to `python_code` blocks (0 tokens, millisecond execution).
   - Structured document formatting and report assembly are delegated to `artifact` blocks where possible.
   - Orchestrator instructions explicitly enforce this principle.
4. **New Default Agents**:
   - `writer` (Content & Editorial Specialist) for articles, copy, essays, and communication.
   - `planner` (Strategic Planning & Decomposition Agent) for roadmaps, milestones, and project phasing.
5. **Goal-Agnostic, Strict Adherence Prompts**:
   - Every agent prompt adheres to the user's explicit objective, constraints, and format requirements without inventing unprompted secondary tasks or persona-specific tangents.

## Implementation steps

1. **Step 1: System Prompts Overhaul (Goal-Agnostic Alignment)**
   - Update `backend/app/agents/*/prompt.md` across all agents to eliminate unsolicited persona flavor and enforce strict goal adherence.
2. **Step 2: Add Required Default Agents (`writer` and `planner`)**
   - Create `backend/app/agents/writer/` (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`).
   - Create `backend/app/agents/planner/` (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`).
3. **Step 3: Enhance On-The-Fly Workflow Orchestration & Non-Agent Block Optimization**
   - In `backend/app/ai_generator.py`:
     - Expand fresh internet information detection to automatically assign `researcher` with `model: "sonar"`.
     - Implement non-agent block patterns (`python_code`, `artifact`, `condition`) in `synthesize_on_the_fly_workflow`.
     - Update `generate_workflow_spec` system prompt to mandate non-agent block optimization and goal-aligned synthesis.
   - In `backend/app/main.py`:
     - Ensure chat queries without explicit agent target route directly into on-the-fly workflow orchestration.
     - Update `route_agent` to recognize fresh information queries and new agent roles.
4. **Step 4: Frontend Visual Integration**
   - Update `AgentCard.tsx`, `GranularStepTrace.tsx`, `LiveExecutionConsole.tsx`, and `AgentDetailsModal.tsx` to support `writer` and `planner`.
5. **Step 5: Automated Verification & Documentation**
   - Add Tests 78–82 in `backend/test_endpoints.py`.
   - Run the full test suite and verify all tests pass.
   - Create `implementation.md`, `verification.md`, and `qa-checklist.md`.
   - Create `docs/decisions/on-the-fly-orchestration-and-agent-prompt-alignment/decisions.md`.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/agents/orchestrator/prompt.md` | Overhaul prompt: agent roster, fresh internet detection, non-agent block optimization, goal-agnostic principles | Instruct orchestrator on complete agent roster and non-agent blocks |
| `backend/app/agents/researcher/prompt.md` | Make prompt goal-agnostic and focused on cited real-time findings | Prevent unsolicited historical cross-examinations |
| `backend/app/agents/coder/prompt.md` | Make prompt goal-agnostic; eliminate mandatory Big-O lectures | Keep code answers clean and directly aligned to request |
| `backend/app/agents/reviewer/prompt.md` | Make prompt goal-agnostic; calibrate critique to request scope | Prevent alarmist vulnerability tables for simple code |
| `backend/app/agents/data_analyst/prompt.md` | Make prompt goal-agnostic; ensure general numerical flexibility | Prevent overcomplicated statistical tests and finance mandates |
| `backend/app/agents/synthesizer/prompt.md` | Make prompt goal-agnostic; remove mandatory changelogs/release notes | Consolidate strictly in service of the user's explicit goal |
| `backend/app/agents/file_creator/prompt.md` | Make prompt goal-agnostic | Deliver clean file artifacts without meta commentary |
| `backend/app/agents/file_parser/prompt.md` | Make prompt goal-agnostic | Deliver grounded document context |
| `backend/app/agents/general_assistant/prompt.md` | Make prompt goal-agnostic | Deliver direct, helpful answers without boilerplate |
| `backend/app/agents/writer/` | New agent package (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`) | Editorial, content, and copywriting specialist |
| `backend/app/agents/planner/` | New agent package (`config.json`, `prompt.md`, `tools.py`, `skills.json`, `mcp.json`) | Strategic planning and task decomposition specialist |
| `backend/app/ai_generator.py` | Overhaul `synthesize_on_the_fly_workflow` & `generate_workflow_spec` | Fresh internet detection with Sonar, non-agent block optimization, goal-agnostic synthesis |
| `backend/app/main.py` | Update `route_agent` and `_execute_chat_turn` | Route un-targeted chat queries through orchestrator workflow engine |
| `frontend/src/app/agents/components/AgentCard.tsx` | Add icons and badges for `writer` and `planner` | Visual consistency in Agents page |
| `frontend/src/app/chat/components/GranularStepTrace.tsx` | Add badge colors for `writer` and `planner` | Visual consistency in granular traces |
| `frontend/src/app/chat/components/LiveExecutionConsole.tsx` | Add badge colors for `writer` and `planner` | Visual consistency during live execution |
| `frontend/src/app/chat/components/AgentDetailsModal.tsx` | Add sample arguments and execution support for new agents | Interactive testing in modal |
| `backend/test_endpoints.py` | Add Tests 78–82 | Verify fresh internet info routing, non-agent blocks, goal-agnostic prompts, and new agents |

## Interfaces

- **Workflow Step Non-Agent Schema (`WorkflowStep`)**:
  - `python_code` block: `{"step_type": "python_code", "code": "def execute(inputs, previous_outputs, context): ..."}`
  - `artifact` block: `{"step_type": "artifact", "artifact_title": "...", "artifact_type": "markdown", "instructions": "..."}`
  - `condition` block: `{"step_type": "condition", "condition_expr": "...", "true_target_step_id": "...", "false_target_step_id": "..."}`
- **New Agent Identifiers**:
  - `writer`: Role `Content & Editorial Specialist`, Model `qwen-3.8` (Groq), Icon `pen-tool`.
  - `planner`: Role `Strategic Planning & Decomposition Specialist`, Model `qwen-3.8` (Groq), Icon `calendar`.
- **Perplexity Sonar Web Research Directive**:
  - When query matches fresh internet information criteria, step model is set to `sonar` and agent ID is `researcher`.

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Existing tests expecting specific agent count (9) | Test failures | Update health and agents endpoints assertions to reflect 11 default agents gracefully |
| Existing tests expecting specific 3-step agent DAGs in Test 70/77 | Regressions in existing tests | Preserve backwards compatibility for tested prompt patterns while adding optimized non-agent paths for calculations and fresh search |
| Sandboxed Python script execution security | Security risk in code blocks | All `python_code` blocks execute through `execute_tool_script` using AST verification and strict `__builtins__` containment |

## Verification

- Automated Tests:
  - Run full test suite: `backend\venv\Scripts\python backend/test_endpoints.py`.
  - Verify new tests:
    - Test 78: Fresh internet information detection automatically designates `researcher` with `sonar`.
    - Test 79: Non-agent blocks (`python_code`, `artifact`) executed within on-the-fly workflows for optimization.
    - Test 80: Goal-agnostic agent prompts verified across all agents without unsolicited flavor.
    - Test 81: New default agents `writer` and `planner` discovered, listed, and executable.
    - Test 82: End-to-end chat orchestration with on-the-fly workflow and live progress streaming.
- Manual Checks:
  - Ask "What is the current weather in Tokyo?" in chat and verify live execution console shows `researcher` (Perplexity Sonar).
  - Ask "Calculate the compound interest for $10,000 at 5% over 10 years" and verify execution uses `python_code` block without hallucination.
  - Ask "Write a blog post about renewable energy" and verify `writer` agent is engaged.
  - Verify `npm --prefix frontend run build` completes with 0 errors.

## Rollout

- In-place update to backend agent definitions and synthesis engine.
- Backward compatible with existing session history, custom agents, and workflows.
- No database migrations needed.
