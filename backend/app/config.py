from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://boxinvest:boxinvest@localhost:5432/boxinvest"

    scraper_request_delay_seconds: float = 2.0
    scraper_max_listings_per_run: int = 50

    ml_model_path: str = "/app/models/price_estimator.pkl"
    ml_retrain_min_samples: int = 100

    # Edge Score weights (must sum to 1.0)
    weight_price_deviation: float = 0.30
    weight_yield: float = 0.25
    weight_storage_potential: float = 0.20
    weight_demand: float = 0.15
    weight_liquidity: float = 0.10


settings = Settings()
