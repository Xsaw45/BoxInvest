"""
BoxInvest API — FastAPI entrypoint.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.scheduler import scheduler, setup_scheduler
from app.api import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("BoxInvest API starting…")
    await init_db()
    setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started")
    yield
    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("BoxInvest API stopped")


app = FastAPI(
    title="BoxInvest API",
    description="Garage & parking investment opportunity detector",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
