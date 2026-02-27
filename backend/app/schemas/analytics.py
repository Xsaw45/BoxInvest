from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_listings: int
    enriched_listings: int
    avg_edge_score: float | None
    avg_gross_yield: float | None
    avg_price: float | None
    top_cities: list[dict]


class TopOpportunity(BaseModel):
    id: str
    title: str
    city: str | None
    price: float
    surface: float | None
    gross_yield: float | None
    edge_score: float
    url: str | None
