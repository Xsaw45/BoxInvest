from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.listing import Listing
from app.models.enrichment import ListingEnrichment
from app.schemas.analytics import DashboardSummary, TopOpportunity

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count()).select_from(Listing))).scalar_one()
    enriched = (
        await db.execute(select(func.count()).select_from(ListingEnrichment))
    ).scalar_one()

    agg = (
        await db.execute(
            select(
                func.avg(ListingEnrichment.edge_score),
                func.avg(ListingEnrichment.gross_yield),
                func.avg(Listing.price),
            ).join(Listing, Listing.id == ListingEnrichment.listing_id)
        )
    ).first()

    # Top 5 cities by listing count
    cities_q = (
        select(Listing.city, func.count().label("count"))
        .where(Listing.city.isnot(None))
        .group_by(Listing.city)
        .order_by(func.count().desc())
        .limit(5)
    )
    cities = (await db.execute(cities_q)).all()

    return DashboardSummary(
        total_listings=total,
        enriched_listings=enriched,
        avg_edge_score=round(float(agg[0]), 1) if agg[0] else None,
        avg_gross_yield=round(float(agg[1]), 2) if agg[1] else None,
        avg_price=round(float(agg[2]), 0) if agg[2] else None,
        top_cities=[{"city": r.city, "count": r.count} for r in cities],
    )


@router.get("/top", response_model=list[TopOpportunity])
async def top_opportunities(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Return top listings by edge score (top 5% threshold)."""
    # Compute the 95th percentile edge score
    p95_q = select(
        func.percentile_cont(0.95).within_group(ListingEnrichment.edge_score)
    )
    p95 = (await db.execute(p95_q)).scalar()

    q = (
        select(
            Listing.id,
            Listing.title,
            Listing.city,
            Listing.price,
            Listing.surface,
            Listing.url,
            ListingEnrichment.gross_yield,
            ListingEnrichment.edge_score,
        )
        .join(ListingEnrichment, ListingEnrichment.listing_id == Listing.id)
        .where(ListingEnrichment.edge_score.isnot(None))
        .order_by(ListingEnrichment.edge_score.desc())
        .limit(limit)
    )
    rows = (await db.execute(q)).all()

    return [
        TopOpportunity(
            id=str(r.id),
            title=r.title,
            city=r.city,
            price=float(r.price),
            surface=float(r.surface) if r.surface else None,
            gross_yield=float(r.gross_yield) if r.gross_yield else None,
            edge_score=float(r.edge_score),
            url=r.url,
        )
        for r in rows
    ]
