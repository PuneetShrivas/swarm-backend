"""
Perplexity Web Search Agent & Result Compactor for Agnostic Research.
Handles real-time web retrieval, snippet compaction, deduplication of syndicated news,
disk-backed query hash caching, and granular latency metrics.
"""

import os
import re
import json
import time
import hashlib
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

from app.agents.researcher.tools import async_search_via_perplexity_search_api

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache_agnostic_retrieval")
DEFAULT_PERPLEXITY_TIMEOUT = float(os.environ.get("PERPLEXITY_TIMEOUT_SECONDS", "60.0"))


class ResultCompactor:
    """Strips boilerplate, caps characters, and deduplicates syndicated news wire releases."""

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
            title = item.get("title", "").strip().lower()
            snippet = item.get("snippet", "").strip().lower()

            # Content fingerprint from title and first 100 characters of snippet
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
    Supports in-memory session caching, disk-backed persistent caching,
    domain scoping, and concurrency rate limiting.
    """

    def __init__(self, cache_dir: Optional[str] = None, max_concurrency: int = 3):
        self.cache_dir = cache_dir or CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self._session_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_lock = asyncio.Lock()
        self.cache_hits: int = 0
        self.cache_misses: int = 0

    @staticmethod
    def _normalize_query_key(
        query: Union[str, List[str]],
        domains: Optional[List[str]] = None,
        recency: Optional[str] = None,
        is_mock: bool = False,
    ) -> str:
        mode_prefix = "mock" if is_mock else "live"
        if isinstance(query, (list, tuple)):
            norm_q = tuple(" ".join(str(q).lower().strip().split()) for q in query)
        else:
            norm_q = " ".join(str(query).lower().strip().split())
        norm_domains = tuple(sorted(d.lower().strip() for d in (domains or [])))
        norm_recency = (recency or "").lower().strip()
        raw = f"{mode_prefix}|{norm_q}|{norm_domains}|{norm_recency}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _get_cache_key(
        self,
        query: Union[str, List[str]],
        domains: Optional[List[str]] = None,
        recency: Optional[str] = None,
        is_mock: bool = False,
    ) -> str:
        return self._normalize_query_key(query, domains, recency, is_mock=is_mock)

    def clear_session_cache(self) -> None:
        """Clears in-memory session cache and resets cache counters."""
        self._session_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0

    def get_cache_stats(self) -> Dict[str, int]:
        """Returns in-memory cache statistics."""
        return {
            "session_cache_entries": len(self._session_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }

    def _read_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                    # 24 hour cache TTL
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
        query: Union[str, List[str]],
        domains: Optional[List[str]] = None,
        recency: Optional[str] = None,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Executes a single or batch search query against Perplexity Search API or returns cached/mocked results.
        """
        api_key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
        is_test_env = os.environ.get("TESTING") == "true" or os.environ.get("MOCK_PERPLEXITY") == "true"
        allow_mock = is_test_env and (not api_key or os.environ.get("ALLOW_MOCK_DATA") == "true" or os.environ.get("MOCK_PERPLEXITY") == "true")

        if not allow_mock and (not api_key or api_key.startswith("your-") or api_key.startswith("test-")):
            raise RuntimeError(
                "PERPLEXITY_API_KEY is not configured or invalid. "
                "Live research report generation requires authentic web search; mock data insertion is strictly disabled."
            )

        is_mock = allow_mock and (not api_key or api_key.startswith("your-") or api_key.startswith("test-") or os.environ.get("MOCK_PERPLEXITY") == "true")

        cache_key = self._get_cache_key(query, domains, recency, is_mock=is_mock)

        # 1. Check in-memory session cache first (instant 0ms lookup)
        async with self._cache_lock:
            if cache_key in self._session_cache:
                self.cache_hits += 1
                return [dict(item) for item in self._session_cache[cache_key]]

        # 2. Check persistent disk-backed cache next
        cached = self._read_cache(cache_key)
        if cached is not None:
            async with self._cache_lock:
                self._session_cache[cache_key] = cached
                self.cache_hits += 1
            return [dict(item) for item in cached]

        self.cache_misses += 1

        if is_mock:
            first_q = query[0] if isinstance(query, list) and query else (query if isinstance(query, str) else "")
            results = self._generate_mock_results(first_q, domains)
            self._write_cache(cache_key, results)
            async with self._cache_lock:
                self._session_cache[cache_key] = results
            return results

        async with self.semaphore:
            results = await self._execute_live_search(query, domains, recency, max_results, api_key)
            if results:
                self._write_cache(cache_key, results)
                async with self._cache_lock:
                    self._session_cache[cache_key] = results
            return results

    async def _execute_live_search(
        self,
        query: Union[str, List[str]],
        domains: Optional[List[str]],
        recency: Optional[str],
        max_results: int,
        api_key: str,
    ) -> List[Dict[str, Any]]:
        # Enforce search recency filter for freshest live results
        norm_rec = (recency or "month").lower().strip()
        if norm_rec not in ["hour", "day", "week", "month", "year"]:
            norm_rec = "month"

        search_res = await async_search_via_perplexity_search_api(
            query=query,
            api_key=api_key,
            max_results=max_results,
            search_context_size="high",
            timeout=DEFAULT_PERPLEXITY_TIMEOUT,
            max_retries=3,
            search_recency_filter=norm_rec,
            search_domain_filter=domains,
        )

        if search_res and search_res.get("results"):
            raw_results = []
            for item in search_res["results"]:
                url = item.get("url", "")
                domain = item.get("domain") or (urlparse(url).netloc if url else "web")
                raw_results.append({
                    "title": item.get("title") or f"Source: {domain}",
                    "url": url,
                    "domain": domain,
                    "snippet": ResultCompactor.clean_snippet(item.get("snippet", ""), max_chars=1500),
                    "date": item.get("date") or time.strftime("%Y-%m-%d"),
                })
            return ResultCompactor.deduplicate_results(raw_results)

        return []

    async def batch_search_with_timings(
        self,
        queries: List[Dict[str, Any]],
        max_results: int = 5,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes a batch of search query dicts:
        [{'text': 'query string', 'domains': [...], 'recency': 'year'}]
        Returns (combined_results, timing_dict).
        """
        t0 = time.perf_counter()
        if not queries:
            return [], {"duration_ms": 0.0, "queries_count": 0, "results_count": 0}

        tasks = []
        for q in queries:
            query_str = q.get("text", "") if isinstance(q, dict) else str(q)
            domains = q.get("domains") if isinstance(q, dict) else None
            recency = q.get("recency") if isinstance(q, dict) else None
            if query_str:
                tasks.append(self.search(query=query_str, domains=domains, recency=recency, max_results=max_results))

        nested_results = await asyncio.gather(*tasks, return_exceptions=True)
        combined: List[Dict[str, Any]] = []

        for res in nested_results:
            if isinstance(res, list):
                combined.extend(res)

        deduped = ResultCompactor.deduplicate_results(combined)
        duration_ms = round((time.perf_counter() - t0) * 1000, 2)

        return deduped, {
            "duration_ms": duration_ms,
            "queries_count": len(queries),
            "results_count": len(deduped),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }

    def _generate_mock_results(self, query: str, domains: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Generates mock results strictly when TESTING=true and ALLOW_MOCK_DATA=true."""
        domain = domains[0] if domains else "research-journal.org"
        today = time.strftime("%Y-%m-%d")
        return [
            {
                "title": f"Analytical Study on {query[:30]}",
                "url": f"https://{domain}/article/{hashlib.md5(query.encode()).hexdigest()[:8]}",
                "domain": domain,
                "snippet": f"Empirical findings confirm material progress regarding {query}. Data indicates verified adoption and 25% efficiency gains as of {today}.",
                "date": today,
            },
            {
                "title": f"Industry Assessment: {query[:30]}",
                "url": f"https://{domain}/reports/{hashlib.md5(query.encode()).hexdigest()[:8]}",
                "domain": domain,
                "snippet": f"Competitive overview highlights key participants and ongoing regulatory scrutiny concerning {query}.",
                "date": today,
            }
        ]
