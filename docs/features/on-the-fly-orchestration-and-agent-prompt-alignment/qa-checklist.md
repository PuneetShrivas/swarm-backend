# QA Checklist: On-the-Fly Workflow Orchestration & Goal-Agnostic Agent Prompt Alignment

**Datetime:** 2026-11-02T12:29:00+05:30  
**Status:** In Planning / Awaiting Plan Approval

## Manual QA Verification Steps

- [ ] **Fresh Internet Search in Chat**:
  - Open Chat window with Orchestrator (Auto).
  - Type: "What is today's weather in Tokyo?"
  - Verify live execution console shows `researcher` agent running with Perplexity Sonar and returns fresh web citations.
- [ ] **Mathematical Calculation with Non-Agent Block**:
  - Type: "Calculate compound interest for $10,000 at 5% annually for 10 years"
  - Verify granular trace displays `python_code` non-agent block execution with 0 tokens and instant latency.
- [ ] **Content Writing Query**:
  - Type: "Write an introductory blog post explaining quantum computing for high school students"
  - Verify `writer` agent is engaged and generates clear editorial copy adhering strictly to the topic without unsolicited technical boilerplate.
- [ ] **Strategic Roadmap Query**:
  - Type: "Create a 3-phase launch plan for a SaaS product"
  - Verify `planner` agent produces milestones, dependencies, and timelines without personal bias.
- [ ] **Goal-Agnostic Response Verification**:
  - Ask for a simple Python script (e.g. "Write a function to check if a string is a palindrome").
  - Verify Coder outputs clean code without unrequested Big-O complexity essays or boilerplate unit test suites.
  - Ask for a summary of a general topic (e.g. "Summarize the history of coffee").
  - Verify Synthesizer delivers a clean summary without unrequested changelogs, release notes, or software versioning metadata.
- [ ] **Agents Page Verification**:
  - Navigate to `/agents` in browser.
  - Verify all 11 default agents are listed with their respective icons, tools, and skills.
- [ ] **Build Integrity**:
  - Frontend build completes cleanly: `npm --prefix frontend run build`.
  - Backend test suite completes cleanly with 82/82 tests passing: `backend\venv\Scripts\python backend/test_endpoints.py`.
