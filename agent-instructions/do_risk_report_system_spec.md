# D&O Public Risk Report System: Requirements & Architecture

**Input:** company ticker + long report template + validation checklist
**Output:** validated D&O public-risk report (DOCX/PDF) with citations and a limitations appendix
**Stack:** Python (asyncio) · Perplexity Search API (retrieval) · Claude API (Haiku / Sonnet / Opus) · EDGAR (primary filings)

---

## 1. Purpose

Given a ticker, automatically produce a complete D&O public-risk report in the supplied template. The report must pass the supplied validation checklist before delivery. The system must be fast, token-efficient, and traceable: every claim links to a source, and gaps are reported as "not found" rather than filled from model memory.

---

## 2. Core Design Principles

1. **Python owns control flow.** The workflow is known in advance (fixed template, fixed checklist), so it is a DAG with parallel fan-out, joins, and bounded loops. The LLM is never asked "what should I do next".
2. **One LLM worker, many roles.** A single function `run_role(role, inputs)` is invoked with different system prompts, schemas, and model tiers. A role is configuration, not a separate agent.
3. **Evidence Ledger as the only data bus.** Raw search text is consumed once (by Extract) and never passed downstream. Every later stage reads typed, section-scoped ledger rows.
4. **Primary sources first.** EDGAR filings and structured APIs beat search snippets. Perplexity covers what filings do not (news, litigation, ratings, history).
5. **Raw search, not summarized search.** Use the Perplexity Search API (ranked results), not Sonar chat completions. A second LLM layer adds cost, latency, and hallucination risk.
6. **"Not found" is a first-class result.** Never fill gaps from model memory.
7. **Code does arithmetic and date logic.** Never the LLM.

---

## 3. Components

### 3.1 Deterministic code (no LLM)

| Component | Duties |
|---|---|
| **Orchestrator** | DAG execution, parallel fan-out, pipelined scheduling, budgets, retries, checkpointing, cost and latency logging |
| **Retrieval layer** | Perplexity wrapper (cache, dedupe, domain/recency filters, result compaction, multi-query batching); EDGAR fetcher (submissions API, XBRL facts API, 10-K, 10-Q, DEF 14A, 8-Ks) |
| **Evidence Ledger** | Typed records, dedupe on (claim, source), section-scoped reads, JSONL persistence |
| **Deterministic validator** | Section/field completeness, citation resolution, number and date consistency, mechanical checklist items |
| **Renderer** | Converts `[E###]` citations to footnotes, exports DOCX/PDF, appends limitations and low-confidence items |

### 3.2 The single LLM worker and its roles

| Role | Task | Model | Input scope | Output |
|---|---|---|---|---|
| **Plan** | Build entity card; refine section queries beyond the static query library | Sonnet | Template section + entity card | JSON queries |
| **Extract** | Turn compacted results into atomic facts; reject wrong-entity and irrelevant results; no inference | Haiku (Sonnet for dense legal text) | One batch of results | Ledger records |
| **Gap** | Compare ledger to section field requirements; emit targeted follow-up queries; flag single-source high-stakes facts | Haiku or Sonnet | Section ledger rows | JSON queries or empty |
| **Draft** | Write one section from its ledger rows, citing IDs, stating "not found" where applicable | Sonnet | Section ledger rows | Section text |
| **Synthesize** | Executive summary, overall risk rating under one rubric, cross-section consistency | Opus | Section drafts + key ledger rows | Summary + rating |
| **Verify** | Adversarial check of each claim against its cited evidence; judgment items from the checklist | Opus | Draft + cited rows only | Issue list |
| **Repair** | Rewrite flagged text from new or existing evidence | Sonnet | Issues + affected rows | Patched text |

Same implementation, different prompt, schema, and scope. Adding or changing a role means editing configuration only.

---

## 4. Evidence Ledger Schema

```python
class Evidence(BaseModel):
    id: str                      # "E014", cited by ID in drafts, never by URL
    section: str
    claim: str                   # one atomic fact
    value: str | None = None     # amount, date, status
    as_of: str | None = None     # date the fact was true
    status: Literal["found", "not_found"] = "found"
    source_url: str
    source_type: Literal["court", "regulator", "filing", "rating_agency", "news", "other"]
    published: str | None = None
    confidence: Literal["high", "med", "low"]
    quote: str | None = None     # short verbatim snippet for verification
```

Drafts cite `[E014]`. This cuts output tokens and makes citation validation mechanical.

---

## 5. Workflow

