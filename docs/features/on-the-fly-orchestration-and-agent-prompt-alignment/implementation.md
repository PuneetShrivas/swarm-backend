# Implementation: On-the-Fly Workflow Orchestration & Goal-Agnostic Agent Prompt Alignment

**Datetime:** 2026-11-02T12:27:00+05:30  
**Status:** In Planning / Awaiting Plan Approval

## Overview

This document tracks the technical implementation tasks for fixing on-the-fly workflow orchestration in the chat window, introducing required default agents (`writer`, `planner`), aligning agent prompts to be goal-agnostic, and leveraging non-agent blocks (`python_code`, `artifact`, `condition`) for execution optimization.

## Implementation Phases

### Phase 1: Goal-Agnostic System Prompts Overhaul
- [ ] Audit and rewrite `backend/app/agents/orchestrator/prompt.md` to reflect full agent roster, fresh internet detection, non-agent block optimization principles, and goal-first discipline.
- [ ] Rewrite `backend/app/agents/researcher/prompt.md` to deliver factual, cited findings without unsolicited philosophizing.
- [ ] Rewrite `backend/app/agents/coder/prompt.md` to deliver clean code strictly aligned to the user's task without mandatory Big-O lectures.
- [ ] Rewrite `backend/app/agents/reviewer/prompt.md` to provide scoped, constructive reviews without alarmist vulnerability tables.
- [ ] Rewrite `backend/app/agents/data_analyst/prompt.md` to provide universal numerical and tabular analysis across all domains without finance bias or forced statistical tests.
- [ ] Rewrite `backend/app/agents/synthesizer/prompt.md` to consolidate answers directly fulfilling the user's goal without unrequested changelogs or release notes.
- [ ] Rewrite `backend/app/agents/file_creator/prompt.md`, `file_parser/prompt.md`, `general_assistant/prompt.md` to eliminate meta-commentary and focus on goal execution.

### Phase 2: Add New Default Agents (`writer` and `planner`)
- [ ] Create `backend/app/agents/writer/`:
  - `config.json`: ID `writer`, icon `pen-tool`, model `qwen-3.8`.
  - `prompt.md`: Editorial, essay, article, and content drafting.
  - `tools.py`: Readability analysis, outline generator, text formatter.
  - `skills.json`: Content generation skills.
  - `mcp.json`: Standard MCP configuration.
- [ ] Create `backend/app/agents/planner/`:
  - `config.json`: ID `planner`, icon `calendar`, model `qwen-3.8`.
  - `prompt.md`: Strategic planning, roadmap design, milestone sequencing.
  - `tools.py`: Milestone generator, dependency checker, timeline formatter.
  - `skills.json`: Strategic planning skills.
  - `mcp.json`: Standard MCP configuration.

### Phase 3: Enhance On-the-Fly Orchestration & Non-Agent Block Optimization
- [ ] In `backend/app/ai_generator.py`:
  - Add comprehensive fresh internet information detection with automatic assignment of `researcher` (`sonar`).
  - Add non-agent block optimization (`python_code` for math/transformations, `artifact` for file deliverables).
  - Update `generate_workflow_spec` system instruction with non-agent block directives.
- [ ] In `backend/app/main.py`:
  - Direct chat queries without targeted agent to orchestrator workflow synthesis.
  - Update `route_agent` heuristics to include fresh internet search and new agents.

### Phase 4: Frontend UI Updates
- [ ] Update `AgentCard.tsx` with icons for `writer` and `planner`.
- [ ] Update `LiveExecutionConsole.tsx` with badge colors for new agents.
- [ ] Update `GranularStepTrace.tsx` with badge colors for new agents.
- [ ] Update `AgentDetailsModal.tsx` with tool/skill execution support for new agents.

### Phase 5: Verification & Testing
- [ ] Add Tests 78–82 in `backend/test_endpoints.py`.
- [ ] Run full backend test suite (`python backend/test_endpoints.py`).
- [ ] Run frontend build (`npm --prefix frontend run build`).

---

## Step Execution Progress

### Step 1: Goal-Agnostic System Prompts Overhaul
- **Datetime:** 2026-11-02T12:28:30+05:30
- **Status:** Completed
- **Files Changed:**
  - `backend/app/agents/orchestrator/prompt.md`: Updated to include full 11-agent roster, fresh internet detection directive, non-agent block optimization principle, and goal-first discipline.
  - `backend/app/agents/researcher/prompt.md`: Made goal-agnostic and focused on cited real-time findings; removed unsolicited historical retrospectives.
  - `backend/app/agents/coder/prompt.md`: Made goal-agnostic; removed mandatory Big-O complexity essays and unrequested boilerplate test suites.
  - `backend/app/agents/reviewer/prompt.md`: Made goal-agnostic; calibrated feedback to request scope and removed forced alarmist OWASP tables for simple code.
  - `backend/app/agents/data_analyst/prompt.md`: Made goal-agnostic; enforced universal neutrality across domains and eliminated forced inferential tests for simple calculations.
  - `backend/app/agents/synthesizer/prompt.md`: Made goal-agnostic; removed unsolicited changelog/release notes mandates and self-referential commentary.
  - `backend/app/agents/file_creator/prompt.md`, `file_parser/prompt.md`, `general_assistant/prompt.md`: Stripped meta-commentary and focused on direct goal execution.
