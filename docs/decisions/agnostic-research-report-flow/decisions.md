# Architecture Decision: Prompt-Driven Agnostic Research & Report Flow

## Datetime
`2026-11-05T11:17:20+05:30`

## Status
Accepted (In Planning)

## Context
The existing `do_risk_report` workflow is tightly bound to public corporate D&O risk underwriting (with hardcoded SEC EDGAR CIK lookups, financial XBRL facts, and static D&O section definitions). The requirement is to build a completely domain-agnostic research and report workflow that can take *any* subject/topic and *any* arbitrary Markdown prompt specification file (`prompt.md`) to dynamically formulate research queries, execute web search via Perplexity Search API, extract facts into an Evidence Ledger, conduct automated Gap Analysis to rerun research as needed, synthesize the report matching the prompt's layout, and invoke a File Generation Agent to compile publication-ready Markdown and ReportLab PDF documents with dynamic footnoting and NumberedCanvas page numbering. The system must support model/provider selection from the CLI and output granular hierarchical timings and token usage accounting.

## Decisions

### 1. Dynamic Markdown Prompt Specification Parser (`spec_parser.py`)
- Rather than relying on hardcoded section definitions, the workflow parses an arbitrary `.md` file at runtime.
- The parser extracts:
  1. Global preamble rules (tone, persona, forbidden content, formatting rules).
  2. Section hierarchy (`#`, `##`, `###` headings) and maps each to a discrete topic block with instructions and bullet checklists.
  3. Evidence requirements and closing statements.
- This decoupling allows the same engine to generate competitive analyses, technical whitepapers, medical summaries, geopolitical briefings, or product evaluations simply by swapping the prompt file.

### 2. Domain-Agnostic Evidence Ledger (`ledger.py`)
- Generalizes the evidence storage to accept facts from any domain, tracking:
  - Unique ID (`E001`, `E002`...)
  - Target section slug
  - Core claim / finding
  - Source URL, domain, title, and verbatim quote
  - Publication / as-of date
  - Confidence rating (`high`, `med`, `low`)
- Supports citation resolution for downstream footnote generation.

### 3. Integrated Perplexity Search API with Disk Caching & Compaction (`retrieval.py`)
- Employs the fast, direct Perplexity Search API (`POST https://api.perplexity.ai/search`) with `search_context_size="high"`.
- Features local query hash caching to optimize cost and latency on repeat queries.
- Incorporates `ResultCompactor` to remove boilerplate, collapse whitespace, and eliminate duplicate syndicated wire articles.

### 4. Granular Token Accounting & Hierarchical Timings (`telemetry.py`)
- Extends beyond wall-clock time by capturing input tokens, output tokens, and total tokens on every LLM call across all providers.
- Renders both an ASCII timing tree and columnar table in the terminal displaying:
  - Planning time
  - Per-section search & extraction latency
  - Gap analysis time & rerun iterations
  - Section drafting & synthesis latency
  - File generation & PDF compilation duration
  - Total wall-clock vs compute time, concurrency speedup factor, and token usage breakdown.

### 5. Multi-Provider CLI Flexibility
- Enables users to switch between Azure Foundry (Claude Sonnet 4.6 / Claude Opus 4.8), Groq (Llama 3.3 / GPT-OSS), Google Gemini, and IteraCompute directly via `--model` and `--provider` CLI arguments.
- Supports dual authentication for Azure Foundry (API key or dynamic Entra ID Bearer token provider) and automatic failover to `--fallback-model` upon rate limits.
