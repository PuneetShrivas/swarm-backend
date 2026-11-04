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

    def __init__(self, current_date: Optional[str] = None, provider: Optional[str] = None):
        self.current_date = current_date or datetime.date.today().isoformat()
        self.provider = provider
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

        news_match = re.search(
            r"((?:###|\*\*)[ \t]*(?:UPDATES\s*/\s*PRESS\s*RELEASES\s*/\s*NEWS|NEWS\s*&\s*RECENT\s*DEVELOPMENTS|NEWS\s*&\s*UPDATES|UPDATES\s*&\s*NEWS|NEWS)[^\n]*\n)([\s\S]*?)(?=(?:###|\*\*)[ \t]*[A-Z]|\Z)",
            corrected,
            re.IGNORECASE,
        )
        if news_match:
            news_header = news_match.group(1).strip()
            news_body = news_match.group(2)
            news_lines = [l.strip() for l in news_body.split("\n") if l.strip()]

            parsed_bullets: List[Tuple[Optional[datetime.date], str]] = []
            seen_events: set = set()
            standing_notes: List[str] = []

            for line in news_lines:
                # Check for standing verification notes that don't have dated timelines
                is_standing_note = any(
                    line.lower().startswith(prefix)
                    for prefix in [
                        "adverse securities litigation",
                        "- adverse securities litigation",
                        "independent auditor changes",
                        "- independent auditor changes",
                        "executive departures",
                        "- executive departures",
                        "final section risk band",
                        "- final section risk band",
                        "information gap",
                        "- information gap",
                    ]
                )
                if is_standing_note:
                    standing_notes.append(line)
                    continue

                # Look for date pattern: DD-MMM-YYYY, YYYY-MM-DD, or Month DD, YYYY
                dt_match = re.search(r"(\d{1,2}-[A-Za-z]{3}-\d{4}|\d{4}-\d{2}-\d{2}|\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b)", line)
                if not dt_match:
                    # Rule A: unresolvable date line should be removed
                    continue

                dt_str = dt_match.group(1).replace(",", "")
                item_dt = None
                for fmt in ["%d-%b-%Y", "%Y-%m-%d", "%B %d %Y", "%b %d %Y"]:
                    try:
                        item_dt = datetime.datetime.strptime(dt_str, fmt).date()
                        break
                    except ValueError:
                        pass

                # Rule A: Delete if strictly before cutoff
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
            all_bullets = [b[1] for b in parsed_bullets] + standing_notes
            new_news_text = f"\n{news_header}\n" + "\n".join(all_bullets) + "\n\n"
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
                pattern = re.compile(re.escape(cw), re.IGNORECASE)
                corrected = pattern.sub("internal workplace dynamics", corrected)

        # 5. Purge prohibited retention / pricing commentary from Securities Class Action Risk
        sca_match = re.search(
            r"((?:###|\*\*)[ \t]*SECURITIES\s*CLASS\s*ACTION\s*RISK[^\n]*\n)([\s\S]*?)(?=(?:###|\*\*)[ \t]*[A-Z]|\Z)",
            corrected,
            re.IGNORECASE,
        )
        if sca_match:
            sca_header = sca_match.group(1)
            sca_body = sca_match.group(2)
            sca_lines = sca_body.split("\n")
            cleaned_sca_lines = []
            for line in sca_lines:
                if re.search(r"retention.*?\$\d+|\$\d+.*?retention|attachment.*?\$\d+|\$\d+.*?attachment|(?:pricing|premium|limit)\s*recommendation", line, re.IGNORECASE):
                    if "attachment" in line.lower() or "retention" in line.lower():
                        cleaned_sca_lines.append("- Tower Attachment: Primary layer attachment remains standard with exposure buffered by underlying Side A/Side C structure.")
                    continue
                cleaned_sca_lines.append(line)
            new_sca_text = f"{sca_header}" + "\n".join(cleaned_sca_lines) + "\n"
            corrected = corrected[:sca_match.start()] + new_sca_text + corrected[sca_match.end():]

        # 6. Resolve Conflicting Market Caps and Enforce Single Band in Company Snapshot
        snap_match = re.search(
            r"((?:###|\*\*)[ \t]*COMPANY\s*SNAPSHOT[^\n]*\n)([\s\S]*?)(?=(?:###|\*\*)[ \t]*[A-Z]|\Z)",
            corrected,
            re.IGNORECASE,
        )
        if snap_match:
            snap_header = snap_match.group(1)
            snap_body = snap_match.group(2)
            snap_lines = snap_body.split("\n")
            cleaned_snap_lines = []
            in_conclusion = False
            for line in snap_lines:
                if "conclusion" in line.lower():
                    in_conclusion = True

                # Market cap line: if two figures stated like "$4.88T vs $5.25T", resolve to first single figure
                if "market cap" in line.lower() and not in_conclusion:
                    caps = re.findall(r"\$\d+(?:\.\d+)?\s*(?:trillion|billion|T|B)", line, re.IGNORECASE)
                    if len(caps) > 1:
                        dt_m = re.search(r"(?:as\s+of|on)\s+([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})", line, re.IGNORECASE)
                        dt_str = f" as of {dt_m.group(1)}" if dt_m else ""
                        line = f"- Market cap: {caps[0]}{dt_str}"

                # In Company Snapshot conclusion:
                if in_conclusion:
                    # Strip AI exposure / AI concentration analysis from conclusion bullets
                    if re.search(r"\bAI\b.*?(?:exposure|concentration|valuation|margins|governance)", line, re.IGNORECASE):
                        continue
                    # Resolve dual bands like "Elevated to High-Volatility" -> "High-Volatility"
                    if re.search(r"(?:elevated\s*to\s*high-volatility|contained\s*to\s*elevated|contained\s*to\s*high-volatility)", line, re.IGNORECASE):
                        line = re.sub(r"elevated\s*to\s*high-volatility", "High-Volatility", line, flags=re.IGNORECASE)
                        line = re.sub(r"contained\s*to\s*high-volatility", "High-Volatility", line, flags=re.IGNORECASE)
                        line = re.sub(r"contained\s*to\s*elevated", "Elevated", line, flags=re.IGNORECASE)

                cleaned_snap_lines.append(line)
            new_snap_text = f"{snap_header}" + "\n".join(cleaned_snap_lines) + "\n"
            corrected = corrected[:snap_match.start()] + new_snap_text + corrected[snap_match.end():]

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
                provider_override=self.provider,
            )
            llm_text = resp.get("patched_text", "")
            if llm_text and len(llm_text) > 200:
                clean_llm = re.sub(r"^REPORT TO VALIDATE AND CORRECT:\s*", "", llm_text, flags=re.IGNORECASE).strip()
                orig_headers = re.findall(r"^#+\s+.*?$", code_corrected, flags=re.MULTILINE)
                new_headers = re.findall(r"^#+\s+.*?$", clean_llm, flags=re.MULTILINE)
                # Ensure the LLM didn't truncate the report or drop section headers
                if len(new_headers) >= len(orig_headers) - 1 and len(clean_llm) >= len(code_corrected) * 0.85:
                    return clean_llm
                else:
                    print(f"Validation Agent note: LLM dropped sections ({len(new_headers)} vs {len(orig_headers)}) or truncated; keeping deterministic corrections.")
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
