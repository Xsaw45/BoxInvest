"""
DVF (Demandes de Valeurs Foncières) enricher.

Downloads per-commune garage transaction CSVs from the French government's open data portal
(files.data.gouv.fr/geo-dvf) and computes median garage price per m² for each tracked city.

Results are cached in memory and refreshed at startup + weekly via APScheduler.
Hardcoded market data in market_enricher.py remains as fallback when DVF is unavailable.

URL structure: https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/communes/{dept}/{commune}.csv
Files are plain CSV (not gzip). Cities with arrondissements (Paris, Lyon, Marseille) have one
file per arrondissement — all files are downloaded and combined before computing the median.

Key DVF data nuance:
  valeur_fonciere is the total transaction price — it is DUPLICATED across every property row
  in the same mutation (transaction). A transaction selling 2 garages at 40k€ each shows
  80k€ on BOTH rows. We must deduplicate by id_mutation and divide by the garage lot count
  to get a per-unit price, then cap to realistic ranges to exclude outlier storage units.
"""
import asyncio
import io
import logging

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

DVF_YEAR = "2024"
DVF_BASE = "https://files.data.gouv.fr/geo-dvf/latest/csv"

# For each city: dept code + list of commune/arrondissement CSV codes.
# Paris:    20 arrondissements → 75101–75120
# Lyon:     9  arrondissements → 69381–69389
# Marseille:16 arrondissements → 13201–13216
# Strasbourg (67482) is absent from the 2024 communes directory → uses hardcoded fallback.
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

# Assumed typical garage surface for price/m² conversion (total price → €/m²)
_TYPICAL_GARAGE_SQM = 12.0

# Realistic per-unit price bounds for French garages/parking spaces.
# Below 1 500 € → data error. Above 150 000 € → large commercial storage unit, not a parking space.
_MIN_PER_LOT = 1_500.0
_MAX_PER_LOT = 150_000.0


def _parse_garage_prices(raw_csv: bytes) -> list[float]:
    """
    Sync function (run in thread executor).

    Parses one DVF commune CSV and returns a list of per-unit garage prices (in €).

    Deduplication logic:
      - `valeur_fonciere` is the TOTAL transaction price, duplicated on every property row.
      - We group by `id_mutation`, take the price once, and divide by the number of
        Dépendance lots in that transaction to get a per-unit price.
      - We cap per-unit prices to [_MIN_PER_LOT, _MAX_PER_LOT] to exclude outliers
        (large commercial storage boxes, errors, mixed apartment+parking transactions).
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

    required = {"nature_mutation", "type_local", "valeur_fonciere", "id_mutation"}
    if not required.issubset(set(df.columns)):
        return []

    # Keep only garage/parking sales
    mask = (df["nature_mutation"] == "Vente") & (df["type_local"] == "Dépendance")
    garage_df = df[mask].copy()
    if garage_df.empty:
        return []

    # Parse price (DVF may use comma as decimal separator)
    garage_df["valeur_fonciere"] = (
        garage_df["valeur_fonciere"]
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )
    garage_df = garage_df.dropna(subset=["valeur_fonciere"])
    garage_df = garage_df[garage_df["valeur_fonciere"] > 0]

    if garage_df.empty:
        return []

    # Deduplicate: group by id_mutation
    # - price:  take first() — all rows in a mutation share the same valeur_fonciere
    # - lots:   count() rows in this mutation that are Dépendance
    per_mutation = garage_df.groupby("id_mutation").agg(
        price=("valeur_fonciere", "first"),
        lots=("id_mutation", "count"),
    )

    # Per-unit price = total transaction price / number of garage lots
    per_mutation["per_lot"] = per_mutation["price"] / per_mutation["lots"]

    # Filter to realistic parking/garage price range
    valid = per_mutation[
        (per_mutation["per_lot"] >= _MIN_PER_LOT)
        & (per_mutation["per_lot"] <= _MAX_PER_LOT)
    ]

    return valid["per_lot"].tolist()


async def _fetch_commune(dept: str, commune: str) -> list[float]:
    """Download one commune CSV and return raw per-unit garage prices."""
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
    return await loop.run_in_executor(None, _parse_garage_prices, raw)


async def _fetch_city(city: str) -> float | None:
    """
    Download all commune files for a city, aggregate per-unit garage prices,
    and return the median price in €/m² (divides by _TYPICAL_GARAGE_SQM).
    Returns None if fewer than 5 valid transactions are found.
    """
    cfg = CITY_DVF_CONFIG.get(city)
    if not cfg:
        return None

    dept = cfg["dept"]
    communes = cfg["communes"]

    tasks = [_fetch_commune(dept, c) for c in communes]
    results = await asyncio.gather(*tasks)

    all_prices: list[float] = []
    for prices in results:
        all_prices.extend(prices)

    if len(all_prices) < 5:
        logger.debug("DVF %s: only %d valid transactions, skipping", city, len(all_prices))
        return None

    s = pd.Series(all_prices)
    median_total = float(s.median())
    price_per_sqm = round(median_total / _TYPICAL_GARAGE_SQM, 2)
    logger.info(
        "DVF %s → median €%.0f/unit → %.0f €/m² (%d transactions)",
        city, median_total, price_per_sqm, len(all_prices),
    )
    return price_per_sqm


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
            success += 1
        else:
            logger.warning("DVF %s → no data (using hardcoded fallback)", city)

    logger.info(
        "DVF refresh complete: %d/%d cities loaded", success, len(CITY_DVF_CONFIG)
    )


def get_cached_price(city: str) -> float | None:
    """Return the DVF-derived median garage price in €/m² for the given city, or None."""
    return _cache.get(city)
