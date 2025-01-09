# app/schemas/analytics.py
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional

class HotspotLocation(BaseModel):
    type: str
    coordinates: List[float]

class Hotspot(BaseModel):
    location: HotspotLocation
    risk_score: float
    crash_count: int
    fatal_count: int
    injury_count: int
    weather_patterns: Dict[str, float]
    road_conditions: Dict[str, float]
    time_patterns: Dict[str, float]

class HotspotResponse(BaseModel):
    hotspots: List[Hotspot]
    prediction_time: datetime
    valid_until: datetime

class TemporalStats(BaseModel):
    hour: int
    crashes: int
    fatalities: int
    injuries: int

class WeatherStats(BaseModel):
    weather_code: str
    crashes: int
    fatalities: int
    injuries: int

class TemporalStatsResponse(BaseModel):
    hourly_distribution: List[TemporalStats]
    weather_impact: List[WeatherStats]

class ClusterLocation(BaseModel):
    latitude: float
    longitude: float

class ClusterStats(BaseModel):
    cluster_id: int
    crash_count: int
    fatal_count: int
    injury_count: int
    center: ClusterLocation

class CountyStats(BaseModel):
    county: str
    crashes: int
    fatalities: int
    injuries: int

class SpatialStatsResponse(BaseModel):
    county_statistics: List[CountyStats]
    clusters: List[ClusterStats]