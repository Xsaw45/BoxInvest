"""
Manual job trigger endpoints — useful for dev and debugging.
In production these are also run on schedule via APScheduler.
"""
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.jobs import ingest_mock_data, enrich_pending_listings, retrain_price_model, refresh_dvf_prices, reenrich_all_listings

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/ingest-mock")
async def trigger_mock_ingest(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    background_tasks.add_task(ingest_mock_data, db)
    return {"status": "scheduled", "job": "ingest_mock"}


@router.post("/enrich")
async def trigger_enrich(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    background_tasks.add_task(enrich_pending_listings, db)
    return {"status": "scheduled", "job": "enrich_pending"}


@router.post("/train-ml")
async def trigger_train(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    background_tasks.add_task(retrain_price_model, db)
    return {"status": "scheduled", "job": "train_ml"}


@router.post("/refresh-dvf")
async def trigger_dvf_refresh(background_tasks: BackgroundTasks):
    background_tasks.add_task(refresh_dvf_prices)
    return {"status": "scheduled", "job": "refresh_dvf"}


@router.post("/reenrich-all")
async def trigger_reenrich_all(background_tasks: BackgroundTasks):
    background_tasks.add_task(reenrich_all_listings)
    return {"status": "scheduled", "job": "reenrich_all"}
