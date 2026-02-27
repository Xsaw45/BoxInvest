"""
Realistic mock data generator for French garage/box listings.
Generates statistically plausible data reflecting real market conditions.
"""
import random
from faker import Faker
from app.scrapers.base import BaseScraper, RawListing

fake = Faker("fr_FR")
random.seed(42)

# French cities with realistic coordinates and market context
CITIES = [
    {"name": "Paris", "postal_prefix": "75", "lat": 48.8566, "lon": 2.3522, "price_factor": 2.8, "rent_factor": 2.5},
    {"name": "Lyon", "postal_prefix": "69", "lat": 45.7640, "lon": 4.8357, "price_factor": 1.4, "rent_factor": 1.3},
    {"name": "Marseille", "postal_prefix": "13", "lat": 43.2965, "lon": 5.3698, "price_factor": 1.0, "rent_factor": 0.95},
    {"name": "Bordeaux", "postal_prefix": "33", "lat": 44.8378, "lon": -0.5792, "price_factor": 1.3, "rent_factor": 1.2},
    {"name": "Toulouse", "postal_prefix": "31", "lat": 43.6047, "lon": 1.4442, "price_factor": 1.1, "rent_factor": 1.05},
    {"name": "Nantes", "postal_prefix": "44", "lat": 47.2184, "lon": -1.5536, "price_factor": 1.2, "rent_factor": 1.1},
    {"name": "Strasbourg", "postal_prefix": "67", "lat": 48.5734, "lon": 7.7521, "price_factor": 1.1, "rent_factor": 1.0},
    {"name": "Montpellier", "postal_prefix": "34", "lat": 43.6108, "lon": 3.8767, "price_factor": 1.0, "rent_factor": 0.95},
    {"name": "Lille", "postal_prefix": "59", "lat": 50.6292, "lon": 3.0573, "price_factor": 0.9, "rent_factor": 0.85},
    {"name": "Rennes", "postal_prefix": "35", "lat": 48.1173, "lon": -1.6778, "price_factor": 1.1, "rent_factor": 1.0},
    {"name": "Nice", "postal_prefix": "06", "lat": 43.7102, "lon": 7.2620, "price_factor": 1.6, "rent_factor": 1.5},
    {"name": "Grenoble", "postal_prefix": "38", "lat": 45.1885, "lon": 5.7245, "price_factor": 0.95, "rent_factor": 0.9},
]

ACCESSIBILITY_OPTIONS = [
    "digicode", "télécommande", "PMR", "hauteur 2m", "hauteur 2.5m",
    "électricité", "eau", "bétonné", "goudronné", "gardiennage",
    "vidéosurveillance", "accès 24h/24", "interphone",
]

TITLES = [
    "Box fermé {surface}m²",
    "Garage individuel {surface}m² - {city}",
    "Place de parking + box {surface}m²",
    "Garage box {surface}m² centre-ville",
    "Box bétonné {surface}m² accès facile",
    "Parking box fermé {surface}m²",
    "Garage sécurisé {surface}m²",
    "Box stockage {surface}m²",
]


class MockScraper(BaseScraper):
    source_name = "mock"

    async def scrape(self, max_listings: int = 500) -> list[RawListing]:
        listings = []
        for i in range(max_listings):
            city_data = random.choice(CITIES)

            # Surface: mostly 10-25m², some outliers
            surface = round(random.triangular(8, 30, 16), 1)

            # Base price per m²: 500-2000€/m² depending on city
            base_price_per_sqm = random.uniform(500, 2000) * city_data["price_factor"]

            # 15% chance of being "undervalued" (opportunity)
            if random.random() < 0.15:
                price_factor = random.uniform(0.55, 0.75)  # well below market
            else:
                price_factor = random.uniform(0.85, 1.20)

            price = round(surface * base_price_per_sqm * price_factor, -2)  # round to 100
            price = max(2000.0, price)

            # Lat/lon jitter around city center
            lat = city_data["lat"] + random.uniform(-0.08, 0.08)
            lon = city_data["lon"] + random.uniform(-0.10, 0.10)

            tags = random.sample(
                ACCESSIBILITY_OPTIONS,
                k=random.randint(1, 4),
            )

            title_template = random.choice(TITLES)
            title = title_template.format(
                surface=int(surface), city=city_data["name"]
            )

            postal_suffix = str(random.randint(0, 20)).zfill(3)
            postal_code = city_data["postal_prefix"] + postal_suffix

            listings.append(
                RawListing(
                    title=title,
                    price=price,
                    source="mock",
                    external_id=f"mock_{i:05d}",
                    url=None,
                    description=fake.paragraph(nb_sentences=3),
                    surface=surface,
                    city=city_data["name"],
                    postal_code=postal_code,
                    address=fake.street_address(),
                    lat=round(lat, 6),
                    lon=round(lon, 6),
                    photos_count=random.randint(0, 8),
                    floor_level=random.choice([None, None, None, -1, 0, 1]),
                    accessibility_tags=tags,
                )
            )
        return listings
