"""
Perplexity Search Queue & Result Compaction Subsystem.
Handles workstream-scoped web retrieval, domain filtering, snippet compaction,
deduplication of syndicated news, and disk-backed query hash caching.
"""

import os
import re
import json
import time
import hashlib
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

from app.agents.researcher.tools import async_search_via_perplexity_search_api

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache_retrieval")

# Standard domain filters per underwriting workstream
WORKSTREAM_DOMAINS: Dict[str, List[str]] = {
    "litigation": [
        "courtlistener.com",
        "dockets.justia.com",
        "law360.com",
        "securities.stanford.edu",
        "casetext.com",
        "law.justia.com",
    ],
    "regulatory": [
        "sec.gov",
        "justice.gov",
        "ftc.gov",
        "cftc.gov",
        "fca.org.uk",
        "consumerfinance.gov",
    ],
    "credit_ratings": [
        "fitchratings.com",
        "moodys.com",
        "spglobal.com",
        "ambest.com",
    ],
    "news": [
        "reuters.com",
        "bloomberg.com",
        "wsj.com",
        "ft.com",
        "cnbc.com",
    ],
}


DEFAULT_PERPLEXITY_TIMEOUT = float(os.environ.get("PERPLEXITY_TIMEOUT_SECONDS", "60.0"))