```
resolve_entity (EDGAR, code)  ──> entity card
        │
        ├─> EDGAR structured pull (XBRL, filings)  ───────────────┐  (parallel, no LLM for numbers)
        │                                                          │
        └─> per section, in parallel:                              │
              static queries + Plan refinements                    │
                └─> Perplexity (batched, cached)                   │
                      └─> compact ─> Extract ─> Ledger <───────────┘
                                      └─> Gap ─> follow-up search (max 2 rounds)
                                      └─> Draft (starts the moment the section completes)
                                              └─> Verify (starts the moment the draft completes)
        join ─> Synthesize (Opus) ─> final cross-section Verify
        ─> Repair (only failed items, max 2 iterations) ─> Render ─> deliver
```

Steps in order:
1. **Entity resolution (code):** ticker to legal name, CIK, former names, parent/subsidiaries, HQ, exchange. Produces the entity card injected into every prompt.
2. **Research (parallel per section):** query, search, compact, extract, gap-check. Max 2 gap-fill rounds.
3. **Draft (parallel):** each section starts immediately when its research completes.
4. **Verify (parallel):** each draft is verified as soon as it is written.
5. **Synthesize:** one Opus call for summary and rating.
6. **Final validation:** deterministic checks plus a cross-section Verify.
7. **Repair:** re-research and rewrite only the failed items. Max 2 iterations.
8. **Render and deliver** with an appendix of low-confidence, single-source, and unresolved items.

---

## 6. Speed Architecture (the critical-path plan)

Wall-clock time is set by the **longest chain of dependent steps**, not by total work. The design goal is to shorten that chain and keep it off the slowest components (Opus, serial searches, barriers).

### 6.1 Remove LLM calls from the critical path
- **Static query library.** Pre-write 5-10 query templates per section at design time (for example `"{company} securities class action {year}"`, `"{company} SEC investigation"`, `"{company} derivative lawsuit"`). Fill with the entity card. Run them immediately, with no Plan call before the first search. The Plan role only adds company-specific refinements in parallel, after the first results are already flowing.
- **EDGAR structured data in code.** Financials, share counts, filing dates, auditor, and officer lists come from the XBRL and submissions APIs via plain HTTP and parsing. No search and no LLM for these fields.
- **Template compiled once.** Parse the template and checklist into section specs and field lists at startup (cached to disk), not per run.

### 6.2 Pipeline, don't batch-and-wait
- Use `asyncio` tasks per section with **no global barriers** until Synthesize. Draft starts the instant a section's ledger is ready. Verify starts the instant a draft is ready.
- Start **Extract on each search response as it arrives**, not after all searches finish.
- Run the EDGAR pull concurrently with all Perplexity searches.
- Overlap the Opus Synthesize prep: assemble its inputs incrementally as sections finish, so the call fires the moment the last section lands.

### 6.3 Maximize parallelism safely
- Fan out all independent calls with `asyncio.gather`.
- **Token-bucket rate limiters** per API (sized to your actual limits) instead of fixed semaphores, so the pipe stays full without 429 storms.
- Reuse HTTP connections (`httpx.AsyncClient` with HTTP/2 and keep-alive, one shared client).
- Batch multiple queries per Perplexity request where supported (verify limits in current docs).
- Hedge slow calls: if a search or LLM call exceeds a latency threshold (for example p95), launch a duplicate and take the first result.

### 6.4 Keep Opus off the long path
- Opus runs only at Synthesize and on the final cross-section Verify. Per-section Verify can run on **Sonnet first**, escalating to Opus only for sections that fail or for high-stakes facts.
- Opus calls have small inputs (drafts and cited rows only), which keeps their latency low.

### 6.5 Shrink what each call reads and writes
- **Prompt caching:** template, checklist, schemas, and entity card in one shared cached prefix. **Warm the cache** with one cheap call at startup so parallel calls hit it instead of all missing at once.
- **Compact search results** before Extract: title, URL, date, top snippet, per-result character cap. Dedupe URLs and syndicated copies.
- **Section-scoped context:** each role sees only its section's ledger rows.
- **Forced tool-use JSON** for all structured roles: no preamble, no parse retries.
- **Tight `max_tokens`** per role, and terse schemas (short field names, enums instead of free text).
- **Draft with citations by ID**, not URLs, to cut output tokens.

### 6.6 Stop early
- Per-section stop rule: *two corroborating sources, or a documented "not found" after N queries*.
- Skip the Gap round if all required fields are met. Skip corroboration for low-stakes fields.
- Hard caps: queries per section, rounds, characters per result, total spend and time per run. On hitting a cap, degrade to "not found" and disclose.

