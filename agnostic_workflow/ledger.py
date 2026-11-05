"""Domain-Agnostic Evidence Ledger.

Sequentially indexes, stores, and resolves verifiable claims with source citations.
Thread-safe and completely self-contained.
"""

import threading
from typing import List, Dict, Any, Optional

from agnostic_workflow.models import AgnosticEvidence


class AgnosticEvidenceLedger:
    """Thread-safe evidence ledger storing atomic facts with sequential [E###] citation IDs."""

    def __init__(self):
        self._lock = threading.Lock()
        self._items: List[AgnosticEvidence] = []
        self._by_id: Dict[str, AgnosticEvidence] = {}
        self._counter = 1

    def add(self, items: List[AgnosticEvidence]) -> List[AgnosticEvidence]:
        """Assigns sequential IDs (E001, E002, ...) and adds items to ledger."""
        with self._lock:
            added = []
            for item in items:
                if not item.id:
                    item.id = f"E{self._counter:03d}"
                    self._counter += 1
                self._items.append(item)
                self._by_id[item.id.upper()] = item
                added.append(item)
            return added

    def all(self) -> List[AgnosticEvidence]:
        """Returns all evidence items."""
        with self._lock:
            return list(self._items)

    def for_section(self, section_slug: str) -> List[AgnosticEvidence]:
        """Returns evidence items assigned to a specific section slug."""
        target = section_slug.lower().strip()
        with self._lock:
            return [ev for ev in self._items if ev.section_slug.lower() == target]

    def resolve_citation(self, citation_id: str) -> Optional[AgnosticEvidence]:
        """Resolves an [E###] citation token to its evidence item."""
        with self._lock:
            return self._by_id.get(citation_id.upper().strip("[]"))

    def stats(self) -> Dict[str, Any]:
        """Calculates summary statistics of collected evidence."""
        with self._lock:
            total = len(self._items)
            sections: Dict[str, int] = {}
            domains: Dict[str, int] = {}
            high_conf = 0

            for ev in self._items:
                sections[ev.section_slug] = sections.get(ev.section_slug, 0) + 1
                if ev.source_domain:
                    domains[ev.source_domain] = domains.get(ev.source_domain, 0) + 1
                if ev.confidence.lower() == "high":
                    high_conf += 1

            return {
                "total_evidence_count": total,
                "sections_covered": len(sections),
                "unique_domains_count": len(domains),
                "high_confidence_count": high_conf,
                "section_breakdown": sections,
                "top_domains": sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5],
            }

    def to_dict(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [ev.to_dict() for ev in self._items]
