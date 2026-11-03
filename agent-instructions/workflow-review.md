Part 1: question comes in
wf_web_search_smart_agent.py invoke() [CHANGED]: same entry point, but it now opens a completion event or push channel for the job.
ask_service.py ask() [CHANGED]: same on/off check and cost tracking, plus a per-stage timer (route, plan, search, structure, draft, validate, synthesis, delivery).
ask_service.py \_ask() [CHANGED]: calls the pre-router first and only falls through to the Gemini router if it doesn’t match.
pre_router.py match() [NEW]: deterministic and takes milliseconds. If the prompt contains a ticker or known company plus report keywords (D&O, risk report, analysis), it goes straight to Tier 3.
ask_router.py route() [UNCHANGED]: still one Gemini call deciding tier 0, 1, 2 or 3, but now only for ambiguous prompts.
Part 2: by tier
Tier 0: ask_followup.py resolve() [UNCHANGED].
Tier 1: \_ask() returns the router’s answer [UNCHANGED].
Tier 2: \_tier2_answer(), quick_answer.answer(), ask_wide.answer() and the Perplexity backup quick_answer_perplexity.answer() are all [UNCHANGED].
Tier 3: ask_service.py \_tier3_submit() [UNCHANGED].
ask_subjects.py extract() [CHANGED]: tries a ticker lookup first (EDGAR tickers file, no LLM). The LLM runs only for free-text company names. It returns legal name, CIK, former names, and HQ, which are passed into every later prompt as an entity guard.
service.py submit_analysis() [UNCHANGED] and continues in Part 3.
Part 3: research job

Setup

jobs.py create_job(), splitter.py split(), and plan_async.py start() [UNCHANGED]. The job id still returns immediately.
planner.py plan() [CHANGED]: loads the pre-compiled D&O question template (static questions with {company} placeholders, each tagged with section, required fields, preferred domains, and recency).
planner.py \_plan_small() [NEW, replaces _plan_full]: one short Sonnet call that adds only company-specific questions (known cases, industry quirks, former names). It runs in parallel with the first EDGAR fetch.
plan_cache.py get_or_build() [CHANGED]: keyed by template version plus entity, so repeat tickers skip even the small call.
queue.py enqueue() [CHANGED]: companies run concurrently on one async loop with shared semaphores sized to Perplexity and Claude rate limits, instead of a thread pool.

Per company: runner.py process() runs three lanes at once

Lane A: primary filings

edgar_fetch.py run() [NEW]: pulls the latest 10-K, 10-Qs, DEF 14A, and recent 8-Ks directly from EDGAR. It extracts financials, board and governance data, auditor changes, and risk factors straight into evidence rows, with no search involved.

Lane B: web research

extractor.py run_all() [CHANGED, replaces run_batch]: all questions are submitted at once behind a semaphore. There are no groups of 3, so a slow question delays only itself.
grounding.py \_primary() [CHANGED]: calls the raw Perplexity Search API, not Sonar chat.
Domain filters go per section (court and regulator sources for litigation, rating agency domains for ratings, and so on).
Results are compacted to title, URL, date, and the top snippet.
Searches are cached by normalized query plus entity.
Per-call timeouts are short (about 20 to 30s) and fail fast to “not found”.
Sonar runs only as a fallback when the Search API returns nothing useful.
structurer.py structure() [CHANGED]: one extraction call per section batch, not per question. It reads snippets directly (there is no intermediate “search notes” layer), uses forced JSON output, and returns not_found as a valid status.
It runs as soon as that section’s searches finish. There is no wait for the whole company.
Each row carries claim, value, as_of, source URL, source type, and confidence.

Lane C: quality gates, per section as evidence arrives

guard.py apply() [CHANGED]: still pure Python and still removes values with no source. It now also flags single-source high-stakes facts (case outcomes, settlements, restatements) and stale as_of dates.
gap_check.py run() [NEW]: compares the section’s required fields to its evidence rows. Unmet fields and single-source flags become targeted follow-up queries that go back through Lane B, capped at 1 to 2 rounds.

Drafting and validation

report_judge.py draft_section() [NEW, split out of assess]: starts for each section as soon as its evidence is final. Sections draft in parallel, and each sees only its own rows. Drafts cite evidence IDs, not URLs.
report_judge.py assess() [CHANGED]: runs after all sections of a company are drafted. The strongest model handles only the executive summary, the overall risk rating, and cross-section consistency.
validator.py run() [NEW]:
Layer 1 (code): all template sections and fields present, every citation resolves to a row, numbers and dates match the evidence, mechanical checklist items pass.
Layer 2 (separate verifier model with an adversarial prompt): runs per section in parallel and flags claims unsupported by their cited rows, plus a final cross-section pass.
Repair loop capped at 2: only failed items are re-researched and only affected sections are redrafted and rechecked.
synthesis_gate.py ensure() [CHANGED]: after the last company, writes the combined report from compact per-company summaries and ratings, not raw evidence. Called from runner.py as before.
Part 4: answer goes back
wf_web_search_smart_agent.py \_poll_job() [CHANGED]: waits on the completion event or push channel. If push isn’t possible, adaptive polling goes 1s, then 2s, then 3s, with the same 8-minute cap.
service.py job_status() [CHANGED]: reports section-level progress (“filings done, litigation running, ratings done, drafting 4/9”) so chat can show it live.
service.py job_result_markdown() and job_result() [CHANGED]: same report and sources. An appendix lists low-confidence items, single-source facts, and fields marked not found or not publicly available.
Optionally, completed sections stream to chat as they pass validation, so the user starts reading before the final synthesis.