### 6.7 Cache aggressively
- **Search cache** by query hash (disk or SQLite/Redis). Repair loops and reruns cost nothing.
- **Ledger cache per ticker with TTL** (for example filings: 30 days; litigation and news: 24 hours). A re-run for the same company only refreshes the stale categories.
- **Checkpoint every stage** to disk so a crash or timeout resumes mid-pipeline.

### 6.8 Make validation cheap and parallel
- Run **deterministic checks first** (milliseconds, free), and only send failures and judgment items to Verify.
- Verify runs **per section in parallel**, with each call seeing only the draft and its cited rows.
- **Targeted repair:** re-research and re-verify only changed sections, never the whole report.

### 6.9 Modes
| Mode | Behavior | Use |
|---|---|---|
| **Fast** | 1 gap round, Sonnet verify only, fewer queries per section | First look, triage |
| **Standard** | 2 gap rounds, Sonnet verify, Opus final pass | Default |
| **Thorough** | Opus verify per section, two-source rule enforced everywhere, full repair loop | Final deliverables |
| **Batch** | Message Batches API for Extract and Verify (about 50% cheaper, asynchronous) | Many tickers overnight |

### 6.10 Latency budget (target for Standard mode, adjust to your limits)
| Stage | Target |
|---|---|
| Entity resolution + EDGAR pull | 10-20 s |
| Research (all sections in parallel, 2 rounds) | 60-120 s |
| Draft + per-section Verify (pipelined) | 30-60 s |
| Synthesize + final Verify | 30-60 s |
| Repair (if needed) | 30-90 s |
| Render | under 10 s |
| **Total** | **about 3-6 minutes** |

Measure actual per-stage latency from the first runs and tune from the real critical path.

---

## 7. Quality and Accuracy Requirements

- **Verify runs in a fresh context**, never sharing history with the Draft call, and with an adversarial prompt ("find unsupported, overstated, contradictory, or stale statements").
- Each role receives **only its scoped inputs** and its **own schema**. Never pass full conversations between roles.
- **Source hierarchy:** court and regulator records, then company filings, then rating agencies, then reputable news, then other.
- **Two-source rule** for settlements, case outcomes, and restatements, otherwise `confidence: low` with an automatic corroboration query.
- **Entity guard** in every Extract prompt: reject results about similarly named companies (use CIK, legal name, former names, HQ).
- **Domain filters per workstream** (court and regulator domains for litigation, `sec.gov` for filings, rating-agency domains for ratings), falling back to open web only on empty results.
- **Date-stamp** every claim (`as_of`) and flag stale items (for example litigation status older than 90 days) for re-check.
- **Search snippets are not documents.** For legally precise facts (outcomes, settlement terms), fetch the primary page or docket text and extract from the full text.

---

## 8. Validation Design

**Layer 1: deterministic (code, free)**
- Every template section and field is present and non-empty.
- Every `[E###]` citation resolves to a ledger row.
- Numbers in the narrative match ledger values.
- Dates are valid, with no future dates and no stale `as_of`.
- Mechanical checklist items (format, ordering, required disclaimers) pass.

**Layer 2: LLM Verify (per section, parallel, fresh context)**
- Each claim is supported by its cited evidence.
- No overstated, contradictory, or mis-attributed statements.
- Risk rating is consistent with the narrative and rubric.
- Judgment items from the checklist.

**Output:** list of `{section, field, problem, suggested_query}`.
**Repair:** re-research only those items, patch, re-validate only changed sections. Max 2 iterations. Unresolved items are listed explicitly in the final report.

---

## 9. Reference Skeleton

