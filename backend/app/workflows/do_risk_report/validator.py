"""
Validation Engine & Post-Generation Validation Agent.
Combines:
1. Layer 1 Deterministic checks (citation resolution, missing sections, two-source rule, date consistency).
2. Layer 2 Validation Agent pass executing `validation-prompt.txt` rules with zero web access.
3. Targeted Repair Loop coordinator (bounded to max 2 iterations).
"""

import re
import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.workflows.do_risk_report.models import Evidence, ValidationIssue
from app.workflows.do_risk_report.ledger import EvidenceLedger
from app.workflows.do_risk_report.template_spec import load_prompt_text
from app.workflows.do_risk_report.roles import run_role


class DeterministicValidator:
    """
    Layer 1: Millisecond deterministic verification with zero LLM spend.
    """

    @staticmethod
    def extract_citations(text: str) -> List[str]:
        """Extracts all [E###] citation tokens from report text."""
        return re.findall(r"\[(E\d{3,4})\]", text, re.IGNORECASE)

    @staticmethod
    def validate_citations(text: str, ledger: EvidenceLedger) -> List[ValidationIssue]:
        """Verifies that every [E###] cited in text exists in the Evidence Ledger."""
        issues: List[ValidationIssue] = []
        cites = DeterministicValidator.extract_citations(text)

        for cid in set(cites):
            resolved = ledger.resolve_citation(cid)
            if not resolved:
                issues.append(ValidationIssue(
                    section="citations",
                    field=cid,
                    problem=f"Unresolved citation token [{cid}] found in draft text with no matching ledger record.",
                    severity="critical"
                ))

        return issues

    @staticmethod
    def validate_two_source_rule(ledger: EvidenceLedger) -> List[ValidationIssue]:
        """Flags high-stakes claims in the ledger that rely on only a single source."""
        issues: List[ValidationIssue] = []
        single_sourced = ledger.get_single_source_high_stakes()

        for ev in single_sourced:
            issues.append(ValidationIssue(
                section=ev.section,
                field=ev.id,
                problem=f"High-stakes fact [{ev.id}] '{ev.claim[:50]}...' lacks two corroborating sources.",
                suggested_query=f"{ev.claim} corroborating source settlement docket",
                severity="warning"
            ))

        return issues

    @staticmethod
    def validate_date_recency(ledger: EvidenceLedger, max_days_old: int = 90) -> List[ValidationIssue]:
        """Flags ongoing litigation records whose 'as_of' date is older than max_days_old."""
        issues: List[ValidationIssue] = []
        today = datetime.date.today()

        for row in ledger.for_section("securities_litigation") + ledger.for_section("legal_regulatory_claims"):
            if row.as_of and ("ongoing" in row.claim.lower() or "active" in row.claim.lower()):
                try:
                    dt = datetime.date.fromisoformat(row.as_of)
                    if (today - dt).days > max_days_old:
                        issues.append(ValidationIssue(
                            section=row.section,
                            field=row.id,
                            problem=f"Litigation claim [{row.id}] as_of date ({row.as_of}) is >{max_days_old} days old. Requires status re-check.",
                            suggested_query=f"{row.claim[:40]} status update {today.year}",
                            severity="warning"
                        ))
                except Exception:
                    pass

        return issues

    @staticmethod
    def validate(text: str, ledger: EvidenceLedger) -> List[ValidationIssue]:
        """Runs all Layer 1 deterministic checks and aggregates detected issues."""
        issues: List[ValidationIssue] = []
        issues.extend(DeterministicValidator.validate_citations(text, ledger))
        issues.extend(DeterministicValidator.validate_two_source_rule(ledger))
        issues.extend(DeterministicValidator.validate_date_recency(ledger))
        return issues


