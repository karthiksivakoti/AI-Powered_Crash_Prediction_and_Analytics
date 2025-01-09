# app/api/v1/endpoints/crashes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text, case
from typing import List, Optional
from datetime import datetime, timedelta
from ....core.database import get_db
from ....models.crash import Crash
from ....schemas.crash import CrashResponse, CrashStatistics, CrashFilter

router = APIRouter()

@router.get("/", response_model=List[CrashResponse])
def get_crashes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    county: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get crashes with optional filtering
    """
    query = db.query(
        Crash,
        func.ST_X(Crash.location).label('longitude'),
        func.ST_Y(Crash.location).label('latitude')
    )
    
    # Apply filters
    if severity:
        query = query.filter(Crash.severity == severity)
    if start_date:
        query = query.filter(Crash.crash_datetime >= start_date)
    if end_date:
        query = query.filter(Crash.crash_datetime <= end_date)
    if county:
        query = query.filter(Crash.county == county)
    
    # Execute query with pagination
    crashes = query.offset(skip).limit(limit).all()
    
    # Format response
    return [
        {
            "id": crash.Crash.id,
            "crn": crash.Crash.crn,
            "crash_datetime": crash.Crash.crash_datetime,
            "severity": crash.Crash.severity,
            "location": {
                "longitude": crash.longitude,
                "latitude": crash.latitude
            },
            "county": crash.Crash.county,
            "municipality": crash.Crash.municipality,
            "weather": crash.Crash.weather,
            "road_condition": crash.Crash.road_condition,
            "fatal_count": crash.Crash.fatal_count,
            "injury_count": crash.Crash.injury_count
        }
        for crash in crashes
    ]

@router.get("/statistics/summary", response_model=CrashStatistics)
def get_crash_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get summary statistics of crashes
    """
    query = db.query(Crash)
    
    if start_date:
        query = query.filter(Crash.crash_datetime >= start_date)
    if end_date:
        query = query.filter(Crash.crash_datetime <= end_date)
    
    stats = query.with_entities(
        func.count().label('total_crashes'),
        func.sum(Crash.fatal_count).label('total_fatalities'),
        func.sum(Crash.injury_count).label('total_injuries'),
        func.count(case([(Crash.fatal_count > 0, 1)])).label('fatal_crashes'),
        func.count(case([(Crash.injury_count > 0, 1)])).label('injury_crashes')
    ).first()
    
    return {
        "total_crashes": stats.total_crashes,
        "fatal_crashes": stats.fatal_crashes,
        "injury_crashes": stats.injury_crashes,
        "total_fatalities": stats.total_fatalities or 0,
        "total_injuries": stats.total_injuries or 0
    }

@router.get("/heatmap", response_model=List[dict])
def get_crash_heatmap(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get crash data for heatmap visualization
    """
    query = db.query(
        func.ST_X(Crash.location).label('longitude'),
        func.ST_Y(Crash.location).label('latitude'),
        func.count().label('weight')
    )
    
    if start_date:
        query = query.filter(Crash.crash_datetime >= start_date)
    if end_date:
        query = query.filter(Crash.crash_datetime <= end_date)
    
    # Group by location with some tolerance
    query = query.group_by(
        func.round(func.ST_X(Crash.location).cast('numeric'), 4),
        func.round(func.ST_Y(Crash.location).cast('numeric'), 4)
    )
    
    points = query.all()
    
    return [
        {
            "longitude": point.longitude,
            "latitude": point.latitude,
            "weight": point.weight
        }
        for point in points
    ]

@router.get("/counties", response_model=List[dict])
def get_county_statistics(db: Session = Depends(get_db)):
    """
    Get crash statistics by county
    """
    stats = db.query(
        Crash.county,
        func.count().label('total_crashes'),
        func.sum(Crash.fatal_count).label('fatalities'),
        func.sum(Crash.injury_count).label('injuries')
    ).group_by(Crash.county).all()
    
    return [
        {
            "county": stat.county,
            "total_crashes": stat.total_crashes,
            "fatalities": stat.fatalities or 0,
            "injuries": stat.injuries or 0
        }
        for stat in stats
    ]

@router.get("/daily", response_model=List[dict])
def get_daily_trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get daily crash trends
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    trends = db.query(
        func.date_trunc('day', Crash.crash_datetime).label('date'),
        func.count().label('crashes'),
        func.sum(Crash.fatal_count).label('fatalities'),
        func.sum(Crash.injury_count).label('injuries')
    ).filter(
        Crash.crash_datetime >= cutoff_date
    ).group_by(
        func.date_trunc('day', Crash.crash_datetime)
    ).order_by('date').all()
    
    return [
        {
            "date": trend.date.strftime('%Y-%m-%d'),
            "crashes": trend.crashes,
            "fatalities": trend.fatalities or 0,
            "injuries": trend.injuries or 0
        }
        for trend in trends
    ]