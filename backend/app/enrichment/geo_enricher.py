"""
Geo enricher using the Overpass API (OpenStreetMap).
Fetches nearby transport stations and commercial POIs around a listing.
"""
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
RADIUS_M = 800  # search radius in metres


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _overpass_query(query: str) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(OVERPASS_URL, data={"data": query})
        resp.raise_for_status()
        return resp.json()


def _transport_score(station_count: int) -> float:
    """Convert station count within RADIUS_M to a 0–100 score."""
    if station_count == 0:
        return 0.0
    if station_count >= 10:
        return 100.0
    return min(100.0, station_count * 12.0)


def _commercial_density(poi_count: int) -> float:
    """POIs per km² proxy → raw count within 800m radius."""
    return float(poi_count)


async def enrich_geo(lat: float, lon: float) -> dict:
    """
    Returns transport_score (0-100) and commercial_density (float).
    Falls back to 0 values on API errors.
    """
    transport_query = f"""
    [out:json][timeout:10];
    (
      node["public_transport"="station"]({lat - 0.007},{lon - 0.01},{lat + 0.007},{lon + 0.01});
      node["railway"="station"]({lat - 0.007},{lon - 0.01},{lat + 0.007},{lon + 0.01});
      node["railway"="subway_entrance"]({lat - 0.007},{lon - 0.01},{lat + 0.007},{lon + 0.01});
      node["highway"="bus_stop"]({lat - 0.007},{lon - 0.01},{lat + 0.007},{lon + 0.01});
    );
    out count;
    """

    commercial_query = f"""
    [out:json][timeout:10];
    (
      node["shop"]({lat - 0.007},{lon - 0.01},{lat + 0.007},{lon + 0.01});
      node["amenity"~"restaurant|cafe|bank|pharmacy"]({lat - 0.007},{lon - 0.01},{lat + 0.007},{lon + 0.01});
    );
    out count;
    """

    try:
        transport_data = await _overpass_query(transport_query)
        station_count = transport_data.get("elements", [{}])[0].get("tags", {}).get("total", 0)
        if isinstance(station_count, str):
            station_count = int(station_count)
    except Exception as exc:
        logger.warning("Overpass transport query failed: %s", exc)
        station_count = 0

    try:
        commercial_data = await _overpass_query(commercial_query)
        poi_count = commercial_data.get("elements", [{}])[0].get("tags", {}).get("total", 0)
        if isinstance(poi_count, str):
            poi_count = int(poi_count)
    except Exception as exc:
        logger.warning("Overpass commercial query failed: %s", exc)
        poi_count = 0

    return {
        "transport_score": _transport_score(station_count),
        "commercial_density": _commercial_density(poi_count),
    }
