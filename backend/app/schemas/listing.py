import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnrichmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    avg_rent_area: float | None = None
    population_density: float | None = None
    commercial_density: float | None = None
    transport_score: float | None = None
    liquidity_score: float | None = None
    accessibility_score: float | None = None
    vertical_storage_potential: float | None = None
    price_per_sqm: float | None = None
    estimated_rent_low: float | None = None
    estimated_rent_high: float | None = None
    gross_yield: float | None = None
    storage_yield_estimate: float | None = None
    ml_estimated_price: float | None = None
    ml_price_deviation: float | None = None
    edge_score: float | None = None
    computed_at: datetime | None = None


class ListingBase(BaseModel):
    title: str
    source: str
    price: float
    surface: float | None = None
    city: str | None = None
    postal_code: str | None = None
    address: str | None = None
    photos_count: int = 0
    floor_level: int | None = None
    accessibility_tags: list[str] = Field(default_factory=list)
    url: str | None = None
    description: str | None = None


class ListingCreate(ListingBase):
    external_id: str | None = None
    lat: float | None = None
    lon: float | None = None


class ListingSchema(ListingBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str | None = None
    lat: float | None = None
    lon: float | None = None
    scraped_at: datetime
    updated_at: datetime
    enrichment: EnrichmentSchema | None = None


class ListingGeoFeature(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: dict


class ListingGeoJSON(BaseModel):
    type: str = "FeatureCollection"
    features: list[ListingGeoFeature]


class ListingsPage(BaseModel):
    total: int
    items: list[ListingSchema]
