"""Perplexity Web Search Agent & Result Compactor for Standalone Agnostic Research.

Handles real-time web retrieval via Perplexity Search API endpoint (https://api.perplexity.ai/search),
snippet compaction, deduplication of syndicated news, disk-backed query hash caching,
and granular latency metrics with zero external project dependencies.
"""

import os
import re
import json
import time
import hashlib
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import httpx

from agnostic_workflow.config import config


CACHE_DIR = config.DEFAULT_CACHE_DIR
DEFAULT_PERPLEXITY_TIMEOUT = float(os.environ.get("PERPLEXITY_TIMEOUT_SECONDS", "60.0"))


async def async_search_via_perplexity_search_api(
    query: Union[str, List[str]],
    api_key: str,
    max_results: int = 10,
    search_context_size: str = "high",
    timeout: float = 20.0,
    max_retries: int = 4,
) -> Optional[Dict[str, Any]]:
    """Asynchronous search via Perplexity's raw Search API endpoint with exponential backoff."""
    if not api_key or not api_key.strip():
        return None

    if isinstance(query, (list, tuple)):
        query_payload = [str(q).strip() for q in query if str(q).strip()]
        if not query_payload:
            return None
        query_payload = query_payload[:50]
    else:
        query_str = str(query).strip()
        if not query_str:
            return None
        query_payload = query_str

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query_payload,
        "max_results": max(1, min(max_results, 20)),
        "search_context_size": search_context_size,
    }

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{config.PERPLEXITY_BASE_URL.rstrip('/')}/search",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    raw_results = data.get("results", [])
                    formatted_results = []
                    sources = []
                    for item in raw_results:
                        url = item.get("url", "")
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        date = item.get("date") or item.get("last_updated") or ""
                        domain = urlparse(url).netloc if url else ""
                        formatted_results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet,
                            "date": date,
                            "domain": domain,
                        })
                        if url:
                            sources.append(url)

                    return {
                        "query": query,
                        "provider": "perplexity_search_api",
                        "results_count": len(formatted_results),
                        "results": formatted_results,
                        "sources": sources[:max_results],
                        "status": "completed",
                    }
                elif resp.status_code == 429:
                    delay = 2.0 * (attempt + 1)
                    await asyncio.sleep(delay)
                else:
                    delay = 1.0 * (attempt + 1)
                    await asyncio.sleep(delay)
        except Exception:
            if attempt == max_retries - 1:
                break
            await asyncio.sleep(1.5 * (attempt + 1))
    return None


class ResultCompactor:
    """Strips boilerplate, caps characters, and deduplicates syndicated news wire releases."""

    @staticmethod
    def clean_snippet(text: str, max_chars: int = 1500) -> str:
        if not text:
            return ""
        # Remove markdown image tags and link anchors
        cleaned = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        cleaned = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", cleaned)
        cleaned = " ".join(cleaned.split())
        if len(cleaned) > max_chars:
            cutoff = cleaned[:max_chars].rfind(" ")
            cleaned = cleaned[:cutoff] + "..." if cutoff > 0 else cleaned[:max_chars] + "..."
        return cleaned

    @staticmethod
    def deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicates syndicated press releases or identical articles across different domains."""
        seen_titles: Set[str] = set()
        seen_snippets: Set[str] = set()
        deduped: List[Dict[str, Any]] = []

        for item in results:
            title = item.get("title", "").strip().lower()
            snippet = item.get("snippet", "").strip().lower()

            # Clean wire prefixes from title
            cleaned_title = re.sub(
                r"^(?:pr\s*newswire|business\s*wire|globe\s*newswire|accesswire|reuters|bloomberg)\s*[:\-–]\s*",
                "",
                title,
            )
            title_words = "".join(c for c in cleaned_title if c.isalnum())
            snippet_prefix = "".join(c for c in snippet[:100] if c.isalnum())

            # Match on normalized title or long identical snippet prefix
            if title_words and title_words in seen_titles:
                continue
            if len(snippet_prefix) >= 30 and snippet_prefix in seen_snippets:
                continue

            if title_words:
                seen_titles.add(title_words)
            if len(snippet_prefix) >= 30:
                seen_snippets.add(snippet_prefix)
            deduped.append(item)

        return deduped


class PerplexitySearchQueue:
    """Async search queue for Perplexity Search API with caching and concurrency limiting."""

    def __init__(self, cache_dir: Optional[str] = None, max_concurrency: int = 3):
        self.cache_dir = cache_dir or CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self.semaphore = asyncio.Semaphore(max_concurrency)

    def _get_cache_key(self, query: Union[str, List[str]], domains: Optional[List[str]] = None, recency: Optional[str] = None, is_mock: bool = False) -> str:
        mode_prefix = "mock" if is_mock else "live"
        query_repr = tuple(query) if isinstance(query, (list, tuple)) else query
        raw = f"{mode_prefix}|{query_repr}|{sorted(domains or [])}|{recency or ''}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _read_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
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
        """Executes a single or batch search query against Perplexity Search API or returns cached results."""
        api_key = (os.environ.get("PERPLEXITY_API_KEY") or config.PERPLEXITY_API_KEY).strip()
        is_test_env = os.environ.get("TESTING") == "true" or os.environ.get("MOCK_PERPLEXITY") == "true"
        allow_mock = is_test_env and (not api_key or os.environ.get("ALLOW_MOCK_DATA") == "true" or os.environ.get("MOCK_PERPLEXITY") == "true")

        if not allow_mock and (not api_key or api_key.startswith("your-") or api_key.startswith("test-")):
            raise RuntimeError(
                "PERPLEXITY_API_KEY is not configured or invalid. "
                "Live research report generation requires authentic web search; mock data insertion is strictly disabled."
            )

        is_mock = allow_mock and (not api_key or api_key.startswith("your-") or api_key.startswith("test-") or os.environ.get("MOCK_PERPLEXITY") == "true")

        cache_key = self._get_cache_key(query, domains, recency, is_mock=is_mock)
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        if is_mock:
            first_q = query[0] if isinstance(query, list) and query else (query if isinstance(query, str) else "")
            results = self._generate_mock_results(first_q, domains)
            self._write_cache(cache_key, results)
            return results

        async with self.semaphore:
            results = await self._execute_live_search(query, domains, recency, max_results, api_key)
            if results:
                self._write_cache(cache_key, results)
            return results

    async def _execute_live_search(
        self,
        query: Union[str, List[str]],
        domains: Optional[List[str]],
        recency: Optional[str],
        max_results: int,
        api_key: str,
    ) -> List[Dict[str, Any]]:
        search_res = await async_search_via_perplexity_search_api(
            query=query,
            api_key=api_key,
            max_results=max_results,
            search_context_size="high",
            timeout=DEFAULT_PERPLEXITY_TIMEOUT,
            max_retries=3,
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
        }

    def _generate_mock_results(self, query: str, domains: Optional[List[str]]) -> List[Dict[str, Any]]:
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
