"""
tools/news_search.py
Fetches recent news using NewsAPI (primary) and Tavily news (fallback).
"""

from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import NEWS_API_KEY, TAVILY_API_KEY
from utils.logger import logger
from utils.cache import get_cached, set_cached
from tools.web_search import sanitise_text


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=False)
def _newsapi_search(company: str, country: str, max_results: int = 10) -> list[dict]:
    from newsapi import NewsApiClient
    client = NewsApiClient(api_key=NEWS_API_KEY)
    resp = client.get_everything(
        q=f'"{company}"',
        language="en",
        sort_by="publishedAt",
        page_size=max_results,
    )
    results = []
    for art in resp.get("articles", []):
        content = f"{art.get('title', '')}. {art.get('description', '')}. {art.get('content', '')}"
        results.append({
            "title": art.get("title", ""),
            "content": sanitise_text(content),
            "url": art.get("url", ""),
            "published_at": art.get("publishedAt", ""),
            "source": art.get("source", {}).get("name", ""),
            "score": 0.8,
            "source_type": "news",
        })
    return results


def _tavily_news(company: str, country: str, max_results: int = 5) -> list[dict]:
    if not TAVILY_API_KEY:
        return []
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=TAVILY_API_KEY)
        resp = client.search(
            query=f"{company} {country} latest news 2024 2025",
            max_results=max_results,
            topic="news",
        )
        results = []
        for r in resp.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "content": sanitise_text(r.get("content", "")),
                "url": r.get("url", ""),
                "published_at": r.get("published_date", ""),
                "source": "Tavily News",
                "score": r.get("score", 0.6),
                "source_type": "news",
            })
        return results
    except Exception as exc:
        logger.warning(f"Tavily news fallback failed: {exc}")
        return []


def news_search(
    company: str,
    country: str,
    max_results: int = 10,
    use_cache: bool = True,
) -> list[dict]:
    """
    Return recent news articles about a company.
    Tries NewsAPI first; falls back to Tavily news topic search.
    """
    if use_cache:
        cached = get_cached(company, country, "news")
        if cached:
            return cached

    results: list[dict] = []

    if NEWS_API_KEY:
        try:
            results = _newsapi_search(company, country, max_results)
            logger.info(f"NewsAPI returned {len(results)} articles")
        except Exception as exc:
            logger.warning(f"NewsAPI failed: {exc}")

    if not results:
        logger.info("Falling back to Tavily news search")
        results = _tavily_news(company, country, max_results)

    if use_cache and results:
        set_cached(company, country, "news", results)
    return results
