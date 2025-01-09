# app/core/config.py
from pydantic import BaseModel

class Settings(BaseModel):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/crash_analytics"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Crash Analytics API"
    
    class Config:
        env_file = ".env"

settings = Settings()