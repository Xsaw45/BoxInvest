"""
All background job implementations.
Called both by APScheduler (scheduled) and the /api/jobs/* endpoints (manual).
"""
import logging
import uuid
from datetime import datetime

from geoalchemy2.elements import WKTElement
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.enrichment.dvf_enricher import refresh_all_cities
from app.enrichment.pipeline import run_enrichment_pipeline
from app.ml.price_estimator import predict_price
from app.ml.training import trigger_training
from app.models.enrichment import ListingEnrichment
from app.models.listing import Listing
from app.scrapers.mock import MockScraper
from app.scrapers.leboncoin import LeboncoinScraper
from app.enrichment.market_enricher import get_market_data

logger = logging.getLogger(__name__)


async def _upsert_listing(db: AsyncSession, raw) -> uuid.UUID:
    """Insert or skip-if-exists a scraped listing. Returns its UUID."""
    existing = None
    if raw.external_id:
        existing = (
            await db.execute(
                select(Listing.id).where(
                    Listing.source == raw.source,
                    Listing.external_id == raw.external_id,
                )
            )
        ).scalar_one_or_none()

    if existing:
        return existing

    location = None
    if raw.lat is not None and raw.lon is not None:
        location = WKTElement(f"POINT({raw.lon} {raw.lat})", srid=4326)

    listing = Listing(
        id=uuid.uuid4(),
        source=raw.source,
        external_id=raw.external_id,
        url=raw.url,
        title=raw.title,
        description=raw.description,
        price=raw.price,
        surface=raw.surface,
        location=location,
        city=raw.city,
        postal_code=raw.postal_code,
        address=raw.address,
        photos_count=raw.photos_count,
        floor_level=raw.floor_level,
        accessibility_tags=raw.accessibility_tags or [],
        scraped_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(listing)
    await db.flush()
    return listing.id


async def ingest_mock_data(db: AsyncSession | None = None):
    """Seed the DB with mock listings if it has fewer than 10 listings."""
    own_session = db is None
    if own_session:
        db = AsyncSessionLocal()
    try:
        count = (await db.execute(select(func.count()).select_from(Listing))).scalar_one()
        if count >= 10:
            logger.info("DB already has %d listings — skipping mock seed", count)
            return

        scraper = MockScraper()
        listings = await scraper.scrape(max_listings=500)
        for raw in listings:
            await _upsert_listing(db, raw)
        await db.commit()
        logger.info("Seeded %d mock listings", len(listings))
    finally:
        if own_session:
            await db.close()


async def enrich_pending_listings(db: AsyncSession | None = None):
    """Enrich all listings that don't yet have an enrichment row."""
    own_session = db is None
    if own_session:
        db = AsyncSessionLocal()
    try:
        # Find listings with no enrichment
        subq = select(ListingEnrichment.listing_id)
        q = (
            select(Listing)
            .where(Listing.id.notin_(subq))
            .limit(200)
        )
        listings = (await db.execute(q)).scalars().all()
        logger.info("Enriching %d listings…", len(listings))

        for listing in listings:
            try:
                lat = None
                lon = None
                if listing.location is not None:
                    from geoalchemy2.functions import ST_Y, ST_X
                    coords = (
                        await db.execute(
                            select(
                                ST_Y(listing.location).label("lat"),
                                ST_X(listing.location).label("lon"),
                            )
                        )
                    ).first()
                    if coords:
                        lat, lon = coords.lat, coords.lon

                market = get_market_data(listing.city)

                ml_price = predict_price(
                    surface=float(listing.surface) if listing.surface else None,
                    lat=lat,
                    lon=lon,
                    city_avg_sell_per_sqm=market.city_avg_sell_per_sqm,
                    transport_score=30.0,
                    accessibility_score=20.0,
                    photos_count=listing.photos_count or 0,
                )

                data = await run_enrichment_pipeline(
                    listing_id=str(listing.id),
                    price=float(listing.price),
                    surface=float(listing.surface) if listing.surface else None,
                    city=listing.city,
                    lat=lat,
                    lon=lon,
                    accessibility_tags=listing.accessibility_tags or [],
                    photos_count=listing.photos_count or 0,
                    ml_estimated_price=ml_price,
                    source=listing.source,
                )

                enrichment = ListingEnrichment(id=uuid.uuid4(), listing_id=listing.id, **data)
                db.add(enrichment)

            except Exception as exc:
                logger.warning("Failed to enrich listing %s: %s", listing.id, exc)
                continue

        await db.commit()
        logger.info("Enrichment batch done")
    finally:
        if own_session:
            await db.close()


async def retrain_price_model(db: AsyncSession | None = None):
    own_session = db is None
    if own_session:
        db = AsyncSessionLocal()
    try:
        success = await trigger_training(db)
        logger.info("ML retrain result: %s", "success" if success else "skipped")
    finally:
        if own_session:
            await db.close()


async def refresh_dvf_prices():
    """Download latest DVF garage transaction medians for all tracked cities."""
    logger.info("Starting DVF price refresh...")
    await refresh_all_cities()
    logger.info("DVF price refresh complete")


async def scrape_leboncoin():
    """Run the Leboncoin scraper and persist new listings."""
    from app.config import settings
    db = AsyncSessionLocal()
    try:
        scraper = LeboncoinScraper()
        listings = await scraper.scrape(max_listings=settings.scraper_max_listings_per_run)
        new_count = 0
        for raw in listings:
            listing_id = await _upsert_listing(db, raw)
            new_count += 1
        await db.commit()
        logger.info("Leboncoin: persisted %d new listings", new_count)
    finally:
        await db.close()
