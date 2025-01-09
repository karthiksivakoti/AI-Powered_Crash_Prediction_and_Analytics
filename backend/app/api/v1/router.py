# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import crashes

api_router = APIRouter()
api_router.include_router(crashes.router, tags=["crashes"])