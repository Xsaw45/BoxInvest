"""
APScheduler job definitions.
Attached to FastAPI's lifespan so the scheduler lives with the app process.
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler():
    from app.jobs import (
        enrich_pending_listings,
        ingest_mock_data,
        retrain_price_model,
        scrape_leboncoin,
    )

    # Seed mock data once at startup (job checks internally if already seeded)
    scheduler.add_job(
        ingest_mock_data,
        trigger="date",
        id="seed_mock_once",
        replace_existing=True,
    )

    # Leboncoin scrape every 6 hours
    scheduler.add_job(
        scrape_leboncoin,
        trigger=IntervalTrigger(hours=6),
        id="scrape_leboncoin",
        replace_existing=True,
    )

    # Enrich new listings every 6 hours (offset 30 min from scrape)
    scheduler.add_job(
        enrich_pending_listings,
        trigger=IntervalTrigger(hours=6, minutes=30),
        id="enrich_pending",
        replace_existing=True,
    )

    # Retrain ML model every Sunday at 03:00
    scheduler.add_job(
        retrain_price_model,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="retrain_ml",
        replace_existing=True,
    )

    logger.info("APScheduler configured with %d jobs", len(scheduler.get_jobs()))
