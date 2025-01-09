# app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:your_password@localhost:5432/crash_analytics"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Crash Analytics API"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

# Create a settings instance
settings = get_settings()