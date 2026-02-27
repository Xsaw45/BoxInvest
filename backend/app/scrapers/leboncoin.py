"""
Leboncoin scraper for garage/box/parking listings.
Uses httpx + BeautifulSoup (lighter than Playwright for listing pages).
Falls back gracefully if blocked.
"""
import asyncio
import logging
import re

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.scrapers.base import BaseScraper, RawListing

logger = logging.getLogger(__name__)

SEARCH_URL = (
    "https://www.leboncoin.fr/recherche"
    "?category=8&owner_type=all&real_estate_type=6,7"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

ACCESSIBILITY_KEYWORDS = [
    "digicode", "télécommande", "pmc", "pmr", "hauteur", "électricité",
    "eau", "bétonné", "gardiennage", "vidéo", "24h", "interphone",
]


class LeboncoinScraper(BaseScraper):
    source_name = "leboncoin"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> str:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        return resp.text

    def _extract_price(self, text: str) -> float | None:
        match = re.search(r"([\d\s]+)\s*€", text.replace("\xa0", " "))
        if match:
            try:
                return float(match.group(1).replace(" ", ""))
            except ValueError:
                return None
        return None

    def _extract_surface(self, text: str) -> float | None:
        match = re.search(r"(\d+[\.,]?\d*)\s*m²", text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                return None
        return None

    def _extract_tags(self, description: str) -> list[str]:
        desc_lower = description.lower()
        return [kw for kw in ACCESSIBILITY_KEYWORDS if kw in desc_lower]

    async def scrape(self, max_listings: int = 50) -> list[RawListing]:
        listings: list[RawListing] = []
        try:
            async with httpx.AsyncClient() as client:
                html = await self._fetch_page(client, SEARCH_URL)
                soup = BeautifulSoup(html, "lxml")

                # Leboncoin listing cards
                cards = soup.select("a[data-test-id='ad']") or soup.select("li[data-qa-id='aditem_container']")

                if not cards:
                    logger.warning("Leboncoin: no listing cards found — site structure may have changed")
                    return []

                for card in cards[:max_listings]:
                    try:
                        title_el = card.select_one("[data-qa-id='aditem_title']") or card.select_one("p.text-title")
                        price_el = card.select_one("[data-qa-id='aditem_price']") or card.select_one("span.price-label")
                        location_el = card.select_one("[data-qa-id='aditem_location']")

                        title = title_el.get_text(strip=True) if title_el else "Garage / Box"
                        price_text = price_el.get_text(strip=True) if price_el else ""
                        price = self._extract_price(price_text)

                        if not price:
                            continue

                        location_text = location_el.get_text(strip=True) if location_el else ""
                        city = location_text.split("/")[0].strip() if location_text else None
                        postal_code = None
                        if location_text and "/" in location_text:
                            postal_code = location_text.split("/")[-1].strip()

                        href = card.get("href", "")
                        url = f"https://www.leboncoin.fr{href}" if href.startswith("/") else href
                        external_id = href.split("/")[-1].split(".")[0] if href else None

                        # Description only available on detail page — skip for now
                        surface = self._extract_surface(title)

                        listings.append(
                            RawListing(
                                title=title,
                                price=price,
                                source="leboncoin",
                                external_id=external_id,
                                url=url,
                                surface=surface,
                                city=city,
                                postal_code=postal_code,
                                photos_count=0,
                            )
                        )

                        await asyncio.sleep(settings.scraper_request_delay_seconds)

                    except Exception as exc:
                        logger.debug("Skipping card: %s", exc)
                        continue

        except httpx.HTTPStatusError as exc:
            logger.error("Leboncoin HTTP error %s: %s", exc.response.status_code, exc)
        except Exception as exc:
            logger.error("Leboncoin scraper failed: %s", exc)

        logger.info("Leboncoin scraper returned %d listings", len(listings))
        return listings
