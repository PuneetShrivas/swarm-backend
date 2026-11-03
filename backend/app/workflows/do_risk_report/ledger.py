import json
import threading
from typing import List, Dict, Optional, Any, Set, Tuple
from app.workflows.do_risk_report.models import Evidence


class EvidenceLedger:
    """
    Evidence Ledger: The single data bus for the D&O Risk Report pipeline.
    
    Principles:
    1. Raw search text is consumed once (by Extract) and never passed downstream.
    2. Every downstream stage reads typed, section-scoped ledger rows.
    3. Drafts cite evidence solely by ID (e.g. `[E014]`).
    4. Deduplication is enforced on (normalized claim, normalized source_url).
    5. Thread-safe operations for concurrent section extractions.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._rows: List[Evidence] = []
        self._id_map: Dict[str, Evidence] = {}
        self._dedupe_set: Set[Tuple[str, str]] = set()
        self._counter: int = 1

    def _normalize(self, text: str) -> str:
        return " ".join(text.strip().lower().split())

    def _generate_id(self) -> str:
        new_id = f"E{self._counter:03d}"
        self._counter += 1
        return new_id

    def add(self, items: List[Evidence]) -> int:
        """
        Adds evidence items to the ledger with deduplication.
        Returns count of newly added rows.
        """
        added_count = 0
        with self._lock:
            for item in items:
                norm_claim = self._normalize(item.claim)
                norm_url = self._normalize(item.source_url)
                dedupe_key = (norm_claim, norm_url)

                if dedupe_key in self._dedupe_set:
                    continue

                # Ensure valid sequential ID if missing or colliding
                if not item.id or item.id in self._id_map:
                    item.id = self._generate_id()
                else:
                    # Sync counter if external ID has higher sequence number
                    if item.id.startswith("E") and item.id[1:].isdigit():
                        seq = int(item.id[1:])
                        if seq >= self._counter:
                            self._counter = seq + 1

                self._rows.append(item)
                self._id_map[item.id] = item
                self._dedupe_set.add(dedupe_key)
                added_count += 1

        return added_count

    def for_section(self, section: str) -> List[Evidence]:
        """Returns all evidence rows allocated to a specific section."""
        with self._lock:
            return [row for row in self._rows if row.section.lower() == section.lower()]

    def resolve_citation(self, cite_id: str) -> Optional[Evidence]:
        """Resolves an [E###] citation token to its Evidence record."""
        clean_id = cite_id.strip("[]").upper()
        with self._lock:
            return self._id_map.get(clean_id)

    def all_rows(self) -> List[Evidence]:
        """Returns a snapshot copy of all evidence rows in the ledger."""
        with self._lock:
            return list(self._rows)

    def check_two_source_rule(self, claim: str) -> bool:
        """
        Checks whether at least two distinct source URLs corroborate a factual claim.
        Used for high-stakes facts like settlements, case outcomes, and restatements.
        """
        norm_target = self._normalize(claim)
        matching_sources: Set[str] = set()

        with self._lock:
            for row in self._rows:
                if row.status == "found" and norm_target in self._normalize(row.claim):
                    matching_sources.add(self._normalize(row.source_url))

        return len(matching_sources) >= 2

    def get_low_confidence_or_unresolved(self) -> List[Evidence]:
        """Filters rows flagged as low confidence or 'not_found' for the limitations appendix."""
        with self._lock:
            return [
                row for row in self._rows
                if row.confidence == "low" or row.status == "not_found"
            ]

    def get_single_source_high_stakes(self) -> List[Evidence]:
        """Identifies high-stakes litigation/regulatory items supported by only 1 source."""
        high_stakes_sections = {"securities_litigation", "legal_regulatory_claims", "financial_reporting"}
        with self._lock:
            high_stakes_rows = [
                row for row in self._rows
                if row.section.lower() in high_stakes_sections and row.status == "found"
            ]

        single_sourced: List[Evidence] = []
        for row in high_stakes_rows:
            if not self.check_two_source_rule(row.claim):
                single_sourced.append(row)

        return single_sourced

    def to_jsonl(self, filepath: str) -> int:
        """Saves all evidence rows to a JSONL file on disk for stage checkpointing."""
        with self._lock:
            rows_copy = list(self._rows)

        with open(filepath, "w", encoding="utf-8") as f:
            for row in rows_copy:
                f.write(row.model_dump_json() + "\n")

        return len(rows_copy)

    def from_jsonl(self, filepath: str) -> int:
        """Loads evidence rows from a JSONL file on disk."""
        loaded_items: List[Evidence] = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    loaded_items.append(Evidence(**data))

        return self.add(loaded_items)

    def stats(self) -> Dict[str, Any]:
        """Returns statistical telemetry on collected evidence."""
        with self._lock:
            sections: Dict[str, int] = {}
            source_types: Dict[str, int] = {}
            confidence_counts: Dict[str, int] = {"high": 0, "med": 0, "low": 0}
            status_counts: Dict[str, int] = {"found": 0, "not_found": 0}

            for r in self._rows:
                sections[r.section] = sections.get(r.section, 0) + 1
                source_types[r.source_type] = source_types.get(r.source_type, 0) + 1
                confidence_counts[r.confidence] = confidence_counts.get(r.confidence, 0) + 1
                status_counts[r.status] = status_counts.get(r.status, 0) + 1

            return {
                "total_rows": len(self._rows),
                "sections": sections,
                "source_types": source_types,
                "confidence": confidence_counts,
                "status": status_counts,
            }
