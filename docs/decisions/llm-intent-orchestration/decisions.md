# Architecture Decision: LLM-Driven Intent Analysis & Semantic Orchestration

**Slug**: `llm-intent-orchestration`  
**Date**: `2026-11-02T17:49:00+05:30`  
**Status**: PROPOSED  

---

## Context
The Swarm Orchestrator previously relied on sequential heuristic matching across 15+ `if any(k in prompt_lower for k in [...])` blocks in `backend/app/ai_generator.py`. This led to:
1. **False Positives / Substring Collisions**: Words like `"download"` inadvertently matching `"dow"` (Dow Jones index), or `"stockpile"` matching `"stock"`.
2. **Greedy Priority Inversion**: Whichever check appeared earliest in the file hijacked queries that belonged to more specialized agents.
3. **Semantic Inflexibility**: Nuanced or colloquial requests without predefined keywords fell through to generic fallbacks.

## Decision
1. **Single-Pass Structured LLM Intent Evaluation**:
   Replace the sequential substring decision tree with a dedicated, low-latency LLM evaluation function (`analyze_query_intent`) using Groq LPU / Gemini Flash.
   The LLM classifies the query across orthogonal dimensions in a single inference turn:
   - Primary intent category (`spreadsheet_operations`, `document_authoring`, `artifact_report`, `code_engineering`, `strategic_planning`, `market_intelligence`, `live_web_research`, `data_analytics`, `document_parsing`, `conversational_greeting`, `general_inquiry`).
   - Need for fresh internet information (`requires_live_web_search`).
   - Deliverable export requirement and format (`file_export_requested`, `export_format`).
2. **Declarative Pipeline Dispatcher**:
   Replace procedural `if` blocks with a declarative mapping table / pipeline factory function `build_workflow_from_intent`.
3. **Deterministic Fallback Layer**:
   Maintain a non-blocking fallback classifier and query cache to guarantee zero downtime and minimal latency even during external LLM outages.

## Consequences
- **Positive**:
  - Eliminates all keyword collision and substring matching issues permanently.
  - Understands natural language nuance, metaphors, and complex multi-part goals.
  - Modular, maintainable architecture where adding a new agent or capability only requires updating the intent enum and pipeline factory.
- **Negative / Mitigations**:
  - Small latency overhead (150-300ms) on cold queries: Mitigated by ultra-fast Groq LPU inference and LRU caching for repeated requests.
  - Dependence on LLM JSON output: Mitigated by strict JSON schema mode, sanitization, and deterministic fallback.
