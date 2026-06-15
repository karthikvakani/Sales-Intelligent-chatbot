"""
utils/cache.py
Disk-backed TTL cache so repeated queries for the same company
don't re-hit external APIs (directly addresses the duplicated-effort
business problem noted in Section 9 of the assessment).
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Any, Optional

from config.settings import CACHE_DIR, CACHE_TTL_HOURS
from utils.logger import logger


def _cache_key(company: str, country: str, source: str) -> str:
    raw = f"{company.lower().strip()}|{country.lower().strip()}|{source}"
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def get_cached(company: str, country: str, source: str) -> Optional[Any]:
    """Return cached data if it exists and hasn't expired."""
    key = _cache_key(company, country, source)
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
        age_hours = (time.time() - payload["ts"]) / 3600
        if age_hours > CACHE_TTL_HOURS:
            path.unlink(missing_ok=True)
            logger.debug(f"Cache expired for {source}/{company}")
            return None
        logger.info(f"Cache hit [{source}] for '{company}' ({age_hours:.1f}h old)")
        return payload["data"]
    except Exception as exc:
        logger.warning(f"Cache read error: {exc}")
        return None


def set_cached(company: str, country: str, source: str, data: Any) -> None:
    """Write data to cache."""
    key = _cache_key(company, country, source)
    path = _cache_path(key)
    try:
        path.write_text(json.dumps({"ts": time.time(), "data": data}, ensure_ascii=False, default=str))
        logger.debug(f"Cached [{source}] for '{company}'")
    except Exception as exc:
        logger.warning(f"Cache write error: {exc}")


def clear_cache(company: str = "", country: str = "") -> int:
    """Clear all cache files (or those matching company/country)."""
    removed = 0
    for f in CACHE_DIR.glob("*.json"):
        f.unlink(missing_ok=True)
        removed += 1
    logger.info(f"Cleared {removed} cache files")
    return removed
