# Feature Plan: LLM-Driven Intent Analysis & Semantic Orchestration

**Slug**: `llm-intent-orchestration`  
**Created At**: `2026-11-02T17:49:00+05:30`  
**Status**: Complete  

---

## Goal
Replace the legacy substring-matching and keyword-based decision tree in the swarm orchestrator (`synthesize_on_the_fly_workflow` and `requires_fresh_internet_information`) with a single-pass, structured LLM-based intent analysis engine. The new engine evaluates user queries holistically to classify intent, determine real-time search necessity, detect file export requirements, and assemble optimal multi-agent pipelines in a single semantic pass without brittle regex or keyword heuristics.

---

## Scope

### In Scope
1. **Single-Pass LLM Intent Analyzer (`analyze_query_intent`)**:
   - Fast, structured LLM prompt (using low-latency inference: Groq fast model or Gemini Flash) returning a strictly validated JSON schema.
   - Comprehensive intent classification (`spreadsheet_operations`, `document_authoring`, `artifact_report`, `code_engineering`, `strategic_planning`, `market_intelligence`, `live_web_research`, `data_analytics`, `document_parsing`, `conversational_greeting`, `general_inquiry`).
   - Unified dimensional analysis: `requires_live_web_search` (boolean), `file_export_requested` (boolean), `export_format` (enum: `md`, `xlsx`, `csv`, `pdf`, `pptx`, `py`, `json`, etc.), `recommended_pipeline` (agent sequence).
2. **Declarative Pipeline Dispatcher**:
   - Replace the 15+ sequential substring `if/elif` blocks in `synthesize_on_the_fly_workflow` with a clean, declarative pipeline factory mapping evaluated intent objects directly to DAG specifications.
3. **Resilience & Offline Fallback**:
   - Intelligent fallback classifier if the LLM provider encounters rate limits or network latency, ensuring zero downtime.
   - In-memory LRU caching for recurring query patterns to ensure near-zero latency for repeated queries.
4. **Verification & Regression Testing**:
   - Automated test suite validating classification accuracy across all 11 intent domains, compound intents (e.g. poetry + markdown download, stock research + Excel export), and conversational greetings.
   - Zero regression across existing test suites (`test_orchestration_query_routing.py`, `test_excel_specialist.py`, `test_aggressive_researcher_orchestration.py`).

### Out of Scope
- Modifying underlying agent packages or agent tool definitions.
- Changing frontend chat UI layout or messaging protocol (intent analysis occurs entirely server-side within the orchestrator).
- Modifying the DAG workflow execution engine (`backend/app/workflows/engine.py`).

---

