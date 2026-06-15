"""
tools/financial_data.py
Fetches financial data for public companies via yfinance.
Degrades gracefully for private companies (Section 7 — minimal digital footprint).
"""

from tenacity import retry, stop_after_attempt, wait_exponential

from utils.logger import logger
from utils.cache import get_cached, set_cached


def _ticker_candidates(company: str, country: str) -> list[str]:
    """
    Generate likely ticker symbols. This is a heuristic;
    for a production system we'd query a symbol search API.
    """
    name = company.upper().replace(" ", "").replace(",", "").replace(".", "")[:6]
    return [name, name[:4], name[:3]]


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8), reraise=False)
def financial_search(
    company: str,
    country: str,
    use_cache: bool = True,
) -> list[dict]:
    """
    Try to retrieve financial snapshot from yfinance.
    Returns empty list if company is private or ticker not found.
    """
    if use_cache:
        cached = get_cached(company, country, "financial")
        if cached is not None:
            return cached

    try:
        import yfinance as yf

        results: list[dict] = []
        candidates = _ticker_candidates(company, country)

        for ticker_sym in candidates:
            try:
                ticker = yf.Ticker(ticker_sym)
                info = ticker.info

                # yfinance returns a dict with 'quoteType' if the ticker is valid
                if not info or info.get("quoteType") is None:
                    continue

                # Check the long name matches our target company (avoid false positives)
                long_name = info.get("longName", "").lower()
                if company.lower()[:5] not in long_name and long_name not in company.lower():
                    continue

                summary = {
                    "ticker": ticker_sym,
                    "title": f"{info.get('longName', company)} — Financial Overview",
                    "content": (
                        f"Company: {info.get('longName', company)}\n"
                        f"Sector: {info.get('sector', 'N/A')}\n"
                        f"Industry: {info.get('industry', 'N/A')}\n"
                        f"Country: {info.get('country', country)}\n"
                        f"Employees: {info.get('fullTimeEmployees', 'N/A')}\n"
                        f"Market Cap: {info.get('marketCap', 'N/A')}\n"
                        f"Revenue: {info.get('totalRevenue', 'N/A')}\n"
                        f"Website: {info.get('website', 'N/A')}\n"
                        f"Business Summary: {info.get('longBusinessSummary', 'N/A')[:1500]}\n"
                    ),
                    "url": info.get("website", f"https://finance.yahoo.com/quote/{ticker_sym}"),
                    "score": 0.85,
                    "source_type": "yfinance",
                }
                results.append(summary)
                logger.info(f"yfinance: found data for ticker '{ticker_sym}'")
                break
            except Exception:
                continue

        if not results:
            logger.info(f"yfinance: no public data found for '{company}' — likely private")

        if use_cache:
            set_cached(company, country, "financial", results)
        return results

    except Exception as exc:
        logger.warning(f"yfinance error: {exc}")
        return []
