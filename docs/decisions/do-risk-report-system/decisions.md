# Architectural Decisions: D&O Public Risk Report System

Created At: 2026-11-03T12:45:00+05:30
Updated At: 2026-11-03T12:57:00+05:30
Status: Draft | Proposed

## 1. Evidence Ledger as the Single Bus

- **Context**: The D&O Public Risk Report requires strict auditability and high token efficiency. Passing raw web search text or conversational histories across multiple agents/steps inflates prompt tokens, risks hallucinations, and makes citation validation impossible.
- **Decision**: All extracted facts must reside in a typed `EvidenceLedger` (`Evidence` records with `id="E###"`). Roles downstream of `extract` (e.g. `gap`, `draft`, `verify`, `repair`) read only section-scoped ledger rows. Drafts cite claims using `[E###]` tokens, which are mechanically converted to footnotes at render time.
- **Consequences**:
  - Predictable token budgets per call.
  - Zero raw search text leaks into drafting.
  - Mechanical O(1) citation verification without LLM reasoning.

## 2. Deterministic Code for SEC EDGAR Filings & XBRL Facts

- **Context**: LLMs are notoriously unreliable at arithmetic, reading large multi-hundred-page 10-K tables, and extracting exact financial statements without rounding or misinterpreting units (e.g. thousands vs. millions).
- **Decision**: Primary company filing metrics (revenues, operating income, net income, assets, liabilities, shares outstanding, auditor name, and filing accession dates) are pulled directly via SEC EDGAR APIs (Company Facts XBRL and Submissions JSON) in deterministic Python code. These metrics are placed directly into the Evidence Ledger with `source_type="filing"` and `confidence="high"`.
- **Consequences**:
  - 100% accuracy on financial figures.
  - Zero token spend on parsing massive 10-K financial tables.
  - SEC compliance with `User-Agent` requirements and rate limiters.

## 3. Inference on Groq Models & Web Search Queues via Perplexity

- **Context**: The user specified that Claude models should not be used; instead, available Groq models should be used for inference, and Perplexity should be used for web search queues.
- **Decision**:
  - All LLM worker roles are mapped to available Groq models via `app.groq_client`:
    - Fast extraction and gap analysis: `llama-3.1-8b-instant` (sub-second throughput, ~800-1000 tokens/sec).
    - Planning, drafting, and repair: `llama-3.3-70b-versatile` or `qwen-2.5-32b`.
    - Synthesis and adversarial verification: `llama-3.3-70b-versatile` or `deepseek-r1-distill-llama-70b`.
  - All web search queues are dispatched to the Perplexity Search API with domain filters (courtlistener, sec.gov, justice.gov, credit agencies) and query-hash caching.
- **Consequences**:
  - Significantly lower latency on the critical path due to Groq's high LPU throughput.
  - Eliminates Anthropic Claude dependency.
  - Retains grounded, live Perplexity search retrieval with domain filters.

## 4. Default Prompt Templates (`web-search-prompt.txt` & `validation-prompt.txt`)

- **Context**: Standardized D&O underwriting requires strict report formatting (Snapshot, CPI score, News 12-month window, Financial Overview with debt maturities in one line, SCA Risk with Contained/Elevated/High-Volatility/Severe Tail Exposure bands, Overall Verdict with verbatim Band Register) and post-generation correction.
- **Decision**:
  - Store and compile `web-search-prompt.txt` as the default report specification template in `template_spec.py`.
  - Store and compile `validation-prompt.txt` as the default validation template with dynamic `{{currentDate}}` interpolation.
- **Consequences**:
  - 100% adherence to the required 0.01%-tier senior D&O underwriter format.
  - Standardized terminology, scales, and constraints across all sections.

## 5. Dedicated Validation Agent with Zero Web Access

- **Context**: The user specified that after the report has been generated, there needs to be a validation agent which verifies with the validation prompt.
- **Decision**:
  - Implement a dedicated agent `do_risk_validator` positioned immediately after executive synthesis in the workflow DAG.
  - The Validation Agent has NO web access and works strictly from the report text as input.
  - Enforces:
    - 12-month calendar cutoff for news/updates strictly before `{{currentDate}}`, protecting within-window news items and ordering newest-first.
    - Share price date recency check: if labeled "current/today" but date is older than latest trading day, relabels "last close (<stated date>)".
    - Revenue-trend line descending order (latest year -> oldest).
    - Deletion of unsourced culture characterizations and unanchored superlatives.
    - Cross-section date and name agreement, and inserting "Data unavailable." for empty headings.
- **Consequences**:
  - Clean separation of concerns between drafting and post-generation quality assurance.
  - Enforces deterministic and stylistic report integrity prior to publication artifact rendering.
