# Feature Plan: Orchestration Query Routing Fix & Markdown Document Artifact Synthesis

**Slug**: `orchestration-query-routing-fix`  
**Created At**: `2026-11-02T17:33:00+05:30`  
**Status**: APPROVED & IN PROGRESS  

---

## 1. Context & Problem Statement
When a user inputs a query that is not related to live market web search (e.g. `"generate a markdown md file instructing how a good poem should be written and make it available for download"`), the system incorrectly routes the request to a financial market pipeline (`Live Market & Valuation Intelligence Pipeline`) with step names like `"Live Market Data & Stock Discovery"`. Furthermore, at the end of the workflow execution, no downloadable `.md` file artifact is generated or made available.

### Root Causes
1. **False Positive Substring Match in `has_market_kw`**:
   In `backend/app/ai_generator.py`, `has_market_kw` checked `any(k in prompt_lower for k in [..., "dow", ...])`. The word `"dow"` is an exact substring of `"download"`, causing any prompt containing `"download"` to be classified as financial market research (e.g. Dow Jones index).
2. **Missing Creative Writing & Document Compilation Pipeline**:
   The workflow synthesis lacked a dedicated multi-agent branch for creative/instructional content authoring paired with file export (`writer` -> `file_creator` -> `synthesizer`), instead falling through to data analysis or market research.
3. **Restricted File Artifact Intent in `extract_file_artifact_from_turn`**:
   In `backend/app/main.py`, `extract_file_artifact_from_turn` required explicit phrases like `"generate csv"` or `"create file"`, omitting `"markdown file"`, `"md file"`, and `"available for download"`, and defaulted non-code blocks to `.txt` rather than extracting the markdown document as an `.md` artifact.

---

## 2. Proposed Architecture & Fix Strategy

### Phase 1: Strict Word-Boundary Token Matching for Financial Terms
- Replace raw substring matching in `has_market_kw` (`backend/app/ai_generator.py`) with regex word boundary patterns (`r"\bdow\b"`, `r"\bbtc\b"`, `r"\bs&p\b"`, `r"\bstock\b"`).
- Prevent `"download"`, `"stockpile"`, or similar common English words from falsely triggering financial market routing.

### Phase 2: Creative & Document Writing with File Compilation Pipeline
- In `backend/app/ai_generator.py`, add a high-priority routing pipeline:
  - Trigger: `has_doc_file_export and has_writing_creative and not has_market_kw`
  - Workflow:
    - Step 1: `writer` (Creative & Editorial Content Authoring)
    - Step 2: `file_creator` (Downloadable Markdown File Compilation)
    - Step 3: `synthesizer` (Executive Overview & File Delivery)

### Phase 3: Robust Markdown Artifact Extraction
- In `backend/app/main.py`:
  - Enhance `extract_file_artifact_from_turn` to recognize markdown file generation requests (`"markdown file"`, `"md file"`, `".md"`, `"available for download"`).
  - Extract the markdown body and generate an appropriate `.md` filename (e.g. `poetry_writing_guide_1793620875.md`) with MIME `text/markdown`.
  - Provide both `content` and `content_base64` so the chat message displays a 1-click **Download File** card.

### Phase 4: Verification & Automated Tests
- Create `backend/test_orchestration_query_routing.py` testing:
  - Exact poem markdown download query routing
  - Rejection of false positive market matches on "download"
  - Proper artifact extraction for markdown files
  - Regression check for legitimate live market queries
