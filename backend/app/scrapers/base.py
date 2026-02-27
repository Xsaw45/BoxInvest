from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RawListing:
    title: str
    price: float
    source: str
    external_id: str | None = None
    url: str | None = None
    description: str | None = None
    surface: float | None = None
    city: str | None = None
    postal_code: str | None = None
    address: str | None = None
    lat: float | None = None
    lon: float | None = None
    photos_count: int = 0
    floor_level: int | None = None
    accessibility_tags: list[str] = field(default_factory=list)


class BaseScraper(ABC):
    source_name: str = "unknown"

    @abstractmethod
    async def scrape(self, max_listings: int = 50) -> list[RawListing]:
        """Fetch listings from the source and return normalized RawListing objects."""
