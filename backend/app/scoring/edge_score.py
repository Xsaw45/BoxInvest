"""
Investment Edge Score engine.
Produces a normalized 0–100 score combining price deviation, yield,
storage potential, demand indicators and liquidity.

Weights (must sum to 1.0):
  price_deviation  0.30
  yield            0.25
  storage          0.20
  demand           0.15
  liquidity        0.10
"""
import math

from app.config import settings

# Reference values for normalization
YIELD_EXCELLENT = 12.0   # % — top-tier gross yield for a French garage
YIELD_POOR = 2.0         # %
TRANSPORT_MAX = 100.0
COMMERCIAL_MAX = 30.0    # POIs count within 800m considered "dense"


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _price_deviation_score(
    price: float,
    surface: float | None,
    city_avg_sell_per_sqm: float,
    ml_price_deviation: float | None,
) -> float:
    """
    Score how far below fair value a listing is.
    If we have an ML estimate, use it. Otherwise fall back to city median.
    Returns 0–100 (100 = extremely undervalued).
    """
    if ml_price_deviation is not None:
        # ml_price_deviation = (ml_price - listing_price) / ml_price * 100
        # Positive → listing cheaper than ML estimate → good
        return _clamp((ml_price_deviation + 10) * 3.0)

    if not surface or surface <= 0 or city_avg_sell_per_sqm <= 0:
        return 50.0  # neutral when no data

    fair_price = surface * city_avg_sell_per_sqm
    deviation_pct = (fair_price - price) / fair_price * 100  # positive = below fair
    # Map: -30% overpriced → 0, at fair → 50, +30% underpriced → 100
    return _clamp(50.0 + deviation_pct * 1.67)


def _yield_score(gross_yield: float | None) -> float:
    """Normalize gross yield to 0–100."""
    if gross_yield is None:
        return 40.0  # neutral
    # Linear interpolation between YIELD_POOR and YIELD_EXCELLENT
    score = (gross_yield - YIELD_POOR) / (YIELD_EXCELLENT - YIELD_POOR) * 100.0
    return _clamp(score)


def _storage_score(
    vertical_storage_potential: float,
    accessibility_tags: list[str],
) -> float:
    tags_set = {t.lower() for t in (accessibility_tags or [])}
    base = vertical_storage_potential
    # Bonus for electricity (enables lighting/shelving) and large height
    if "électricité" in tags_set:
        base += 10.0
    if "hauteur 2.5m" in tags_set:
        base += 10.0
    return _clamp(base)


def _demand_score(transport_score: float, commercial_density: float) -> float:
    """Combine transport and commercial density into a demand signal."""
    transport_norm = _clamp(transport_score)
    commercial_norm = _clamp(commercial_density / COMMERCIAL_MAX * 100.0)
    return transport_norm * 0.6 + commercial_norm * 0.4


def compute_edge_score(
    price: float,
    surface: float | None,
    city_avg_sell_per_sqm: float,
    gross_yield: float | None,
    transport_score: float,
    commercial_density: float,
    accessibility_tags: list[str],
    liquidity_score: float,
    ml_price_deviation: float | None = None,
    vertical_storage_potential: float = 30.0,
) -> float:
    w = settings

    price_dev = _price_deviation_score(price, surface, city_avg_sell_per_sqm, ml_price_deviation)
    yld = _yield_score(gross_yield)
    storage = _storage_score(vertical_storage_potential, accessibility_tags)
    demand = _demand_score(transport_score, commercial_density)
    liquidity = _clamp(liquidity_score)

    raw = (
        price_dev  * w.weight_price_deviation
        + yld      * w.weight_yield
        + storage  * w.weight_storage_potential
        + demand   * w.weight_demand
        + liquidity * w.weight_liquidity
    )

    return round(_clamp(raw), 2)