## Current Behavior
Currently in [`backend/app/ai_generator.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/ai_generator.py):
- `synthesize_on_the_fly_workflow` executes 15+ sequential `if` blocks with hundreds of hardcoded substring checks:
  - `has_artifact_command`, `has_pdf_or_doc`, `has_report_request` (lines 663-672)
  - `has_excel_specialist` (lines 748-757)
  - `has_code_keywords` (lines 861-870)
  - `has_writing`, `has_doc_file_export` (lines 921-935)
  - `has_planning` (lines 1007-1011)
  - `has_market_kw` (lines 1114-1126)
  - `has_data_kw`, `has_file_kw` (lines 1279-1281)
  - `has_deep_kw` (lines 1448-1452)
  - `has_file_gen` (lines 1492-1497)
  - `has_coding` (lines 1597-1601)
  - `has_search`, `is_fresh` (lines 1651-1657)
  - `has_math` (lines 1799-1803)
  - `has_parse` (lines 1841-1844)
  - `is_trivial_greeting` (lines 1894-1898)
- `requires_fresh_internet_information` (lines 555-620) uses lists of search intents, temporal cues, and topic names.
- This results in:
  - Brittle keyword collisions (e.g., words like "download" inadvertently triggering "dow" or "stockpile" triggering "stock").
  - Semantic blindness (indirect queries like "compose a piece honoring the sunset" fail to trigger writer/document authoring).
  - High maintenance overhead for every new agent or specialized workflow.

---

## Proposed Behavior
1. When a user message arrives in [`_execute_chat_turn`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/main.py#L1380), the orchestrator calls `analyze_query_intent(prompt, attached_artifacts)`.
2. A single, ultra-fast LLM call (utilizing low-latency Groq LPU or Gemini Flash with structured JSON schema) analyzes the prompt holistically and returns:
   ```json
   {
     "primary_intent": "document_authoring",
     "requires_live_web_search": false,
     "file_export_requested": true,
     "export_format": "md",
     "complexity": "multi_step",
     "pipeline_name": "Document Authoring & Downloadable Markdown Synthesis Pipeline",
     "agent_sequence": ["writer", "file_creator", "synthesizer"],
     "step_directives": [
       {"agent_id": "writer", "name": "Creative & Instructional Content Authoring", "instructions": "..."},
       {"agent_id": "file_creator", "name": "Downloadable Markdown File Compilation", "instructions": "..."},
       {"agent_id": "synthesizer", "name": "Executive Overview & File Delivery", "instructions": "..."}
     ]
   }
   ```
3. `synthesize_on_the_fly_workflow` receives this structured intent object and dispatches to the declarative workflow builder.
4. If an LLM call fails or times out, a lightweight token-boundary fallback handles the dispatch safely without disruption.

---

## Implementation Steps

### Phase 1: Intent Schema & Core Analyzer (`backend/app/ai_generator.py`)
1. Define the Pydantic data model and JSON schema for `QueryIntentClassification`:
   - `primary_intent`: Literal enum of all supported domains.
   - `requires_live_web_search`: bool.
   - `file_export_requested`: bool.
   - `export_format`: Optional[str].
   - `recommended_agents`: List[str].
   - `workflow_title`: str.
   - `workflow_description`: str.
2. Implement `analyze_query_intent(prompt: str, attached_artifacts: Optional[List[Dict[str, Any]]] = None) -> QueryIntentClassification`:
   - Prompts Groq (Qwen/Llama) or Gemini Flash with a concise system prompt and structured JSON schema.
   - Employs an in-memory LRU cache (`@functools.lru_cache` or dict cache) for instant responses on identical queries.
   - Implements a graceful fallback parser in case of API timeouts.

### Phase 2: Declarative Pipeline Factory (`backend/app/ai_generator.py`)
1. Build a clean, modular factory function: `build_workflow_from_intent(intent: QueryIntentClassification, prompt_clean: str, attached_artifacts: List[Dict[str, Any]]) -> Dict[str, Any]`.
2. Map each intent type cleanly to its canonical multi-agent pipeline:
   - `spreadsheet_operations`: `excel_specialist` (+ `researcher` if live data needed) -> `synthesizer`.
   - `document_authoring`: `writer` -> (`file_creator` if `file_export_requested`) -> `synthesizer`.
   - `artifact_report`: `file_parser` / `researcher` -> `writer` -> `synthesizer`.
   - `code_engineering`: `coder` -> `reviewer` -> `synthesizer`.
   - `strategic_planning`: `planner` -> `synthesizer`.
   - `market_intelligence`: `researcher` (Sonar) -> `data_analyst` -> (`file_creator` / `synthesizer`).
   - `live_web_research`: `researcher` (Sonar) -> `synthesizer` / `data_analyst`.
   - `data_analytics`: `data_analyst` -> (`file_creator`) -> `synthesizer`.
   - `document_parsing`: `file_parser` -> `data_analyst` -> `synthesizer`.
   - `conversational_greeting`: `general_assistant` (1-step).
   - `general_inquiry`: `general_assistant` -> `synthesizer`.
3. Refactor `synthesize_on_the_fly_workflow` to call `analyze_query_intent` and dispatch through `build_workflow_from_intent`.
4. Replace `requires_fresh_internet_information(prompt)` with the LLM-evaluated `intent.requires_live_web_search`.

### Phase 3: Integration with Main Chat Turn (`backend/app/main.py`)
1. Ensure `_execute_chat_turn` passes the evaluated intent to workflow execution metadata so the frontend execution trace displays the LLM's classified intent and rationale.
2. Verify that artifact extraction continues to work seamlessly with the LLM-identified `export_format`.

### Phase 4: Automated Testing & Verification
1. Create `backend/test_llm_intent_orchestration.py`:
   - Test intent classification across diverse user prompts (instructional poem with markdown download, Excel joins and cell edits, stock performance with spreadsheet, Python script generation, casual greetings, live news queries).
   - Test LLM fallback behavior when client is mocked or simulated offline.
   - Verify zero substring keyword matching regressions.
2. Run full regression suite:
   - `backend/test_orchestration_query_routing.py`
   - `backend/test_excel_specialist.py`
   - `backend/test_aggressive_researcher_orchestration.py`
   - `npm --prefix frontend run build`

---

## Files to Change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/ai_generator.py` | Add `analyze_query_intent`, `build_workflow_from_intent`, and refactor `synthesize_on_the_fly_workflow`. | Replace 15+ hardcoded keyword `if` blocks with holistic, single-pass LLM intent evaluation. |
| `backend/app/main.py` | Connect LLM intent metadata to chat turn execution trace. | Provide visibility into the LLM's classification rationale in the trace logs. |
| `backend/test_llm_intent_orchestration.py` | New comprehensive test suite for LLM intent analysis and declarative pipeline dispatching. | Verify accuracy across all intent domains and fallback resilience. |
| `docs/features/llm-intent-orchestration/` | Feature documentation (`plan.md`, `implementation.md`, `verification.md`, `qa-checklist.md`). | Comply with `AGENTS.md` and repository standards. |
| `docs/decisions/llm-intent-orchestration/decisions.md` | Architecture decision record documenting LLM intent analysis vs keyword trees. | Maintain key architectural decisions per repository guidelines. |
| `CHANGELOG.md` | Add release notes for LLM intent orchestration engine. | Repository change tracking. |

---

## Interfaces

### `QueryIntentClassification` Data Model
```python
class QueryIntentClassification(BaseModel):
    primary_intent: Literal[
        "spreadsheet_operations",
        "document_authoring",
        "artifact_report",
        "code_engineering",
        "strategic_planning",
        "market_intelligence",
        "live_web_research",
        "data_analytics",
        "document_parsing",
        "conversational_greeting",
        "general_inquiry",
    ]
    requires_live_web_search: bool
    file_export_requested: bool
    export_format: Optional[Literal["md", "xlsx", "csv", "pdf", "pptx", "py", "json", "txt"]] = None
    is_multi_step: bool = True
    workflow_title: str
    workflow_description: str
    recommended_agent_ids: List[str]
    reasoning: str
```

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| **LLM Classification Latency** | An additional LLM call could add 200-400ms before workflow execution starts. | Use ultra-fast Groq LPU models (`llama-3.3-70b-versatile` or `qwen-2.5-32b`) or Gemini Flash with a concise prompt, plus an in-memory LRU cache for frequent prompts. |
| **LLM API Unavailability or Rate Limit** | If the LLM call fails, workflow planning could be interrupted. | Implement a resilient, non-blocking fallback classifier that uses token-boundary matching so the system never crashes or halts. |
| **Malformed JSON from LLM** | JSON parsing error could break intent evaluation. | Use strict structured JSON output mode, clean markdown fences with `_clean_json_markdown`, and validate with Pydantic. Fall back automatically on parsing failure. |
| **Regression on Complex Queries** | Existing specialized pipelines (e.g. Perplexity Sonar for stocks, Excel Specialist for formulas) might be misclassified. | Comprehensive unit tests covering all existing benchmark queries before enabling the new dispatcher. |

---

## Verification Plan

- **Unit tests**: `backend/test_llm_intent_orchestration.py` covering:
  - Complex spreadsheet query classification (`excel_specialist`)
  - Creative guide query with download intent (`document_authoring` + `export_format: md`)
  - Live stock query with spreadsheet intent (`market_intelligence` + `requires_live_web_search: True` + `export_format: xlsx`)
  - Casual greetings (`conversational_greeting` -> single step)
  - Code implementation requests (`code_engineering`)
  - Fallback classifier resilience when LLM raises exception
- **Regression tests**:
  - `backend/test_orchestration_query_routing.py`
  - `backend/test_excel_specialist.py`
  - `backend/test_aggressive_researcher_orchestration.py`
- **Commands**:
  - `backend\venv\Scripts\python backend/test_llm_intent_orchestration.py`
  - `backend\venv\Scripts\python backend/test_orchestration_query_routing.py`
  - `backend\venv\Scripts\python backend/test_excel_specialist.py`
  - `backend\venv\Scripts\python backend/test_aggressive_researcher_orchestration.py`
  - `npm --prefix frontend run build`

---

## Rollout
- Fully backward compatible: Existing API contracts in `/api/chat` and `/api/workflows` remain unchanged.
- Intent analysis runs transparently inside `synthesize_on_the_fly_workflow`.
- Zero database migrations required.
