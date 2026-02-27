# BoxInvest

**Garage & parking investment opportunity detector.**

Aggregates listings from multiple sources, enriches them with open market data, and computes a 0–100 **Investment Edge Score** to surface undervalued opportunities.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + SQLAlchemy async |
| Database | PostgreSQL 16 + PostGIS |
| Data pipeline | Pandas + Scikit-learn |
| Background jobs | APScheduler (in-process) |
| Frontend | React 18 + TypeScript + Vite |
| Map | Leaflet + OpenStreetMap (100% free) |
| Scraping | httpx + BeautifulSoup (Leboncoin) |
| Containerization | Docker Compose |

All services are **free / open-source**. No paid API keys required.

---

## Quick Start

```bash
# 1. Clone and copy env
cp .env.example .env

# 2. Start everything
docker-compose up --build

# 3. Open the app
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```

On first start, the backend automatically seeds **500 mock listings** and enriches them.

---

## Seed & Enrich Manually

Via the UI buttons in the top bar, or via the API:

```bash
# Seed mock data
curl -X POST http://localhost:8000/api/jobs/ingest-mock

# Enrich all pending listings
curl -X POST http://localhost:8000/api/jobs/enrich

# Train ML price model (needs ≥100 enriched listings)
curl -X POST http://localhost:8000/api/jobs/train-ml
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/listings` | Paginated listings with filters |
| GET | `/api/listings/geojson` | GeoJSON for map rendering |
| GET | `/api/listings/{id}` | Listing detail + enrichments |
| GET | `/api/analytics/summary` | Dashboard stats |
| GET | `/api/analytics/top` | Top listings by Edge Score |
| POST | `/api/jobs/ingest-mock` | Trigger mock data seed |
| POST | `/api/jobs/enrich` | Trigger enrichment pipeline |
| POST | `/api/jobs/train-ml` | Trigger ML model training |

Interactive docs: http://localhost:8000/docs

---

## Edge Score Algorithm

```
edge_score = (
    price_deviation_score  × 0.30   # % below local / ML fair price
  + yield_score           × 0.25   # gross yield vs area average
  + storage_potential     × 0.20   # height tags, surface ≥ 12m²
  + demand_score          × 0.15   # transport stations, commercial POIs
  + liquidity_score       × 0.10   # photos, security tags, surface
) × 100  →  0–100
```

**Green ≥ 75 · Yellow 55–74 · Orange 35–54 · Red < 35**

---

## Free Data Sources

| Source | Data |
|---|---|
| Overpass API (OSM) | Transport stations, commercial POIs |
| Nominatim | Geocoding |
| data.gouv.fr DVF | Real estate transaction history |
| INSEE | Population density |
| Mock generator | 500 realistic French garage listings |

---

## Project Structure

```
BoxInvest/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── models/       # SQLAlchemy ORM
│   │   ├── schemas/      # Pydantic
│   │   ├── scrapers/     # Leboncoin + mock
│   │   ├── enrichment/   # OSM + market pipeline
│   │   ├── scoring/      # Metrics + Edge Score
│   │   ├── ml/           # Random Forest price estimator
│   │   ├── jobs.py       # Background job implementations
│   │   ├── scheduler.py  # APScheduler setup
│   │   └── main.py       # FastAPI app
│   └── alembic/          # DB migrations
└── frontend/
    └── src/
        ├── api/          # Typed API client
        ├── components/   # Map, Dashboard, Listing
        ├── hooks/        # React Query hooks
        ├── stores/       # Zustand filters state
        └── types/        # TypeScript interfaces
```
