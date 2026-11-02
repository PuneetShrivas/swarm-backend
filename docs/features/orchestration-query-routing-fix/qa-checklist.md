# QA Checklist: Orchestration Query Routing Fix & Markdown Document Artifact Synthesis

**Slug**: `orchestration-query-routing-fix`  
**Created At**: `2026-11-02T17:37:00+05:30`  
**Completed At**: `2026-11-02T17:45:45+05:30`  
**Status**: PASSED  

---

- [x] **1. Word Boundary Regex on Market Tickers**:
  - [x] Queries with `"download"` do not match `"dow"`.
  - [x] Queries with `"stockpile"` do not match `"stock"`.
  - [x] Queries with `"btc"` or `"s&p"` or `"dow jones"` match when used as standalone terms.

- [x] **2. Document Authoring & Downloadable Markdown Synthesis Routing**:
  - [x] Query `"generate a markdown md file instructing how a good poem should be written and make it available for download"` routes to `Document Authoring & Downloadable Markdown Synthesis Pipeline`.
  - [x] Step 1 is assigned to `writer` ("Creative & Instructional Content Authoring").
  - [x] Step 2 is assigned to `file_creator` ("Downloadable Markdown File Compilation").
  - [x] Step 3 is assigned to `synthesizer` ("Executive Overview & File Delivery").

- [x] **3. Downloadable Markdown Artifact Generation**:
  - [x] `extract_file_artifact_from_turn` generates an artifact for `.md` files.
  - [x] `mime_type` is `text/markdown`.
  - [x] `filename` ends in `.md`.
  - [x] `downloadable` is `True`.
  - [x] `content_base64` is populated.

- [x] **4. Fallback Extraction from Prior Step Outputs**:
  - [x] When synthesizer's final result is a brief summary or message, the artifact is successfully recovered from the `file_creator` step output.

- [x] **5. Regressions Verification**:
  - [x] Stock market live research query still triggers Perplexity Sonar and Excel file generation.
  - [x] Excel specialist query still routes to Excel Specialist Agent.
  - [x] Frontend build succeeds.