- **Reason:** Prevent swarm agents from injecting persona-specific tangents, secondary agendas, or unsolicited boilerplate into user workflow results.
- **Tests Added/Updated:** Checked agent loading via `agent_registry.reload()`.
- **Commands Run:**
  - `backend\venv\Scripts\python -c "import sys; sys.path.insert(0, 'backend'); from app.agents.registry import agent_registry; agent_registry.reload(); print('Loaded', len(agent_registry.get_all()), 'agents')"`
- **Result:** Loaded 9 agents cleanly with updated goal-agnostic instructions.

### Step 2: Add Required Default Agents (`writer` and `planner`)
- **Datetime:** 2026-11-02T12:35:00+05:30
- **Status:** Completed
- **Files Changed:**
  - `backend/app/agents/writer/config.json`: New agent configuration with ID `writer`, role `Content, Editorial & Copywriting Specialist`, model `qwen-3.8`, icon `pen-tool`.
  - `backend/app/agents/writer/prompt.md`: Goal-agnostic system prompt for article drafting, essays, newsletters, copy, and editorial communication.
  - `backend/app/agents/writer/tools.py`: Python tools (`analyze_readability`, `generate_article_outline`, `format_editorial_copy`).
  - `backend/app/agents/writer/skills.json`: Semantic triggers for content drafting, copywriting, editorial polishing, and readability analysis.
  - `backend/app/agents/writer/mcp.json`: Standard MCP configuration.
  - `backend/app/agents/planner/config.json`: New agent configuration with ID `planner`, role `Strategic Planning & Task Decomposition Specialist`, model `qwen-3.8`, icon `calendar`.
  - `backend/app/agents/planner/prompt.md`: Goal-agnostic system prompt for roadmaps, milestone planning, and task decomposition.
  - `backend/app/agents/planner/tools.py`: Python tools (`generate_milestone_plan`, `calculate_critical_path`, `estimate_sprint_allocation`).
  - `backend/app/agents/planner/skills.json`: Semantic triggers for strategic roadmapping, task decomposition, dependency sequencing, and sprint planning.
  - `backend/app/agents/planner/mcp.json`: Standard MCP configuration.
- **Reason:** Fulfill user requirement (a) to provide missing default agents for creative/editorial writing and strategic planning.
- **Tests Added/Updated:** Verified dynamic discovery of 11 default agents in `agent_registry` and tool execution for `writer` and `planner`.
- **Commands Run:**
  - `backend\venv\Scripts\python -c "import sys; sys.path.insert(0, 'backend'); from app.agents.registry import agent_registry; agent_registry.reload(); agents = agent_registry.get_all(); print('Loaded', len(agents), 'agents:', [a.id for a in agents])"`
  - `backend\venv\Scripts\python -c "import sys; sys.path.insert(0, 'backend'); from app.agents.registry import agent_registry; agent_registry.reload(); w = agent_registry.get('writer'); print('Writer tool res:', w.execute_tool('analyze_readability', {'text': 'This is a clean and concise sentence.'})); p = agent_registry.get('planner'); print('Planner tool res:', p.execute_tool('generate_milestone_plan', {'goal': 'Launch SaaS platform'}))"`
- **Result:** Successfully registered and verified both agents; active default agent count is now 11.

### Step 3: Enhance On-The-Fly Workflow Orchestration & Non-Agent Block Optimization
- **Datetime:** 2026-11-02T12:44:30+05:30
- **Status:** Completed
- **Files Changed:**
  - `backend/app/ai_generator.py`:
    - Added `requires_fresh_internet_information` to detect real-time, current, live, or time-sensitive queries (weather, sports scores, live stock quotes, breaking news, recency indicators).
    - Updated `synthesize_on_the_fly_workflow` to automatically route fresh internet queries to `researcher` with `model: "sonar"` (Perplexity Sonar).
    - Added non-agent block optimization pattern using `python_code` for deterministic computations with 0 tokens and sub-millisecond execution.
    - Added workflow pipelines for `writer` and `planner`.
    - Updated `generate_workflow_spec` system instruction to include full 11-agent roster, fresh internet detection directive, and block optimization directive.
  - `backend/app/main.py`:
    - Updated `route_agent` to evaluate orchestrator multi-agent keywords first, followed by `writer`, `planner`, and expanded `research_keywords` covering fresh internet and real-time topics.
- **Reason:** Automatically engage the research agent for fresh web information and use non-agent blocks (`python_code`) to optimize execution speed and cost.
- **Tests Added/Updated:** Verified `requires_fresh_internet_information` and end-to-end execution of a 2-step `python_code` on-the-fly workflow.
- **Commands Run:**
  - `backend\venv\Scripts\python -c "... synthesize_on_the_fly_workflow tests ..."`
  - `backend\venv\Scripts\python -c "... WorkflowExecutionEngine.execute_workflow ..."`
- **Result:** Fresh internet detection returns `True` and routes to `researcher` (`sonar`); non-agent `python_code` executes in sandbox with 0 tokens.



