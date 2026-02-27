"""
Random Forest price estimator for garage/box listings.
Wraps sklearn's RandomForestRegressor with persist/load via joblib.
"""
import logging
import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.config import settings

logger = logging.getLogger(__name__)

FEATURES = [
    "surface",
    "lat",
    "lon",
    "city_avg_sell_per_sqm",
    "transport_score",
    "accessibility_score",
    "photos_count",
]

_model: Pipeline | None = None


def _model_path() -> Path:
    return Path(settings.ml_model_path)


def get_model() -> Pipeline | None:
    global _model
    if _model is None and _model_path().exists():
        try:
            _model = joblib.load(_model_path())
            logger.info("ML model loaded from %s", _model_path())
        except Exception as exc:
            logger.warning("Failed to load ML model: %s", exc)
    return _model


def predict_price(
    surface: float | None,
    lat: float | None,
    lon: float | None,
    city_avg_sell_per_sqm: float,
    transport_score: float,
    accessibility_score: float,
    photos_count: int,
) -> float | None:
    model = get_model()
    if model is None:
        return None
    try:
        features = np.array([[
            surface or 15.0,
            lat or 48.85,
            lon or 2.35,
            city_avg_sell_per_sqm,
            transport_score,
            accessibility_score,
            float(photos_count),
        ]])
        prediction = model.predict(features)[0]
        return round(float(prediction), 2)
    except Exception as exc:
        logger.warning("ML prediction failed: %s", exc)
        return None


def train_model(training_data: list[dict]) -> bool:
    """
    Train/retrain the model from a list of dicts with keys matching FEATURES + 'price'.
    Returns True if training succeeded and model was saved.
    """
    if len(training_data) < settings.ml_retrain_min_samples:
        logger.warning(
            "Not enough samples to train (%d < %d)",
            len(training_data),
            settings.ml_retrain_min_samples,
        )
        return False

    try:
        import pandas as pd

        df = pd.DataFrame(training_data).dropna(subset=FEATURES + ["price"])

        X = df[FEATURES].astype(float).values
        y = df["price"].astype(float).values

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("rf", RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=-1,
            )),
        ])
        pipeline.fit(X, y)

        _model_path().parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, _model_path())

        global _model
        _model = pipeline

        logger.info("ML model trained on %d samples and saved to %s", len(df), _model_path())
        return True

    except Exception as exc:
        logger.error("ML training failed: %s", exc)
        return False
