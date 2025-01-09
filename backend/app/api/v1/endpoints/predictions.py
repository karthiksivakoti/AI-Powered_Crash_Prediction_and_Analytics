# app/api/v1/endpoints/predictions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....services.ml.risk_prediction import RiskPredictor
from ....services.ml.hotspot_detection import HotspotDetector
from typing import Dict, List
from datetime import datetime, timedelta

router = APIRouter()
risk_predictor = RiskPredictor()
hotspot_detector = HotspotDetector()

@router.post("/train/risk")
def train_risk_model(db: Session = Depends(get_db)):
    """Train the risk prediction model"""
    try:
        results = risk_predictor.train(db)
        return {
            "message": "Risk prediction model trained successfully",
            "metrics": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.post("/predict/risk")
def predict_risk(
    location: Dict,
    db: Session = Depends(get_db)
):
    """Predict crash risk for a location"""
    try:
        prediction = risk_predictor.predict_risk(location)
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict/hotspots")
def predict_hotspots(
    time_window: int = 24,
    min_crashes: int = 3,
    db: Session = Depends(get_db)
):
    """Get predicted crash hotspots"""
    try:
        predictions = hotspot_detector.predict_hotspots(
            db,
            time_window=time_window,
            min_crashes=min_crashes
        )
        return {
            "hotspots": predictions,
            "prediction_time": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(hours=time_window)).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))