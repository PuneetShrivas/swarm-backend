# Agnostic Research & Report Generation Swarm (Portable Package)

A self-contained, domain-agnostic research and publication report generation swarm. Accepts an arbitrary prompt `.md` or `.txt` specification defining the desired report structure, queries the web via the Perplexity Search API, indexes atomic facts into a structured Evidence Ledger, drafts sections with `[E###]` citations, executes cross-section synthesis, and compiles publication-grade Markdown and ReportLab PDF documents with `Page X of Y` headers, cover metadata tables, and numbered footnote tables.

---

## Portability & Quick Start

This entire folder is **completely decoupled** and can be zipped, transferred to any environment (Ubuntu, Debian, macOS, Windows, Docker), and executed standalone.

### 1. Zipping and Transferring
To package this directory:
```powershell
# PowerShell
Compress-Archive -Path agnostic_workflow -DestinationPath agnostic_workflow.zip
```
```bash
# Linux / macOS
zip -r agnostic_workflow.zip agnostic_workflow/
```

### 2. Setup in New Environment
```bash
cd agnostic_workflow

# 1. Create and activate a Python 3.10+ virtual environment
python -m venv venv
source venv/bin/activate       # On Linux/macOS
# .\venv\Scripts\Activate.ps1   # On Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials
cp .env.example .env
# Edit .env and supply your PERPLEXITY_API_KEY and LLM keys (AZURE_API_KEY, GROQ_API_KEY, or GEMINI_API_KEY)
```

---

## CLI Usage

Run the workflow using `run_workflow.py`:

```bash
# Basic run with default 8-section research report template
python run_workflow.py "Solid State Battery Commercialization"

# Run with a custom prompt specification file
python run_workflow.py "NVIDIA Corporation" \
  --prompt-file path/to/prompt.md \
  --provider azure \
  --model claude-sonnet-4-6 \
  --fallback-model claude-opus-4-8 \
  --mode standard

# Run using Groq LPU with tabular terminal output
python run_workflow.py "Quantum Computing Milestones" \
  --prompt-file path/to/prompt.md \
  --provider groq \
  --model llama-3.3-70b-versatile \
  --format table
```

### CLI Options

| Argument | Flag | Default | Description |
|---|---|---|---|
| `subject` | Position 1 | *Required* | Target company, topic, technology, or person to research |
| `--prompt-file` | `-p` | `templates/standard_research_report.md` | Path to prompt Markdown or text file defining report sections |
| `--provider` | | `azure` | LLM provider: `azure`, `azure-foundry`, `groq`, `gemini`, `iteracompute` |
| `--model` | `-m` | `claude-sonnet-4-6` | LLM model for planning, extraction, drafting, and synthesis |
| `--fallback-model` | | `claude-opus-4-8` | Failover model on 429 TPM rate-limit errors |
| `--mode` | | `standard` | `fast` (1 round, no gap check), `standard` (2 rounds + gap check), `deep` (3 rounds + deep gap) |
| `--output-dir` | `-o` | `./artifacts` | Directory to output generated `.md`, `.pdf`, and `_telemetry.json` |
| `--format` | `-f` | `tree` | Terminal telemetry display: `tree`, `table`, or `json` |
| `--quiet` | `-q` | `False` | Suppress intermediate step logs |

---

## Prompt Specification Formatting

The workflow dynamically parses prompt specification files. Both of the following styles are fully supported:

### Style A: Standard Markdown Headers (`##`)
```markdown
# {SUBJECT}

## 1. EXECUTIVE SUMMARY
- Summary of core findings

## 2. FINANCIAL OVERVIEW
- Revenue trends
- Balance sheet flexibility

## 3. OVERALL SYNTHESIS & VERDICT
- Final assessment
```

### Style B: Plain Uppercase or Bold Headers
```text
You are a senior analyst. Carry out research for the target company.

COMPANY SNAPSHOT
Legal name
HQ footprint

** UPDATES / PRESS RELEASES / NEWS**
Litigation dockets
Leadership changes

FINANCIAL OVERVIEW
Revenue numbers
Debt maturity

OVERALL D&O UNDERWRITER VERDICT
HEADLINE
Final band
```

The specification parser automatically detects section names, excludes metadata/instructions (e.g. `TARGET COMPANY:`, `RULES:`, `IN SCOPE:`), identifies synthesis sections (e.g. `VERDICT`, `EXECUTIVE SUMMARY`), and extracts trailing closing statements.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   User Prompt Specification |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    Dynamic Spec Parser      |
                      +--------------+--------------+
                                     |
                                     v
                   +-----------------------------------+
                   |   Per-Section Parallel Swarm      |
                   |   (Plan -> Perplexity Search ->   |
                   |    Compactor -> Evidence Ledger   |
                   |    -> Gap Check Loop -> Drafter)  |
                   +-----------------+-----------------+
                                     |
                                     v
                      +-----------------------------+
                      | Cross-Section Synthesis Pass|
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | File Generation Agent       |
                      | - Citation to Footnote Map  |
                      | - ReportLab NumberedCanvas  |
                      |   (Page X of Y, Meta Cards) |
                      +--------------+--------------+
                                     |
                       +-------------+-------------+
                       |                           |
                       v                           v
              Publication Markdown         Publication PDF
              & Telemetry JSON
```

---

## File Structure

```
agnostic_workflow/
├── __init__.py               # Package metadata
├── config.py                 # Multi-location .env loader
├── models.py                 # Data models (SectionSpec, AgnosticEvidence, etc.)
├── spec_parser.py            # Dynamic Markdown & text specification parser
├── ledger.py                 # Thread-safe sequential evidence ledger
├── retrieval.py              # Zero-dependency Perplexity Search API queue & compactor
├── roles.py                  # Multi-provider LLM executor with token metrics
├── renderer.py               # ReportLab PDF (NumberedCanvas) & Markdown compiler
├── telemetry.py              # ASCII timing trees and token accounting tables
├── orchestrator.py           # Multi-stage research & drafting orchestrator
├── run_workflow.py           # Standalone CLI entrypoint
├── templates/
│   └── standard_research_report.md
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # Deployment & usage documentation
```
