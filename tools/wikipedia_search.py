"""
tools/wikipedia_search.py
Fetches company summary from Wikipedia, disambiguated using the
country to handle ambiguous names (Section 7 of the assessment).
"""

from tenacity import retry, stop_after_attempt, wait_exponential

from utils.logger import logger
from utils.cache import get_cached, set_cached
from tools.web_search import sanitise_text


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=False)
def wikipedia_search(
    company: str,
    country: str,
    sentences: int = 20,
    use_cache: bool = True,
) -> list[dict]:
    """
    Search Wikipedia for the company. Country used for disambiguation.
    Returns list with one item (or empty list on failure).
    """
    if use_cache:
        cached = get_cached(company, country, "wikipedia")
        if cached:
            return cached

    import wikipedia as wiki
    wiki.set_lang("en")

    results: list[dict] = []
    search_terms = [
        f"{company} {country}",
        company,
        f"{company} company",
    ]

    for term in search_terms:
        try:
            page = wiki.page(term, auto_suggest=True)
            content = sanitise_text(page.summary[:6000])
            results = [{
                "title": page.title,
                "content": content,
                "url": page.url,
                "score": 0.9,
                "source_type": "wikipedia",
            }]
            logger.info(f"Wikipedia: found '{page.title}' using query '{term}'")
            break
        except wiki.exceptions.DisambiguationError as e:
            # Try to pick the most relevant option using country/company context
            for option in e.options[:5]:
                if country.lower() in option.lower() or company.lower() in option.lower():
                    try:
                        page = wiki.page(option)
                        content = sanitise_text(page.summary[:6000])
                        results = [{
                            "title": page.title,
                            "content": content,
                            "url": page.url,
                            "score": 0.7,
                            "source_type": "wikipedia",
                        }]
                        logger.info(f"Wikipedia disambiguation resolved to '{page.title}'")
                        break
                    except Exception:
                        continue
            if results:
                break
        except wiki.exceptions.PageError:
            logger.debug(f"Wikipedia: no page for '{term}'")
            continue
        except Exception as exc:
            logger.warning(f"Wikipedia error for '{term}': {exc}")
            continue

    if not results:
        logger.warning(f"Wikipedia: no result found for '{company}' in '{country}'")

    if use_cache and results:
        set_cached(company, country, "wikipedia", results)
    return results
