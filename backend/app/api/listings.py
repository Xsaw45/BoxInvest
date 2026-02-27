import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.functions import ST_AsGeoJSON, ST_X, ST_Y
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.listing import Listing
from app.models.enrichment import ListingEnrichment
from app.schemas.listing import ListingGeoJSON, ListingSchema, ListingsPage

router = APIRouter(prefix="/listings", tags=["listings"])


def _serialize_listing(listing: Listing) -> dict:
    """Convert ORM Listing to dict, extracting lat/lon from PostGIS geometry."""
    data = {
        "id": str(listing.id),
        "source": listing.source,
        "external_id": listing.external_id,
        "url": listing.url,
        "title": listing.title,
        "description": listing.description,
        "price": float(listing.price),
        "surface": float(listing.surface) if listing.surface else None,
        "city": listing.city,
        "postal_code": listing.postal_code,
        "address": listing.address,
        "photos_count": listing.photos_count,
        "floor_level": listing.floor_level,
        "accessibility_tags": listing.accessibility_tags or [],
        "scraped_at": listing.scraped_at,
        "updated_at": listing.updated_at,
        "lat": None,
        "lon": None,
        "enrichment": None,
    }
    # lat/lon are injected by the query via ST_Y / ST_X
    if hasattr(listing, "_lat"):
        data["lat"] = listing._lat
        data["lon"] = listing._lon
    if listing.enrichment:
        e = listing.enrichment
        data["enrichment"] = {
            "avg_rent_area": float(e.avg_rent_area) if e.avg_rent_area else None,
            "population_density": float(e.population_density) if e.population_density else None,
            "commercial_density": float(e.commercial_density) if e.commercial_density else None,
            "transport_score": float(e.transport_score) if e.transport_score else None,
            "liquidity_score": float(e.liquidity_score) if e.liquidity_score else None,
            "accessibility_score": float(e.accessibility_score) if e.accessibility_score else None,
            "vertical_storage_potential": float(e.vertical_storage_potential) if e.vertical_storage_potential else None,
            "price_per_sqm": float(e.price_per_sqm) if e.price_per_sqm else None,
            "estimated_rent_low": float(e.estimated_rent_low) if e.estimated_rent_low else None,
            "estimated_rent_high": float(e.estimated_rent_high) if e.estimated_rent_high else None,
            "gross_yield": float(e.gross_yield) if e.gross_yield else None,
            "storage_yield_estimate": float(e.storage_yield_estimate) if e.storage_yield_estimate else None,
            "ml_estimated_price": float(e.ml_estimated_price) if e.ml_estimated_price else None,
            "ml_price_deviation": float(e.ml_price_deviation) if e.ml_price_deviation else None,
            "edge_score": float(e.edge_score) if e.edge_score else None,
            "computed_at": e.computed_at,
        }
    return data


@router.get("", response_model=ListingsPage)
async def list_listings(
    city: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_surface: float | None = None,
    max_surface: float | None = None,
    min_yield: float | None = Query(None, alias="min_yield"),
    min_edge: float | None = Query(None, alias="min_edge"),
    source: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    base_q = (
        select(
            Listing,
            ST_Y(Listing.location).label("lat"),
            ST_X(Listing.location).label("lon"),
        )
        .outerjoin(ListingEnrichment, ListingEnrichment.listing_id == Listing.id)
        .options(selectinload(Listing.enrichment))
    )

    if city:
        base_q = base_q.where(func.lower(Listing.city) == city.lower())
    if source:
        base_q = base_q.where(Listing.source == source)
    if min_price is not None:
        base_q = base_q.where(Listing.price >= min_price)
    if max_price is not None:
        base_q = base_q.where(Listing.price <= max_price)
    if min_surface is not None:
        base_q = base_q.where(Listing.surface >= min_surface)
    if max_surface is not None:
        base_q = base_q.where(Listing.surface <= max_surface)
    if min_yield is not None:
        base_q = base_q.where(ListingEnrichment.gross_yield >= min_yield)
    if min_edge is not None:
        base_q = base_q.where(ListingEnrichment.edge_score >= min_edge)

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    result_q = base_q.order_by(ListingEnrichment.edge_score.desc().nullslast()).limit(limit).offset(offset)
    rows = (await db.execute(result_q)).all()

    items = []
    for row in rows:
        listing = row[0]
        listing._lat = row[1]
        listing._lon = row[2]
        items.append(_serialize_listing(listing))

    return {"total": total, "items": items}


@router.get("/geojson", response_model=ListingGeoJSON)
async def listings_geojson(
    city: str | None = None,
    min_edge: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(
            Listing.id,
            Listing.title,
            Listing.price,
            Listing.surface,
            Listing.city,
            Listing.url,
            ST_Y(Listing.location).label("lat"),
            ST_X(Listing.location).label("lon"),
            ListingEnrichment.edge_score,
            ListingEnrichment.gross_yield,
            ListingEnrichment.price_per_sqm,
        )
        .outerjoin(ListingEnrichment, ListingEnrichment.listing_id == Listing.id)
        .where(Listing.location.isnot(None))
    )
    if city:
        q = q.where(func.lower(Listing.city) == city.lower())
    if min_edge is not None:
        q = q.where(ListingEnrichment.edge_score >= min_edge)

    rows = (await db.execute(q)).all()

    features = []
    for row in rows:
        if row.lat is None or row.lon is None:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row.lon, row.lat]},
            "properties": {
                "id": str(row.id),
                "title": row.title,
                "price": float(row.price),
                "surface": float(row.surface) if row.surface else None,
                "city": row.city,
                "url": row.url,
                "edge_score": float(row.edge_score) if row.edge_score else None,
                "gross_yield": float(row.gross_yield) if row.gross_yield else None,
                "price_per_sqm": float(row.price_per_sqm) if row.price_per_sqm else None,
            },
        })

    return {"type": "FeatureCollection", "features": features}


@router.get("/{listing_id}", response_model=ListingSchema)
async def get_listing(listing_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    q = (
        select(
            Listing,
            ST_Y(Listing.location).label("lat"),
            ST_X(Listing.location).label("lon"),
        )
        .where(Listing.id == listing_id)
        .options(selectinload(Listing.enrichment))
    )
    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing = row[0]
    listing._lat = row[1]
    listing._lon = row[2]
    return _serialize_listing(listing)
