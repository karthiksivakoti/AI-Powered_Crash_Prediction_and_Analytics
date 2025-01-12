# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import crashes, analytics, predictions

api_router = APIRouter()

# Crash data endpoints
api_router.include_router(
    crashes.router,
    prefix="/crashes",
    tags=["crashes"]
)

# Analytics endpoints
api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)

# Predictions endpoints
api_router.include_router(
    predictions.router,
    prefix="/predictions",
    tags=["predictions"]
)