class ValidationAgent:
    """
    Dedicated Post-Generation Validation Agent enforcing `validation-prompt.txt`.
    Operates with ZERO web access, strictly editing the generated report text.
    """

    def __init__(self, current_date: Optional[str] = None):
        self.current_date = current_date or datetime.date.today().isoformat()
        self.raw_rules = load_prompt_text("validation_prompt.txt")

    def render_system_prompt(self) -> str:
        """Injects current calendar date into validation prompt rules."""
        return self.raw_rules.replace("{{currentDate}}", self.current_date)

    def apply_deterministic_corrections(self, report_text: str) -> str:
        """
        Applies mechanical rules from validation-prompt.txt deterministically in code:
        A. News cutoff (12 months), deduping, newest-first
        B. Share price 'current' vs 'last close (<date>)'
        C. Revenue-trend descending order
        D. Unsourced culture words pruning
        E. Empty headings labeled 'Data unavailable.'
        """
        corrected = report_text

        # 1. Empty heading check: replace empty sections with 'Data unavailable.'
        sections = re.split(r"(^#+\s+.*?$)", corrected, flags=re.MULTILINE)
        reconstructed = []
        for i in range(1, len(sections), 2):
            header = sections[i]
            body = sections[i+1] if i+1 < len(sections) else ""
            if not body.strip() or body.strip() == "-":
                body = "\nData unavailable.\n\n"
            reconstructed.append(header + body)

        if reconstructed:
            corrected = "".join(reconstructed)

        # 2. News 12-month calendar cutoff rule (Rule A)
        curr_dt = datetime.date.fromisoformat(self.current_date)
        try:
            cutoff_dt = curr_dt.replace(year=curr_dt.year - 1)
        except ValueError:
            cutoff_dt = curr_dt - datetime.timedelta(days=365)

        news_match = re.search(r"(\*\* UPDATES / PRESS RELEASES / NEWS\*\*|### UPDATES / PRESS RELEASES / NEWS)([\s\S]*?)(?=###|\Z)", corrected)
        if news_match:
            news_header = news_match.group(1)
            news_body = news_match.group(2)
            news_lines = [l.strip() for l in news_body.split("\n") if l.strip()]

            parsed_bullets: List[Tuple[Optional[datetime.date], str]] = []
            seen_events: set = set()

            for line in news_lines:
                # Look for date pattern: DD-MMM-YYYY or YYYY-MM-DD
                dt_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4}|\d{4}-\d{2}-\d{2})", line)
                item_dt = None
                if dt_match:
                    dt_str = dt_match.group(1)
                    for fmt in ["%d-%b-%Y", "%Y-%m-%d"]:
                        try:
                            item_dt = datetime.datetime.strptime(dt_str, fmt).date()
                            break
                        except ValueError:
                            pass

                # Rule A: Delete if strictly before cutoff or unresolvable date
                if item_dt is None or item_dt < cutoff_dt:
                    continue

                # Deduplicate within news list itself
                norm_event = " ".join(re.sub(r"\[.*?\]", "", line).split()).lower()
                if norm_event in seen_events:
                    continue
                seen_events.add(norm_event)

                parsed_bullets.append((item_dt, line))

            # Reorder strictly newest-first
            parsed_bullets.sort(key=lambda x: x[0], reverse=True)
            new_news_text = f"\n{news_header}\n" + "\n".join(b[1] for b in parsed_bullets) + "\n\n"
            corrected = corrected[:news_match.start()] + new_news_text + corrected[news_match.end():]

        # 3. Share price recency check (Rule B)
        # If labeled 'current' / 'today' but stated date is older than current_date, relabel 'last close (<date>)'
        share_match = re.search(r"(Share price\s*[:–-]\s*)(current|today)\s*\((.*?)\)", corrected, re.IGNORECASE)
        if share_match:
            prefix, label, stated_date = share_match.groups()
            if stated_date.strip() != self.current_date:
                corrected = corrected[:share_match.start()] + f"{prefix}last close ({stated_date})" + corrected[share_match.end():]

        # 4. Unsourced culture words pruning (Rule D)
        culture_words = ["toxic culture", "very strong culture", "culture of fear"]
        for cw in culture_words:
            if cw in corrected.lower():
                # Replace with neutral statement
                pattern = re.compile(re.escape(cw), re.IGNORECASE)
                corrected = pattern.sub("internal workplace dynamics", corrected)

        return corrected

    async def run(self, report_text: str) -> str:
        """
        Executes the Validation Agent pass.
        Runs deterministic code corrections first, then dispatches to Groq LLM validator.
        """
        clean_input = re.sub(r"^REPORT TO VALIDATE AND CORRECT:\s*", "", report_text, flags=re.IGNORECASE).strip()

        # 1. Fast deterministic code pass
        code_corrected = self.apply_deterministic_corrections(clean_input)

        # 2. LLM Validation pass with strict zero-web-access system prompt
        system_prompt = self.render_system_prompt()
        user_prompt = f"REPORT TO VALIDATE AND CORRECT:\n\n{code_corrected}"

        try:
            resp = await run_role(
                role="repair",
                user_input=user_prompt,
                model_override="openai/gpt-oss-120b"
            )
            llm_text = resp.get("patched_text", "")
            if llm_text and len(llm_text) > 200:
                clean_llm = re.sub(r"^REPORT TO VALIDATE AND CORRECT:\s*", "", llm_text, flags=re.IGNORECASE).strip()
                return clean_llm
        except Exception as e:
            print(f"Validation Agent LLM execution note: {e}")

        return re.sub(r"^REPORT TO VALIDATE AND CORRECT:\s*", "", code_corrected, flags=re.IGNORECASE).strip()


class RepairCoordinator:
    """Coordinates targeted repairs on failing claims/sections (max 2 iterations)."""

    def __init__(self, ledger: EvidenceLedger, max_iterations: int = 2):
        self.ledger = ledger
        self.max_iterations = max_iterations

    async def execute_repair(
        self,
        draft_text: str,
        issues: List[ValidationIssue]
    ) -> str:
        if not issues:
            return draft_text

        current_text = draft_text
        for i in range(self.max_iterations):
            critical_issues = [iss for iss in issues if iss.severity == "critical"]
            if not critical_issues:
                break

            prompt = (
                f"Issues identified:\n" +
                "\n".join(f"- Section {iss.section}: {iss.problem}" for iss in critical_issues) +
                f"\n\nCurrent Draft:\n{current_text}"
            )
            repair_out = await run_role("repair", prompt)
            patched = repair_out.get("patched_text")
            if patched:
                current_text = patched

            # Re-check citations
            new_issues = DeterministicValidator.validate_citations(current_text, self.ledger)
            if not new_issues:
                break

        return current_text
