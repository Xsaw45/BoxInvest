"""
DVF (Demandes de Valeurs Foncières) enricher.

Downloads per-commune garage transaction CSVs from the French government's open data portal
(files.data.gouv.fr/geo-dvf) and computes median garage price per m² for each tracked city.

Results are cached in memory and refreshed at startup + weekly via APScheduler.
Hardcoded market data in market_enricher.py remains as fallback when DVF is unavailable.
"""
import asyncio
import io
import logging

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

# INSEE commune codes for the 12 tracked cities
CITY_DVF_CONFIG: dict[str, dict[str, str]] = {
    "Paris":       {"dept": "75", "commune": "75056"},
    "Lyon":        {"dept": "69", "commune": "69123"},
    "Marseille":   {"dept": "13", "commune": "13055"},
    "Bordeaux":    {"dept": "33", "commune": "33063"},
    "Toulouse":    {"dept": "31", "commune": "31555"},
    "Nantes":      {"dept": "44", "commune": "44109"},
    "Strasbourg":  {"dept": "67", "commune": "67482"},
    "Montpellier": {"dept": "34", "commune": "34172"},
    "Lille":       {"dept": "59", "commune": "59350"},
    "Rennes":      {"dept": "35", "commune": "35238"},
    "Nice":        {"dept": "06", "commune": "06088"},
    "Grenoble":    {"dept": "38", "commune": "38185"},
}

DVF_YEAR = "2024"
DVF_BASE = "https://files.data.gouv.fr/geo-dvf/latest/csv"

# In-memory cache: city → median garage price in €/m²
_cache: dict[str, float] = {}

# Assumed typical garage surface for price/m² conversion (total transaction price → €/m²)
_TYPICAL_GARAGE_SQM = 12.0


def _parse_garage_price_per_sqm(raw_gz: bytes) -> float | None:
    """
    Sync function (run in thread executor).
    Parses a DVF commune gzip CSV and returns the median garage price in €/m².
    Returns None if fewer than 5 valid rows are found.
    """
    try:
        df = pd.read_csv(
            io.BytesIO(raw_gz),
            compression="gzip",
            low_memory=False,
            sep=",",
            dtype=str,  # read as str first to avoid mixed-type warnings
        )
    except Exception as exc:
        logger.warning("DVF CSV parse error: %s", exc)
        return None

    # Normalize column names (DVF uses lowercase with accents sometimes)
    df.columns = [c.strip().lower() for c in df.columns]

    if "nature_mutation" not in df.columns or "type_local" not in df.columns:
        logger.warning("DVF CSV missing expected columns: %s", list(df.columns))
        return None

    # Filter to garage/parking sales only
    mask = (df["nature_mutation"] == "Vente") & (df["type_local"] == "Dépendance")
    garage_df = df[mask].copy()

    if garage_df.empty:
        return None

    # Parse price column
    if "valeur_fonciere" not in garage_df.columns:
        return None

    # DVF uses comma as decimal separator in some files
    garage_df["valeur_fonciere"] = (
        garage_df["valeur_fonciere"]
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )
    garage_df = garage_df[garage_df["valeur_fonciere"] > 0].dropna(subset=["valeur_fonciere"])

    if len(garage_df) < 5:
        return None

    # Convert total transaction price → €/m² using typical garage size
    median_total = float(garage_df["valeur_fonciere"].median())
    return round(median_total / _TYPICAL_GARAGE_SQM, 2)


async def _fetch_city(city: str) -> float | None:
    """Async: download DVF gzip for one city and parse garage median price per m²."""
    cfg = CITY_DVF_CONFIG.get(city)
    if not cfg:
        return None

    url = f"{DVF_BASE}/{DVF_YEAR}/communes/{cfg['dept']}/{cfg['commune']}.csv.gz"
    try:
        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            raw_gz = resp.content
    except httpx.HTTPStatusError as exc:
        logger.warning("DVF HTTP error for %s (%s): %s", city, url, exc.response.status_code)
        return None
    except Exception as exc:
        logger.warning("DVF download failed for %s: %s", city, exc)
        return None

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _parse_garage_price_per_sqm, raw_gz)


async def refresh_all_cities() -> None:
    """
    Download and cache DVF garage medians for all tracked cities.
    Uses a semaphore to limit concurrent downloads (polite to data.gouv.fr).
    """
    sem = asyncio.Semaphore(3)

    async def _guarded(city: str) -> tuple[str, float | None]:
        async with sem:
            result = await _fetch_city(city)
            return city, result

    tasks = [_guarded(city) for city in CITY_DVF_CONFIG]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success = 0
    for item in results:
        if isinstance(item, Exception):
            logger.warning("DVF task raised: %s", item)
            continue
        city, price = item
        if price is not None:
            _cache[city] = price
            logger.info("DVF %s → %.1f €/m²", city, price)
            success += 1
        else:
            logger.warning("DVF %s → no data (using fallback)", city)

    logger.info("DVF refresh complete: %d/%d cities loaded", success, len(CITY_DVF_CONFIG))


def get_cached_price(city: str) -> float | None:
    """Return the DVF-derived median garage price in €/m² for the given city, or None."""
    return _cache.get(city)