```python
import asyncio, hashlib, json, os, httpx
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

claude = AsyncAnthropic()
HAIKU, SONNET, OPUS = "claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"
CACHE = {}  # replace with disk / SQLite / Redis

ROLES = {   # a role = config, not an agent
    "plan":       dict(model=SONNET, system=PLAN_PROMPT,       schema=QUERY_SCHEMA,    max_tokens=800),
    "extract":    dict(model=HAIKU,  system=EXTRACT_PROMPT,    schema=EVIDENCE_SCHEMA, max_tokens=3000),
    "gap":        dict(model=HAIKU,  system=GAP_PROMPT,        schema=QUERY_SCHEMA,    max_tokens=600),
    "draft":      dict(model=SONNET, system=DRAFT_PROMPT,      schema=SECTION_SCHEMA,  max_tokens=2500),
    "synthesize": dict(model=OPUS,   system=SYNTH_PROMPT,      schema=SUMMARY_SCHEMA,  max_tokens=2000),
    "verify":     dict(model=SONNET, system=VERIFY_PROMPT,     schema=ISSUES_SCHEMA,   max_tokens=1500),
    "repair":     dict(model=SONNET, system=REPAIR_PROMPT,     schema=SECTION_SCHEMA,  max_tokens=2500),
}

async def run_role(role: str, user: str, *, model_override=None):
    cfg = ROLES[role]
    async with LLM_LIMITER:                       # token bucket
        resp = await claude.messages.create(
            model=model_override or cfg["model"],
            max_tokens=cfg["max_tokens"], temperature=0,
            system=[SHARED_CACHED_PREFIX,         # template + checklist + entity card, cache_control set
                    {"type": "text", "text": cfg["system"]}],
            tools=[{"name": "out", "description": "result", "input_schema": cfg["schema"]}],
            tool_choice={"type": "tool", "name": "out"},
            messages=[{"role": "user", "content": user}],
        )
    return next(b.input for b in resp.content if b.type == "tool_use")

async def process_section(section, entity, ledger):
    queries = fill_static_queries(section, entity)                  # no LLM, starts instantly
    refine = asyncio.create_task(run_role("plan", plan_input(section, entity)))
    for rnd in range(MAX_ROUNDS):
        async def search_extract(q):
            res = await pplx_search(q["text"], domains=q.get("domains"), recency=q.get("recency"))
            return await run_role("extract", extract_input(section, entity, compact(res)))
        batches = await asyncio.gather(*[search_extract(q) for q in queries])
        for b in batches: ledger.add(b["items"])
        gaps = await run_role("gap", gap_input(section, ledger.for_section(section.name)))
        if not gaps["queries"]: break
        queries = gaps["queries"] + (refine.result()["queries"] if rnd == 0 and refine.done() else [])
    draft = await run_role("draft", draft_input(section, ledger.for_section(section.name)))
    issues = programmatic_checks(draft, ledger) + (await run_role("verify", verify_input(draft, ledger)))["issues"]
    return section, draft, issues

async def run(ticker):
    entity = await resolve_entity(ticker)                           # EDGAR, code
    await warm_cache(entity)                                        # primes the shared prefix once
    ledger = Ledger()
    results = await asyncio.gather(
        edgar_structured_pull(entity, ledger),                      # XBRL + filings, no LLM for numbers
        *[process_section(s, entity, ledger) for s in SECTIONS])    # pipelined, no barriers
    drafts = [r for r in results[1:]]
    report = await run_role("synthesize", synth_input(drafts, ledger))
    for _ in range(2):
        issues = programmatic_checks(report, ledger) + collect_issues(drafts) + await final_verify(report, ledger)
        if not issues: break
        report = await repair_loop(report, issues, ledger)          # targeted re-research only
    return render_docx(report, ledger)
```

Verify Perplexity request/response field names, filters, batching, and rate limits against current documentation before building the wrapper.

---

## 10. Operational Requirements

- **Persistence:** ledger (JSONL), drafts, and stage outputs written after each stage for resume.
- **Reliability:** exponential backoff on both APIs, circuit breaker on repeated rate-limit or 5xx errors, graceful degradation to "not found".
- **Observability:** per-stage latency, tokens, cache-hit rate, and cost logged each run, including the critical path, so tuning targets the real bottleneck.
- **Budgets:** hard caps on queries per section, rounds, characters per result, wall-clock time, and spend per run.
- **Human-in-the-loop:** appendix lists low-confidence, single-source, and unresolved items for reviewer attention.

---

## 11. Acceptance Criteria

- Every template section is populated or explicitly marked "not found / not publicly available".
- Every factual claim carries a resolving citation.
- Zero checklist failures at delivery, or each remaining failure disclosed.
- Human spot-check finds no wrong-entity data and no fabricated facts.
- Standard-mode end-to-end latency meets the target in section 6.10 (tuned from measured runs).
- Per-stage token, latency, and cost report produced for every run.

---

## 12. Known Limits

- Paywalled sources (some rating agencies, proprietary D&O datasets, certain docket systems) are inaccessible; those fields degrade to "not publicly available".
- Search APIs return snippets; legally precise facts require fetching the full primary document.
- Parallelism trades total cost for speed: more concurrent calls means more total tokens. Use Fast, Standard, Thorough, and Batch modes to choose the trade-off.
- Latency figures are planning targets, not guarantees. They depend on API rate limits, model load, and the number of template sections.
