from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def current_iso_time() -> str:
    return datetime.now(timezone.utc).isoformat()


class Evidence(BaseModel):
    """
    Atomic factual claim in the Evidence Ledger.
    Every factual claim cited in drafts must resolve to an Evidence record by ID.
    """
    id: str = Field(..., description="Unique evidence ID, e.g. E001, E014. Cited as [E001] in text.")
    section: str = Field(..., description="Target section slug, e.g. 'company_snapshot', 'securities_litigation'")
    claim: str = Field(..., description="Atomic factual statement extracted from source")
    value: Optional[str] = Field(None, description="Exact extracted value, metric, date, or status")
    as_of: Optional[str] = Field(None, description="Date the fact was verified/true (YYYY-MM-DD)")
    status: Literal["found", "not_found"] = Field("found", description="'found' or 'not_found'")
    source_url: str = Field(..., description="Direct URL or SEC accession number of the primary source")
    source_type: Literal["court", "regulator", "filing", "rating_agency", "news", "other"] = Field(
        "other", description="Classification of the source publisher"
    )
    published: Optional[str] = Field(None, description="Publication date of the source article/filing")
    confidence: Literal["high", "med", "low"] = Field("high", description="Assessed confidence tier")
    quote: Optional[str] = Field(None, description="Verbatim snippet from source text for adversarial verification")


class EntityCard(BaseModel):
    """
    Resolved corporate entity metadata injected into prompt prefixes.
    Derived deterministically from SEC EDGAR submissions and directory lookups.
    """
    ticker: str = Field(..., description="Stock ticker symbol, e.g. AAPL")
    legal_name: str = Field(..., description="Official SEC legal corporate name")
    cik: str = Field(..., description="10-digit zero-padded SEC Central Index Key")
    former_names: List[str] = Field(default_factory=list, description="Historical corporate names")
    sic_code: Optional[str] = Field(None, description="Standard Industrial Classification code")
    industry: Optional[str] = Field(None, description="SIC industry title or description")
    hq_address: Optional[str] = Field(None, description="Corporate headquarters location")
    country_of_domicile: Optional[str] = Field(None, description="Single legal registration home country")
    cpi_score: Optional[str] = Field(None, description="Transparency International CPI score (e.g. 71/100, rank 20)")
    exchange: Optional[str] = Field(None, description="Primary exchange listing (e.g. NASDAQ, NYSE)")
    fiscal_year_end: Optional[str] = Field(None, description="Fiscal year end month/day (e.g. 0930)")
    auditor: Optional[str] = Field(None, description="Current registered independent auditor")


class SectionSpec(BaseModel):
    """Configuration for an individual D&O report section."""
    name: str = Field(..., description="Section key/slug, e.g. 'company_snapshot'")
    title: str = Field(..., description="Section display header, e.g. 'COMPANY SNAPSHOT'")
    required_fields: List[str] = Field(default_factory=list, description="Mandatory factual fields")
    static_queries: List[str] = Field(default_factory=list, description="Pre-compiled static search query templates")
    stop_threshold: int = Field(2, description="Target corroborating source threshold before stopping")


class TemplateSpec(BaseModel):
    """Full compiled D&O Underwriter Report template specification."""
    id: str = Field(default="default_do_v1", description="Template identifier")
    title: str = Field(default="D&O Public Risk Underwriting Lens", description="Template title")
    sections: List[SectionSpec] = Field(default_factory=list, description="Ordered section specifications")
    system_prompt_template: str = Field(..., description="Master underwriting instructions (from web-search-prompt.txt)")
    validation_rules_template: str = Field(..., description="Validation and correction instructions (from validation-prompt.txt)")


class ValidationIssue(BaseModel):
    """An issue detected during deterministic validation or LLM adversarial audit."""
    section: str = Field(..., description="Section where issue occurred")
    field: Optional[str] = Field(None, description="Field name or claim identifier")
    problem: str = Field(..., description="Description of the discrepancy or validation rule broken")
    suggested_query: Optional[str] = Field(None, description="Targeted query to search for repair")
    severity: Literal["critical", "warning", "info"] = Field("warning", description="Severity level")


class ReportResult(BaseModel):
    """Complete output payload of the D&O Public Risk Report system."""
    report_id: str = Field(..., description="Unique report run identifier")
    ticker: str = Field(..., description="Target company ticker symbol")
    entity: EntityCard = Field(..., description="Resolved corporate entity card")
    risk_tier: str = Field(..., description="Overall D&O Risk Tier (Contained, Elevated, High-Volatility, Severe Tail Exposure)")
    executive_summary: str = Field(..., description="Executive summary narrative")
    sections: Dict[str, str] = Field(default_factory=dict, description="Section key to rendered markdown narrative")
    raw_report_text: str = Field(..., description="Full consolidated report text prior to or post validation")
    validated_report_text: str = Field(..., description="Final validated report text emitted by Validation Agent")
    artifacts: List[Dict[str, Any]] = Field(default_factory=list, description="Generated file artifacts (MD, DOCX, PDF)")
    evidence_count: int = Field(0, description="Total number of evidence rows collected in ledger")
    telemetry: Dict[str, Any] = Field(default_factory=dict, description="Per-stage latency, token, and cost metrics")
    created_at: str = Field(default_factory=current_iso_time)
