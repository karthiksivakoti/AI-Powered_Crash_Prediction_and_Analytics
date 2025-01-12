# app/api/v1/endpoints/predictions.py
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....services.ml.risk_prediction import RiskPredictor
from ....services.ml.hotspot_detection import HotspotDetector
from typing import Dict, List
from datetime import datetime, timedelta
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize ML models
risk_predictor = RiskPredictor()
hotspot_detector = HotspotDetector()

class LocationRequest(BaseModel):
    latitude: float
    longitude: float
    timestamp: str = None
    weather: str = "1"
    road_condition: str = "1"

@router.post("/predict/risk")
async def predict_risk(
    location: LocationRequest,
    db: Session = Depends(get_db)
):
    """Predict crash risk for a location"""
    try:
        logger.info(f"Received risk prediction request for location: {location.dict()}")
        
        # Load models if not already loaded
        if not risk_predictor.severity_model or not risk_predictor.count_model:
            logger.info("Loading risk prediction models...")
            success = risk_predictor.load_models()
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to load risk prediction models. Please ensure models are trained."
                )

        # Make prediction
        try:
            prediction = risk_predictor.predict_risk(location.dict())
            logger.info(f"Successfully generated prediction: {prediction}")
            return prediction
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error during prediction: {str(e)}"
            )

    except Exception as e:
        logger.error(f"Error in predict_risk endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/train/hotspots")
async def train_hotspot_model(db: Session = Depends(get_db)):
    """Train the hotspot detection model"""
    try:
        logger.info("Starting hotspot model training...")
        results = hotspot_detector.train(db)
        return {
            "message": "Hotspot detection model trained successfully",
            "metrics": results
        }
    except Exception as e:
        logger.error(f"Error training hotspot model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train/risk")
async def train_risk_model(db: Session = Depends(get_db)):
    """Train the risk prediction model"""
    try:
        logger.info("Starting risk model training...")
        results = risk_predictor.train(db)
        return {
            "message": "Risk prediction model trained successfully",
            "metrics": results
        }
    except Exception as e:
        logger.error(f"Error training risk model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))