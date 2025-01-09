# app/api/v1/endpoints/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from datetime import datetime, timedelta
from ....core.database import get_db
from ....services.ml.hotspot_detection import HotspotDetector
from ....services.ml.risk_prediction import RiskPredictor
from ....models.crash import Crash
from pydantic import BaseModel

router = APIRouter()

# Initialize ML models
hotspot_detector = HotspotDetector()
risk_predictor = RiskPredictor()

class LocationData(BaseModel):
    latitude: float
    longitude: float
    weather: str = "1"  # Default to clear weather
    road_condition: str = "1"  # Default to dry road
    timestamp: datetime = None

@router.post("/train/hotspots")
def train_hotspot_model(db: Session = Depends(get_db)):
    """Train the hotspot detection model"""
    try:
        results = hotspot_detector.train(db)
        return {
            "message": "Hotspot detection model trained successfully",
            "metrics": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hotspots/current")
def get_current_hotspots(
    time_window: int = 24,
    min_crashes: int = 3,
    db: Session = Depends(get_db)
):
    """Get current crash hotspots"""
    try:
        predictions = hotspot_detector.predict_hotspots(db, time_window)
        return {
            "hotspots": predictions,
            "prediction_time": datetime.now(),
            "valid_until": datetime.now() + timedelta(hours=time_window)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/temporal")
def get_temporal_statistics(db: Session = Depends(get_db)):
    """Get temporal crash statistics"""
    # Hourly distribution
    hourly_stats = db.query(
        Crash.hour_of_day,
        func.count(Crash.id).label('crash_count'),
        func.sum(Crash.fatal_count).label('fatal_count'),
        func.sum(Crash.injury_count).label('injury_count')
    ).group_by(Crash.hour_of_day).all()
    
    # Weather impact
    weather_stats = db.query(
        Crash.weather,
        func.count(Crash.id).label('crash_count'),
        func.sum(Crash.fatal_count).label('fatal_count'),
        func.sum(Crash.injury_count).label('injury_count')
    ).group_by(Crash.weather).all()
    
    return {
        "hourly_distribution": [
            {
                "hour": h.hour_of_day,
                "crashes": h.crash_count,
                "fatalities": h.fatal_count,
                "injuries": h.injury_count
            } for h in hourly_stats
        ],
        "weather_impact": [
            {
                "weather_code": w.weather,
                "crashes": w.crash_count,
                "fatalities": w.fatal_count,
                "injuries": w.injury_count
            } for w in weather_stats
        ]
    }

@router.get("/statistics/spatial")
def get_spatial_statistics(db: Session = Depends(get_db)):
    """Get spatial crash statistics"""
    # County-level statistics
    county_stats = db.query(
        Crash.county,
        func.count(Crash.id).label('crash_count'),
        func.sum(Crash.fatal_count).label('fatal_count'),
        func.sum(Crash.injury_count).label('injury_count')
    ).group_by(Crash.county).all()
    
    # Get crash clusters
    clusters = db.query(
        func.ST_ClusterKMeans(Crash.location, 10).over().label('cluster_id'),
        func.count(Crash.id).label('crash_count'),
        func.sum(Crash.fatal_count).label('fatal_count'),
        func.sum(Crash.injury_count).label('injury_count'),
        func.ST_Centroid(func.ST_Collect(Crash.location)).label('centroid')
    ).group_by('cluster_id').all()
    
    return {
        "county_statistics": [
            {
                "county": c.county,
                "crashes": c.crash_count,
                "fatalities": c.fatal_count,
                "injuries": c.injury_count
            } for c in county_stats
        ],
        "clusters": [
            {
                "cluster_id": c.cluster_id,
                "crash_count": c.crash_count,
                "fatal_count": c.fatal_count,
                "injury_count": c.injury_count,
                "center": {
                    "latitude": db.scalar(func.ST_Y(c.centroid)),
                    "longitude": db.scalar(func.ST_X(c.centroid))
                }
            } for c in clusters
        ]
    }