"""
DVF (Demandes de Valeurs Foncières) enricher.

Downloads per-commune garage transaction CSVs from the French government's open data portal
(files.data.gouv.fr/geo-dvf) and computes median garage price per m² for each tracked city.

Results are cached in memory and refreshed at startup + weekly via APScheduler.
Hardcoded market data in market_enricher.py remains as fallback when DVF is unavailable.

URL structure: https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/communes/{dept}/{commune}.csv
Files are plain CSV (not gzip). Cities with arrondissements (Paris, Lyon, Marseille) have one
file per arrondissement — all files are downloaded and combined before computing the median.
"""
import asyncio
import io
import logging

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

DVF_YEAR = "2024"
DVF_BASE = "https://files.data.gouv.fr/geo-dvf/latest/csv"

# For each city: dept code + list of commune/arrondissement CSV codes to download.
# Paris:    20 arrondissements → 75101–75120
# Lyon:     9  arrondissements → 69381–69389
# Marseille:16 arrondissements → 13201–13216
# Others:   single commune code
# Strasbourg (67482) is absent from the communes directory → no entry here, uses hardcoded fallback
CITY_DVF_CONFIG: dict[str, dict] = {
    "Paris": {
        "dept": "75",
        "communes": [f"75{100 + i}" for i in range(1, 21)],  # 75101–75120
    },
    "Lyon": {
        "dept": "69",
        "communes": [f"6938{i}" for i in range(1, 10)],  # 69381–69389
    },
    "Marseille": {
        "dept": "13",
        "communes": [f"132{i:02d}" for i in range(1, 17)],  # 13201–13216
    },
    "Bordeaux":    {"dept": "33", "communes": ["33063"]},
    "Toulouse":    {"dept": "31", "communes": ["31555"]},
    "Nantes":      {"dept": "44", "communes": ["44109"]},
    "Montpellier": {"dept": "34", "communes": ["34172"]},
    "Lille":       {"dept": "59", "communes": ["59350"]},
    "Rennes":      {"dept": "35", "communes": ["35238"]},
    "Nice":        {"dept": "06", "communes": ["06088"]},
    "Grenoble":    {"dept": "38", "communes": ["38185"]},
}

# In-memory cache: city → median garage price in €/m²
_cache: dict[str, float] = {}

# Assumed typical garage surface for price/m² conversion (total transaction price → €/m²)
_TYPICAL_GARAGE_SQM = 12.0


def _parse_garage_price_per_sqm(raw_csv: bytes) -> list[float]:
    """
    Sync function (run in thread executor).
    Parses one DVF commune CSV and returns a list of individual garage transaction prices.
    Returns empty list if no valid garage rows are found.
    """
    try:
        df = pd.read_csv(
            io.BytesIO(raw_csv),
            low_memory=False,
            sep=",",
            dtype=str,
        )
    except Exception as exc:
        logger.debug("DVF CSV parse error: %s", exc)
        return []

    df.columns = [c.strip().lower() for c in df.columns]

    required = {"nature_mutation", "type_local", "valeur_fonciere"}
    if not required.issubset(set(df.columns)):
        return []

    mask = (df["nature_mutation"] == "Vente") & (df["type_local"] == "Dépendance")
    garage_df = df[mask].copy()

    if garage_df.empty:
        return []

    # DVF may use comma as decimal separator
    garage_df["valeur_fonciere"] = (
        garage_df["valeur_fonciere"]
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )
    valid = garage_df["valeur_fonciere"].dropna()
    valid = valid[valid > 0]
    return valid.tolist()


async def _fetch_commune(dept: str, commune: str) -> list[float]:
    """Download one commune CSV and return raw garage transaction prices."""
    url = f"{DVF_BASE}/{DVF_YEAR}/communes/{dept}/{commune}.csv"
    try:
        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                logger.debug("DVF 404: %s", url)
                return []
            resp.raise_for_status()
            raw = resp.content
    except httpx.HTTPStatusError as exc:
        logger.warning("DVF HTTP error (%s): %s", exc.response.status_code, url)
        return []
    except Exception as exc:
        logger.warning("DVF download failed (%s): %s", url, exc)
        return []

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _parse_garage_price_per_sqm, raw)


async def _fetch_city(city: str) -> float | None:
    """
    Download all commune files for a city, aggregate garage prices, and return median €/m².
    Returns None if fewer than 5 total garage transactions are found.
    """
    cfg = CITY_DVF_CONFIG.get(city)
    if not cfg:
        return None

    dept = cfg["dept"]
    communes = cfg["communes"]

    # Fetch all commune files concurrently (they're small, no extra semaphore needed per city)
    tasks = [_fetch_commune(dept, c) for c in communes]
    results = await asyncio.gather(*tasks)

    all_prices: list[float] = []
    for prices in results:
        all_prices.extend(prices)

    if len(all_prices) < 5:
        return None

    median_total = float(pd.Series(all_prices).median())
    return round(median_total / _TYPICAL_GARAGE_SQM, 2)


async def refresh_all_cities() -> None:
    """
    Download and cache DVF garage medians for all tracked cities.
    Uses a semaphore to limit total concurrent HTTP requests.
    """
    sem = asyncio.Semaphore(4)

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

    logger.info(
        "DVF refresh complete: %d/%d cities loaded", success, len(CITY_DVF_CONFIG)
    )


def get_cached_price(city: str) -> float | None:
    """Return the DVF-derived median garage price in €/m² for the given city, or None."""
    return _cache.get(city)
