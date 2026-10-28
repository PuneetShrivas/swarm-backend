# QA Checklist: Advanced Workflow Blocks, DAG Edge Snapping, Expandable Nodes, Real Web Search, Perplexity API & Base Conversational Agent

*Created: 2026-10-28T20:58:00+05:30*  
*Status: Pending Sign-Off*

## Quality Assurance Checklist

### 1. Workflow Blocks Architecture
- [ ] Condition block correctly evaluates boolean expressions and directs flow to True/False targets.
- [ ] Python code block executes inline Python scripts in a safe sandbox, capturing stdout and structured outputs.
- [ ] Loop block loops back to the target step when the condition is true and respects `max_loop_iterations`.
- [ ] Artifact block outputs structured markdown/code files and stores them in workflow run artifacts.
- [ ] Step unit test modal can test Condition, Python, Loop, and Artifact blocks in isolation.

### 2. Interactive DAG Editor
- [ ] Blocks snap connections to the nearest edge (Top, Bottom, Left, Right) dynamically rather than static top/bottom.
- [ ] Clicking any block expands it inline to reveal its full editor controls.
- [ ] Clicking an expanded block collapses it back to compact badge form.
- [ ] Block Palette allows adding Condition, Python, Loop, Artifact, and Agent blocks directly.

### 3. Agent Capabilities & Real Search
- [ ] Researcher agent executes real web searches with live titles, snippets, and source URLs.
- [ ] Perplexity API is supported via `PERPLEXITY_API_KEY` with citations.
- [ ] `general_assistant` agent is available for casual conversational chat.
- [ ] Users can select specific models (`gemini-2.5-flash`, `gemini-2.5-pro`, `sonar`, `sonar-pro`) per agent.

### 4. Build & Regression
- [ ] All backend tests in `backend/test_endpoints.py` pass.
- [ ] `npm --prefix frontend run lint` passes with 0 errors and 0 warnings.
- [ ] `npm --prefix frontend run build` completes successfully.
