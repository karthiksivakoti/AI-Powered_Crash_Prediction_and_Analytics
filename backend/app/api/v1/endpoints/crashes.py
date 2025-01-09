# app/api/v1/endpoints/crashes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.schemas.crash import Crash, CrashCreate
from app import models
from datetime import datetime

router = APIRouter()

@router.get("/crashes/", response_model=List[Crash])
def read_crashes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    crashes = db.query(models.Crash).offset(skip).limit(limit).all()
    return crashes

@router.get("/crashes/statistics")
def get_crash_statistics(db: Session = Depends(get_db)):
    """Get summary statistics of crashes"""
    total_crashes = db.query(models.Crash).count()
    fatal_crashes = db.query(models.Crash).filter(models.Crash.fatal_count > 0).count()
    injury_crashes = db.query(models.Crash).filter(models.Crash.injury_count > 0).count()
    
    return {
        "total_crashes": total_crashes,
        "fatal_crashes": fatal_crashes,
        "injury_crashes": injury_crashes
    }

@router.get("/crashes/by-hour")
def get_crashes_by_hour(db: Session = Depends(get_db)):
    """Get crash distribution by hour of day"""
    results = db.query(
        models.Crash.hour_of_day,
        func.count(models.Crash.id)
    ).group_by(models.Crash.hour_of_day).all()
    
    return [{"hour": hour, "count": count} for hour, count in results]