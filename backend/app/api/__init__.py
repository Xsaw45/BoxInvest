from fastapi import APIRouter
from app.api import health, listings, analytics, jobs

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(listings.router)
api_router.include_router(analytics.router)
api_router.include_router(jobs.router)