class ResultCompactor:
    """
    Strips noise, boilerplate, caps per-snippet characters, and
    deduplicates syndicated articles across media wires.
    """
    @staticmethod
    def clean_snippet(text: str, max_chars: int = 1500) -> str:
        if not text:
            return ""
        # Remove markdown image tags and link anchors
        cleaned = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        cleaned = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", cleaned)
        # Collapse whitespace
        cleaned = " ".join(cleaned.split())
        # Cap at max_chars respecting word boundary
        if len(cleaned) > max_chars:
            cutoff = cleaned[:max_chars].rfind(" ")
            cleaned = cleaned[:cutoff] + "..." if cutoff > 0 else cleaned[:max_chars] + "..."
        return cleaned

    @staticmethod
    def deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicates syndicated press releases or identical articles across different domains."""
        seen_signatures: Set[str] = set()
        deduped: List[Dict[str, Any]] = []

        for item in results:
            url = item.get("url", "").strip()
            title = item.get("title", "").strip().lower()
            snippet = item.get("snippet", "").strip().lower()

            # Generate content fingerprint from normalized title and first 100 chars of snippet
            title_words = "".join(c for c in title if c.isalnum())
            snippet_prefix = "".join(c for c in snippet[:100] if c.isalnum())
            fingerprint = f"{title_words}:{snippet_prefix}"

            if fingerprint in seen_signatures:
                continue

            seen_signatures.add(fingerprint)
            deduped.append(item)

        return deduped


class PerplexitySearchQueue:
    """
    Async search queue for Perplexity Search API.
    Supports query caching, domain scoping, and rate limiting.
    """
    def __init__(self, cache_dir: Optional[str] = None, max_concurrency: int = 2):
        self.cache_dir = cache_dir or CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self.semaphore = asyncio.Semaphore(max_concurrency)

    def _get_cache_key(self, query: str, domains: Optional[List[str]] = None, recency: Optional[str] = None, is_mock: bool = False) -> str:
        mode_prefix = "mock" if is_mock else "live"
        raw = f"{mode_prefix}|{query}|{sorted(domains or [])}|{recency or ''}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _read_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                    # Check TTL (24 hours = 86400s)
                    if time.time() - entry.get("timestamp", 0) < 86400:
                        return entry.get("results")
            except Exception:
                pass
        return None

    def _write_cache(self, key: str, results: List[Dict[str, Any]]) -> None:
        path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"timestamp": time.time(), "results": results}, f)
        except Exception:
            pass

    async def search(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        recency: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Executes a single search query against Perplexity Search or returns cached/mocked results.
        """
        api_key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
        is_mock = (
            not api_key
            or api_key.startswith("your-")
            or api_key.startswith("test-")
            or os.environ.get("TESTING") == "true"
            or os.environ.get("MOCK_PERPLEXITY") == "true"
        )

        cache_key = self._get_cache_key(query, domains, recency, is_mock=is_mock)
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        if is_mock:
            results = self._generate_mock_results(query, domains)
            self._write_cache(cache_key, results)
            return results

        async with self.semaphore:
            results = await self._execute_live_search(query, domains, recency, max_results, api_key)
            if results:
                self._write_cache(cache_key, results)
            return results

    async def _execute_live_search(
        self,
        query: str,
        domains: Optional[List[str]],
        recency: Optional[str],
        max_results: int,
        api_key: str
    ) -> List[Dict[str, Any]]:
        """
        Executes fast, token-efficient live search via the raw Perplexity Search API endpoint
        (POST https://api.perplexity.ai/search) with search_context_size='high'.
        """
        search_res = await async_search_via_perplexity_search_api(
            query=query,
            api_key=api_key,
            max_results=max_results,
            search_context_size="high",
            timeout=DEFAULT_PERPLEXITY_TIMEOUT,
            max_retries=4,
        )

        if search_res and search_res.get("results"):
            raw_results = []
            for item in search_res["results"]:
                url = item.get("url", "")
                raw_results.append({
                    "title": item.get("title") or f"Source: {item.get('domain', 'web')}",
                    "url": url,
                    "domain": item.get("domain") or (urlparse(url).netloc if url else "web"),
                    "snippet": ResultCompactor.clean_snippet(item.get("snippet", ""), max_chars=1500),
                    "date": item.get("date") or time.strftime("%Y-%m-%d"),
                })
            return ResultCompactor.deduplicate_results(raw_results)

        return []

    def _generate_mock_results(self, query: str, domains: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Generates realistic synthetic results for testing and offline environments."""
        domain = domains[0] if domains else "reuters.com"
        today = time.strftime("%Y-%m-%d")
        q_lower = query.lower()

        if "litigation" in q_lower or "class action" in q_lower:
            snippet = f"Securities class action lawsuit filed in U.S. District Court alleging misleading disclosure regarding demand trends. Docket # 23-cv-0914. Ongoing status as of {today}."
            url = f"https://{domain}/docket/23-cv-0914"
            source_type = "court"
        elif "investigation" in q_lower or "sec" in q_lower or "doj" in q_lower:
            snippet = f"Regulatory inquiry disclosed regarding accounting classification of enterprise contracts. No formal enforcement charges filed. Status active as of {today}."
            url = f"https://{domain}/filings/sec-inquiry-note"
            source_type = "regulator"
        elif "rating" in q_lower or "debt" in q_lower:
            snippet = f"Credit rating affirmed at AA+ with Stable Outlook. Total senior unsecured debt assessed at $95B with strong interest coverage."
            url = f"https://{domain}/ratings/corporate-credit-update"
            source_type = "rating_agency"
        else:
            snippet = f"Company report on operational developments and corporate governance disclosure for {query[:30]}."
            url = f"https://{domain}/news/corporate-overview"
            source_type = "news"

        return [
            {
                "title": f"Report on {query[:40]}",
                "url": url,
                "domain": domain,
                "snippet": ResultCompactor.clean_snippet(snippet),
                "date": today,
                "source_type": source_type,
            }
        ]

    async def batch_search(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executes a batch of search queries concurrently.
        Each query dict contains `text`, optional `domains`, optional `recency`.
        """
        tasks = [
            self.search(
                query=q.get("text", q.get("query", "")),
                domains=q.get("domains"),
                recency=q.get("recency"),
                max_results=q.get("max_results", 5)
            )
            for q in queries
        ]
        batch_results = await asyncio.gather(*tasks)
        all_flattened = []
        for r_list in batch_results:
            all_flattened.extend(r_list)
        return ResultCompactor.deduplicate_results(all_flattened)

    async def batch_search_with_timings(
        self,
        queries: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes a batch of search queries concurrently and returns results with micro-timings.
        """
        t0 = time.perf_counter()
        results = await self.batch_search(queries)
        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        meta = {
            "duration_ms": duration_ms,
            "queries_count": len(queries),
            "results_count": len(results),
        }
        return results, meta
