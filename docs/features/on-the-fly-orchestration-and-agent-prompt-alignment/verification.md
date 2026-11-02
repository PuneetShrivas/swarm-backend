# Verification: On-the-Fly Workflow Orchestration & Goal-Agnostic Agent Prompt Alignment

**Datetime:** 2026-11-02T12:28:00+05:30  
**Status:** In Planning / Awaiting Plan Approval

## Planned Verification Suite

| Test ID | Area | Verification Description | Expected Result |
| ------- | ---- | ------------------------ | --------------- |
| Test 78 | Fresh Internet Information | Submit queries with fresh information cues ("weather today", "latest score", "recent news", "current price") | Automatically designates `researcher` agent with model `sonar` (Perplexity Sonar) |
| Test 79 | Non-Agent Block Optimization | Submit deterministic calculation / transformation queries | Employs `python_code` or `artifact` blocks to optimize agent calls with 0 LLM tokens |
| Test 80 | Goal-Agnostic Prompts | Verify agent prompts across all default agents | Prompts focus strictly on the user goal without unsolicited persona-specific tangents |
| Test 81 | New Default Agents | Query agent registry for `writer` and `planner` | Both agents discovered, listed with valid configurations, tools, and skills |
| Test 82 | E2E Chat Orchestration | Execute chat turn with on-the-fly workflow | Workflow executes ephemerally, emits granular milestones, and returns complete answer |

## Commands to Run

```bash
# Backend Automated Tests
backend\venv\Scripts\python backend/test_endpoints.py

# Frontend Build
npm --prefix frontend run build
```
