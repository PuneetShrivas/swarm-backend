# Azure AI Foundry Three-Agent Workflow Pipeline

Connects sequentially to three Azure AI Foundry preview agents:
1. **`DO-researcher`**: Conducts deep risk research from user instructions/ticker.
2. **`DO-validator`**: Audits and validates the research findings against underwriting guidelines.
3. **`DO-report-generator`**: Formats the audited content into an executive publication structure, which is compiled into a professional PDF report.

---

## 1. Prerequisites & Dependencies

The required packages are already installed in `backend/venv`:
```bash
pip install "azure-ai-projects>=2.1.0" azure-identity reportlab python-dotenv
```

---

## 2. Azure Entra ID Authentication

The script uses Azure's `DefaultAzureCredential` to connect to:
`https://puneetshrivas32-0871-resource.services.ai.azure.com/api/projects/puneetshrivas32-0871`

To authenticate, choose **any one** of the following:

### Option A: Service Principal (Recommended for CI / Non-interactive)
Add your Azure App Registration credentials to `backend/.env` or `.env`:
```env
AZURE_TENANT_ID="<your-azure-tenant-id>"
AZURE_CLIENT_ID="<your-app-client-id>"
AZURE_CLIENT_SECRET="<your-app-client-secret>"
```

### Option B: Azure CLI
In your local terminal, sign in once:
```bash
az login
```

### Option C: Interactive Browser Sign-in
Run the script with the `--interactive` flag to open your default browser and sign in with your Azure credentials:
```bash
python azure_agents_pipeline/run_pipeline.py NVDA --interactive
```

---

## 3. Usage & CLI Examples

### Standard Target Public Company Evaluation:
```bash
python azure_agents_pipeline/run_pipeline.py NVDA
```

### Specify Custom Output Directory:
```bash
python azure_agents_pipeline/run_pipeline.py MSFT --output-dir ./reports
```

### Custom Prompt / Investigation Instructions:
```bash
python azure_agents_pipeline/run_pipeline.py --input "Investigate board turnover and SEC accounting restatements for target entity."
```

### Overriding Agent Names or Endpoint:
```bash
python azure_agents_pipeline/run_pipeline.py TSLA \
  --researcher DO-researcher \
  --validator DO-validator \
  --generator DO-report-generator \
  --endpoint "https://puneetshrivas32-0871-resource.services.ai.azure.com/api/projects/puneetshrivas32-0871"
```

---

## 4. Output Artifacts & Telemetry

Each execution produces:
1. **Official PDF Document**: `DO_Risk_Report_<TICKER>_<TIMESTAMP>.pdf` (with executive styling, metadata table, and page numbering).
2. **Markdown Document**: `DO_Risk_Report_<TICKER>_<TIMESTAMP>.md` (raw structured output).
3. **Telemetry JSON**: `DO_Risk_Report_<TICKER>_<TIMESTAMP>_telemetry.json` (per-step duration, token consumption, response IDs, and conversation IDs).

---

## 5. Fast Alternative Pipeline (`run_fast_pipeline.py`)

Sends target company name to `DO-researcher`, and directly routes the preliminary output to:
1. **Pathway 1 (Agent Path)**: `DO-report-generator` agent (bypassing validator).
2. **Pathway 2 (Direct Model Path)**: Azure Foundry model (`claude-sonnet-4-6` or `claude-opus-4-8` via direct messages API) for rapid report synthesis.

### Usage & Modes:

```bash
# Run both pathways concurrently, generate PDFs for both, and display comparative telemetry:
python azure_agents_pipeline/run_fast_pipeline.py NVDA --mode both

# Run only Pathway 1 (Researcher → Report Generator Agent):
python azure_agents_pipeline/run_fast_pipeline.py NVDA --mode agent

# Run only Pathway 2 (Researcher → Direct Azure Foundry Model):
python azure_agents_pipeline/run_fast_pipeline.py NVDA --mode direct

# Choose custom Azure Foundry model for direct pathway:
python azure_agents_pipeline/run_fast_pipeline.py MSFT --mode direct --model claude-opus-4-8
```

### Direct Mode Senior Underwriter Instructions Prompt:
When running Pathway 2 (Direct Model), the system automatically transmits the standardized 13-section D&O Underwriting Report prompt ([`azure_agents_pipeline/prompts.py`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/azure_agents_pipeline/prompts.py)), instructing Claude to structure evidence across:
- **Title**: `# COMPANY NAME`
- **1. Executive Summary**
- **2. Company Snapshot** (CPI, listings, share price, assets, revenue, AI exposure)
- **3. Updates / Press Releases / News** (chronological, max 12 items, strict format)
- **4. Financial Overview & Debt/Refinancing Profile**
- **5. Analysts & Sentiment**
- **6. Governance & Culture**
- **7. Director & Officer History** (mandatory 4 roles + discretionary, 10-year horizon)
- **8. Strategic & Operational Profile**
- **9. Securities Class Action Risk** (Likelihood, Severity, Side A/C bands, Scenario)
- **10. Legal, Regulatory & Claims Context**
- **11. ESG, Cyber & Operational Exposure**
- **12. Forward-Looking Strategic Risk**
- **13. Overall D&O Underwriter Verdict & Band Register**
- **Closing Statement**: `"Assessment based solely on information contained in this report."`

You can optionally override this prompt with a custom markdown file:
```bash
python azure_agents_pipeline/run_fast_pipeline.py NVDA --mode direct --prompt-file path/to/custom_prompt.md
```
