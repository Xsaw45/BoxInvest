"""Initial schema: listings + listing_enrichments

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("surface", sa.Numeric(8, 2), nullable=True),
        sa.Column(
            "location",
            Geometry(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(10), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("photos_count", sa.Integer, default=0),
        sa.Column("floor_level", sa.Integer, nullable=True),
        sa.Column("accessibility_tags", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column(
            "scraped_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_listings_source", "listings", ["source"])
    op.create_index("ix_listings_city", "listings", ["city"])

    op.create_table(
        "listing_enrichments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "listing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("avg_rent_area", sa.Numeric(8, 2), nullable=True),
        sa.Column("population_density", sa.Numeric(12, 2), nullable=True),
        sa.Column("commercial_density", sa.Numeric(10, 2), nullable=True),
        sa.Column("transport_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("liquidity_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("accessibility_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("vertical_storage_potential", sa.Numeric(5, 2), nullable=True),
        sa.Column("price_per_sqm", sa.Numeric(10, 2), nullable=True),
        sa.Column("estimated_rent_low", sa.Numeric(8, 2), nullable=True),
        sa.Column("estimated_rent_high", sa.Numeric(8, 2), nullable=True),
        sa.Column("gross_yield", sa.Numeric(6, 3), nullable=True),
        sa.Column("storage_yield_estimate", sa.Numeric(6, 3), nullable=True),
        sa.Column("ml_estimated_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("ml_price_deviation", sa.Numeric(8, 3), nullable=True),
        sa.Column("edge_score", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "computed_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_listing_enrichments_listing_id",
        "listing_enrichments",
        ["listing_id"],
    )
    op.create_index(
        "ix_listing_enrichments_edge_score",
        "listing_enrichments",
        ["edge_score"],
    )


def downgrade() -> None:
    op.drop_table("listing_enrichments")
    op.drop_table("listings")
