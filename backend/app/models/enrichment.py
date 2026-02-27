import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

from app.database import Base


class ListingEnrichment(Base):
    __tablename__ = "listing_enrichments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Market data
    avg_rent_area: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    population_density: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    commercial_density: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Computed scores (0–100)
    transport_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    liquidity_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    accessibility_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    vertical_storage_potential: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Derived financial metrics
    price_per_sqm: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_rent_low: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    estimated_rent_high: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    gross_yield: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    storage_yield_estimate: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)

    # ML
    ml_estimated_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    ml_price_deviation: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)

    # THE score
    edge_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True, index=True)

    computed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow
    )

    listing: Mapped["Listing"] = relationship(  # noqa: F821
        "Listing", backref=backref("enrichment", uselist=False)
    )
