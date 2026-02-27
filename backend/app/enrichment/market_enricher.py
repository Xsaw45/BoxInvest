"""
Market data enricher.
Uses local city statistics (based on known French market data) for rent and price baselines.
In production this would pull from DVF/INSEE APIs.
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Approximate market data per city
# transport_score: 0-100 estimate based on city transit network quality
# commercial_density: approximate POIs per km²
CITY_MARKET_DATA = {
    "Paris":       {"avg_rent_per_sqm": 25.0, "population_density": 21000, "avg_sell_per_sqm": 2800, "transport_score": 95.0, "commercial_density": 28.0},
    "Lyon":        {"avg_rent_per_sqm": 13.0, "population_density": 10500, "avg_sell_per_sqm": 1400, "transport_score": 78.0, "commercial_density": 18.0},
    "Marseille":   {"avg_rent_per_sqm": 10.0, "population_density": 3500,  "avg_sell_per_sqm": 900,  "transport_score": 65.0, "commercial_density": 14.0},
    "Bordeaux":    {"avg_rent_per_sqm": 12.0, "population_density": 5000,  "avg_sell_per_sqm": 1300, "transport_score": 70.0, "commercial_density": 16.0},
    "Toulouse":    {"avg_rent_per_sqm": 11.0, "population_density": 4000,  "avg_sell_per_sqm": 1100, "transport_score": 68.0, "commercial_density": 15.0},
    "Nantes":      {"avg_rent_per_sqm": 12.0, "population_density": 4500,  "avg_sell_per_sqm": 1200, "transport_score": 72.0, "commercial_density": 15.0},
    "Strasbourg":  {"avg_rent_per_sqm": 11.5, "population_density": 3400,  "avg_sell_per_sqm": 1050, "transport_score": 74.0, "commercial_density": 14.0},
    "Montpellier": {"avg_rent_per_sqm": 10.5, "population_density": 3200,  "avg_sell_per_sqm": 950,  "transport_score": 66.0, "commercial_density": 13.0},
    "Lille":       {"avg_rent_per_sqm": 9.5,  "population_density": 7000,  "avg_sell_per_sqm": 900,  "transport_score": 76.0, "commercial_density": 20.0},
    "Rennes":      {"avg_rent_per_sqm": 11.0, "population_density": 3900,  "avg_sell_per_sqm": 1050, "transport_score": 67.0, "commercial_density": 13.0},
    "Nice":        {"avg_rent_per_sqm": 15.0, "population_density": 4800,  "avg_sell_per_sqm": 1500, "transport_score": 71.0, "commercial_density": 17.0},
    "Grenoble":    {"avg_rent_per_sqm": 10.0, "population_density": 4400,  "avg_sell_per_sqm": 950,  "transport_score": 69.0, "commercial_density": 14.0},
    "default":     {"avg_rent_per_sqm": 9.0,  "population_density": 2000,  "avg_sell_per_sqm": 800,  "transport_score": 40.0, "commercial_density": 8.0},
}


@dataclass
class MarketData:
    avg_rent_area: float
    population_density: float
    city_avg_sell_per_sqm: float
    transport_score: float
    commercial_density: float


def get_market_data(city: str | None) -> MarketData:
    data = CITY_MARKET_DATA.get(city or "", CITY_MARKET_DATA["default"])
    return MarketData(
        avg_rent_area=data["avg_rent_per_sqm"],
        population_density=data["population_density"],
        city_avg_sell_per_sqm=data["avg_sell_per_sqm"],
        transport_score=data["transport_score"],
        commercial_density=data["commercial_density"],
    )
