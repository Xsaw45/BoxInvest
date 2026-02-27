"""
Derived financial metrics for a garage/box listing.
All computations are deterministic given the input data.
"""

HIGH_ACCESSIBILITY_TAGS = {"digicode", "télécommande", "électricité", "eau", "vidéosurveillance", "24h/24"}
HEIGHT_TAGS = {"hauteur 2m", "hauteur 2.5m"}
SECURITY_TAGS = {"gardiennage", "vidéosurveillance", "interphone", "digicode"}

# Storage rental premium vs parking (approx. 30% higher yield)
STORAGE_YIELD_PREMIUM = 1.30


def compute_metrics(
    price: float,
    surface: float | None,
    avg_rent_per_sqm: float,
    city_avg_sell_per_sqm: float,
    accessibility_tags: list[str],
    photos_count: int,
) -> dict:
    tags_set = {t.lower() for t in (accessibility_tags or [])}

    # Price per m²
    price_per_sqm = round(price / surface, 2) if surface and surface > 0 else None

    # Estimated monthly rent (range: -15% / +15% around market)
    estimated_rent_low, estimated_rent_high, gross_yield, storage_yield_estimate = (
        None, None, None, None,
    )
    if surface and surface > 0:
        base_rent = avg_rent_per_sqm * surface
        estimated_rent_low = round(base_rent * 0.85, 2)
        estimated_rent_high = round(base_rent * 1.15, 2)

        if price > 0:
            annual_rent = base_rent * 12
            gross_yield = round(annual_rent / price * 100, 3)
            storage_yield_estimate = round(gross_yield * STORAGE_YIELD_PREMIUM, 3)

    # Accessibility score (0–100)
    high_acc = len(tags_set & HIGH_ACCESSIBILITY_TAGS)
    accessibility_score = min(100.0, high_acc * 20.0 + (10.0 if photos_count >= 3 else 0.0))

    # Vertical storage potential (0–100)
    # Based on height tags and surface ≥ 12m²
    has_height = bool(tags_set & HEIGHT_TAGS)
    big_enough = bool(surface and surface >= 12)
    vertical_storage_potential = 0.0
    if has_height and big_enough:
        vertical_storage_potential = 80.0
    elif has_height or big_enough:
        vertical_storage_potential = 45.0
    else:
        vertical_storage_potential = 20.0

    # Liquidity score (0–100): larger cities, more photos, more tags → easier resale
    liquidity_score = min(
        100.0,
        (photos_count * 5.0)
        + len(tags_set & SECURITY_TAGS) * 8.0
        + (20.0 if surface and surface >= 15 else 0.0),
    )

    return {
        "price_per_sqm": price_per_sqm,
        "estimated_rent_low": estimated_rent_low,
        "estimated_rent_high": estimated_rent_high,
        "gross_yield": gross_yield,
        "storage_yield_estimate": storage_yield_estimate,
        "accessibility_score": round(accessibility_score, 2),
        "vertical_storage_potential": round(vertical_storage_potential, 2),
        "liquidity_score": round(liquidity_score, 2),
    }
