"""
Market data enricher.
Uses local city statistics (based on known French market data) for rent and price baselines.
In production this would pull from DVF/INSEE APIs.
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Approximate market data per city (€/m²/month rent, population density)
CITY_MARKET_DATA = {
    "Paris": {"avg_rent_per_sqm": 25.0, "population_density": 21000, "avg_sell_per_sqm": 2800},
    "Lyon": {"avg_rent_per_sqm": 13.0, "population_density": 10500, "avg_sell_per_sqm": 1400},
    "Marseille": {"avg_rent_per_sqm": 10.0, "population_density": 3500, "avg_sell_per_sqm": 900},
    "Bordeaux": {"avg_rent_per_sqm": 12.0, "population_density": 5000, "avg_sell_per_sqm": 1300},
    "Toulouse": {"avg_rent_per_sqm": 11.0, "population_density": 4000, "avg_sell_per_sqm": 1100},
    "Nantes": {"avg_rent_per_sqm": 12.0, "population_density": 4500, "avg_sell_per_sqm": 1200},
    "Strasbourg": {"avg_rent_per_sqm": 11.5, "population_density": 3400, "avg_sell_per_sqm": 1050},
    "Montpellier": {"avg_rent_per_sqm": 10.5, "population_density": 3200, "avg_sell_per_sqm": 950},
    "Lille": {"avg_rent_per_sqm": 9.5, "population_density": 7000, "avg_sell_per_sqm": 900},
    "Rennes": {"avg_rent_per_sqm": 11.0, "population_density": 3900, "avg_sell_per_sqm": 1050},
    "Nice": {"avg_rent_per_sqm": 15.0, "population_density": 4800, "avg_sell_per_sqm": 1500},
    "Grenoble": {"avg_rent_per_sqm": 10.0, "population_density": 4400, "avg_sell_per_sqm": 950},
    "default": {"avg_rent_per_sqm": 9.0, "population_density": 2000, "avg_sell_per_sqm": 800},
}


@dataclass
class MarketData:
    avg_rent_area: float
    population_density: float
    city_avg_sell_per_sqm: float


def get_market_data(city: str | None) -> MarketData:
    data = CITY_MARKET_DATA.get(city or "", CITY_MARKET_DATA["default"])
    return MarketData(
        avg_rent_area=data["avg_rent_per_sqm"],
        population_density=data["population_density"],
        city_avg_sell_per_sqm=data["avg_sell_per_sqm"],
    )
