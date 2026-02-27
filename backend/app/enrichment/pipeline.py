"""
Enrichment pipeline orchestrator.
Runs all enrichers on a listing and returns a dict ready to upsert into listing_enrichments.
"""
import logging

from app.enrichment.geo_enricher import enrich_geo
from app.enrichment.market_enricher import get_market_data
from app.scoring.metrics import compute_metrics
from app.scoring.edge_score import compute_edge_score

logger = logging.getLogger(__name__)


async def run_enrichment_pipeline(
    listing_id: str,
    price: float,
    surface: float | None,
    city: str | None,
    lat: float | None,
    lon: float | None,
    accessibility_tags: list[str],
    photos_count: int,
    ml_estimated_price: float | None = None,
) -> dict:
    """
    Full enrichment pipeline for one listing.
    Returns a flat dict matching listing_enrichments columns.
    """
    # 1. Market data (local stats)
    market = get_market_data(city)

    # 2. Geo data (transport, POIs) — only if we have coordinates
    geo = {"transport_score": 30.0, "commercial_density": 5.0}
    if lat and lon:
        try:
            geo = await enrich_geo(lat, lon)
        except Exception as exc:
            logger.warning("Geo enrichment failed for listing %s: %s", listing_id, exc)

    # 3. Derived financial metrics
    metrics = compute_metrics(
        price=price,
        surface=surface,
        avg_rent_per_sqm=market.avg_rent_area,
        city_avg_sell_per_sqm=market.city_avg_sell_per_sqm,
        accessibility_tags=accessibility_tags,
        photos_count=photos_count,
    )

    # 4. ML price deviation
    ml_price_deviation = None
    if ml_estimated_price and ml_estimated_price > 0:
        ml_price_deviation = round((ml_estimated_price - price) / ml_estimated_price * 100, 2)

    # 5. Edge score
    edge = compute_edge_score(
        price=price,
        surface=surface,
        city_avg_sell_per_sqm=market.city_avg_sell_per_sqm,
        gross_yield=metrics["gross_yield"],
        transport_score=geo["transport_score"],
        commercial_density=geo["commercial_density"],
        accessibility_tags=accessibility_tags,
        liquidity_score=metrics["liquidity_score"],
        ml_price_deviation=ml_price_deviation,
    )

    return {
        "avg_rent_area": market.avg_rent_area,
        "population_density": market.population_density,
        "commercial_density": geo["commercial_density"],
        "transport_score": geo["transport_score"],
        "liquidity_score": metrics["liquidity_score"],
        "accessibility_score": metrics["accessibility_score"],
        "vertical_storage_potential": metrics["vertical_storage_potential"],
        "price_per_sqm": metrics["price_per_sqm"],
        "estimated_rent_low": metrics["estimated_rent_low"],
        "estimated_rent_high": metrics["estimated_rent_high"],
        "gross_yield": metrics["gross_yield"],
        "storage_yield_estimate": metrics["storage_yield_estimate"],
        "ml_estimated_price": ml_estimated_price,
        "ml_price_deviation": ml_price_deviation,
        "edge_score": edge,
    }
