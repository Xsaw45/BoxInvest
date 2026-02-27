import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import ARRAY, TIMESTAMP, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    surface: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)

    # PostGIS point (SRID 4326 = WGS84 lat/lon)
    location: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=True
    )
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    photos_count: Mapped[int] = mapped_column(Integer, default=0)
    floor_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accessibility_tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )

    scraped_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
