"""
tools/web_search.py
Web search tool using Tavily (primary) with DuckDuckGo as fallback.
Treats all returned content as UNTRUSTED input — sanitised before
passing to the LLM to mitigate prompt-injection from scraped content
(addressed per Section 9 of the assessment).
"""

import re
import time
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import TAVILY_API_KEY
from utils.logger import logger
from utils.cache import get_cached, set_cached


# ── Sanitisation ─────────────────────────────────────────────────────────────
_INJECTION_PATTERNS = [
    r"ignore (previous|all|above).*instructions?",
    r"you are now",
    r"act as",
    r"disregard",
    r"jailbreak",
    r"DAN mode",
    r"new system prompt",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def sanitise_text(text: str) -> str:
    """
    Strip potential prompt-injection patterns from scraped web content.
    This is a defence-in-depth measure; the LLM system prompt also
    instructs the model to treat retrieved content as external data only.
    """
    for pat in _COMPILED:
        text = pat.sub("[REDACTED]", text)
    # Truncate individual snippets so they can't fill the full context window
    return text[:4000]


# ── Tavily ───────────────────────────────────────────────────────────────────
def _tavily_search(query: str, max_results: int = 5) -> list[dict]:
    if not TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY not configured")
    from tavily import TavilyClient
    client = TavilyClient(api_key=TAVILY_API_KEY)
    resp = client.search(query=query, max_results=max_results, search_depth="advanced")
    results = []
    for r in resp.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "content": sanitise_text(r.get("content", "")),
            "url": r.get("url", ""),
            "score": r.get("score", 0.0),
            "source_type": "web",
        })
    return results


# ── DuckDuckGo fallback ───────────────────────────────────────────────────────
def _ddg_search(query: str, max_results: int = 5) -> list[dict]:
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "content": sanitise_text(r.get("body", "")),
                    "url": r.get("href", ""),
                    "score": 0.5,
                    "source_type": "web",
                })
        return results
    except Exception as exc:
        logger.warning(f"DuckDuckGo fallback failed: {exc}")
        return []


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=False,
)
def web_search(
    company: str,
    country: str,
    query_suffix: str = "",
    max_results: int = 5,
    use_cache: bool = True,
) -> list[dict]:
    """
    Search the web for information about a company.
    Returns a list of result dicts with keys: title, content, url, score, source_type.
    """
    cache_key = f"web_{query_suffix}"
    if use_cache:
        cached = get_cached(company, country, cache_key)
        if cached:
            return cached

    query = f"{company} {country} {query_suffix}".strip()
    logger.info(f"Web search: '{query}'")

    results: list[dict] = []
    if TAVILY_API_KEY:
        try:
            results = _tavily_search(query, max_results)
            logger.info(f"Tavily returned {len(results)} results")
        except Exception as exc:
            logger.warning(f"Tavily failed: {exc}. Trying DuckDuckGo…")
            results = _ddg_search(query, max_results)
    else:
        logger.warning("No TAVILY_API_KEY; using DuckDuckGo")
        results = _ddg_search(query, max_results)

    if use_cache and results:
        set_cached(company, country, cache_key, results)
    return results
