# app/schemas/crash.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List

class Location(BaseModel):
    longitude: float
    latitude: float

class CrashBase(BaseModel):
    crn: str
    crash_datetime: datetime
    severity: str
    county: str
    municipality: str
    weather: str
    road_condition: str
    fatal_count: int
    injury_count: int

class CrashResponse(CrashBase):
    id: int
    location: Location

    class Config:
        from_attributes = True

class CrashStatistics(BaseModel):
    total_crashes: int
    fatal_crashes: int
    injury_crashes: int
    total_fatalities: int
    total_injuries: int

class CrashFilter(BaseModel):
    severity: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    county: Optional[str] = None
    hour_of_day: Optional[int] = None
    weather: Optional[str] = None
    road_condition: Optional[str] = None