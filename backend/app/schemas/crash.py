# app/schemas/crash.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CrashBase(BaseModel):
    crn: str
    crash_datetime: datetime
    county: str
    municipality: str
    weather: Optional[str] = None
    road_condition: Optional[str] = None
    severity: str
    fatal_count: int
    injury_count: int
    latitude: float
    longitude: float

class CrashCreate(CrashBase):
    pass

class Crash(CrashBase):
    id: int

    class Config:
        from_attributes = True