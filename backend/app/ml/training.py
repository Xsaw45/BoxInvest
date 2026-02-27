"""
Training data builder + trigger.
Pulls enriched listings from DB and feeds them to the price estimator.
"""
import logging

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.enrichment.market_enricher import get_market_data
from app.ml.price_estimator import FEATURES, train_model

logger = logging.getLogger(__name__)


async def build_training_data(db: AsyncSession) -> list[dict]:
    """
    Build training rows from listings + enrichments already in the DB.
    Falls back gracefully for listings without enrichments.
    """
    query = text("""
        SELECT
            l.price,
            l.surface,
            ST_Y(l.location::geometry) AS lat,
            ST_X(l.location::geometry) AS lon,
            l.city,
            l.photos_count,
            e.transport_score,
            e.accessibility_score
        FROM listings l
        LEFT JOIN listing_enrichments e ON e.listing_id = l.id
        WHERE l.price > 0 AND l.surface IS NOT NULL
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    training_data = []
    for row in rows:
        market = get_market_data(row.city)
        training_data.append({
            "price": float(row.price),
            "surface": float(row.surface),
            "lat": float(row.lat) if row.lat else 48.85,
            "lon": float(row.lon) if row.lon else 2.35,
            "city_avg_sell_per_sqm": market.city_avg_sell_per_sqm,
            "transport_score": float(row.transport_score) if row.transport_score else 30.0,
            "accessibility_score": float(row.accessibility_score) if row.accessibility_score else 20.0,
            "photos_count": float(row.photos_count or 0),
        })

    return training_data


async def trigger_training(db: AsyncSession) -> bool:
    data = await build_training_data(db)
    logger.info("Training ML model with %d samples", len(data))
    return train_model(data)
