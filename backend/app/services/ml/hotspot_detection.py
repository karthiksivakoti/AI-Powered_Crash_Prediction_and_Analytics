# app/services/ml/hotspot_detection.py
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.crash import Crash
import joblib
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_to_native_types(obj):
    """Convert numpy/pandas types to native Python types"""
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, (pd.Series, pd.DataFrame)):
        return obj.to_dict()
    elif isinstance(obj, dict):
        return {key: convert_to_native_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_native_types(item) for item in obj]
    return obj

class HotspotDetector:
    def __init__(self, model_dir: str = "models"):
        self.model_dir = os.path.join(os.path.dirname(__file__), model_dir)
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.spatial_scaler = StandardScaler()
        self.temporal_weights = None
        self.clusters = None
    
    def _calculate_temporal_weights(self, df: pd.DataFrame) -> Dict[int, float]:
        """Calculate crash frequency weights by hour"""
        try:
            hourly_counts = df.groupby('hour_of_day').size()
            total_crashes = len(df)
            if total_crashes == 0:
                logger.warning("No crashes found in dataset")
                return {}
            weights = (hourly_counts / total_crashes).to_dict()
            return {int(k): float(v) for k, v in weights.items()}
        except Exception as e:
            logger.error(f"Error calculating temporal weights: {str(e)}")
            raise
    
    def train(self, db: Session) -> Dict:
        """Train the hotspot detection model"""
        try:
            logger.info("Starting hotspot detection training...")
            
            # Get crash data
            crashes = db.query(
                Crash,
                func.ST_X(Crash.location).label('longitude'),
                func.ST_Y(Crash.location).label('latitude')
            ).all()
            
            logger.info(f"Loaded {len(crashes)} crash records")
            if not crashes:
                raise ValueError("No crash data found in database")
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'crash_datetime': c.Crash.crash_datetime,
                'hour_of_day': c.Crash.hour_of_day,
                'weather': c.Crash.weather,
                'road_condition': c.Crash.road_condition,
                'fatal_count': c.Crash.fatal_count,
                'injury_count': c.Crash.injury_count,
                'longitude': float(c.longitude) if c.longitude else None,
                'latitude': float(c.latitude) if c.latitude else None
            } for c in crashes])
            
            df = df.dropna(subset=['longitude', 'latitude'])
            
            logger.info("Calculating temporal weights...")
            self.temporal_weights = self._calculate_temporal_weights(df)
            
            # Prepare spatial features
            logger.info("Preparing spatial features...")
            coords = df[['latitude', 'longitude']].values
            if len(coords) < 2:
                raise ValueError("Not enough data points for clustering")
            
            X_scaled = self.spatial_scaler.fit_transform(coords)
            
            # Perform DBSCAN clustering
            logger.info("Performing spatial clustering...")
            clustering = DBSCAN(
                eps=0.01,  # Approximately 1km
                min_samples=3,
                metric='euclidean'
            ).fit(X_scaled)
            
            # Count clusters
            n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
            logger.info(f"Found {n_clusters} clusters")
            
            # Calculate cluster statistics
            clusters = []
            for label in range(n_clusters):
                mask = clustering.labels_ == label
                if not any(mask):
                    continue
                    
                cluster_points = df[mask]
                center_lat = float(cluster_points['latitude'].mean())
                center_lon = float(cluster_points['longitude'].mean())
                
                clusters.append({
                    'cluster_id': int(label),
                    'crash_count': int(len(cluster_points)),
                    'fatal_count': int(cluster_points['fatal_count'].sum()),
                    'injury_count': int(cluster_points['injury_count'].sum()),
                    'center': {
                        'latitude': center_lat,
                        'longitude': center_lon
                    },
                    'radius_km': float(np.max(np.sqrt(
                        (cluster_points['latitude'] - center_lat)**2 +
                        (cluster_points['longitude'] - center_lon)**2
                    )) * 111)
                })
            
            self.clusters = clusters
            
            # Save model data
            logger.info("Saving model data...")
            model_data = {
                'spatial_scaler': self.spatial_scaler,
                'temporal_weights': self.temporal_weights,
                'clusters': self.clusters
            }
            joblib.dump(model_data, os.path.join(self.model_dir, 'hotspot_model.joblib'))
            
            return {
                'n_clusters': len(clusters),
                'total_crashes_in_hotspots': sum(c['crash_count'] for c in clusters),
                'hotspots': convert_to_native_types(clusters)
            }
            
        except Exception as e:
            logger.error(f"Error training hotspot model: {str(e)}")
            raise
    
    def predict_hotspots(
        self,
        db: Session,
        time_window: int = 24,
        min_crashes: int = 3
    ) -> List[Dict]:
        """Predict crash hotspots"""
        try:
            if not self.clusters:
                logger.info("Loading saved model...")
                model_data = joblib.load(os.path.join(self.model_dir, 'hotspot_model.joblib'))
                self.clusters = model_data['clusters']
                self.temporal_weights = model_data['temporal_weights']
            
            current_time = datetime.now()
            predictions = []
            
            for cluster in self.clusters:
                # Calculate risk score
                base_risk = (cluster['fatal_count'] * 3 + cluster['injury_count']) / max(cluster['crash_count'], 1)
                temporal_risk = sum(self.temporal_weights.get(h, 0) for h in range(24)) / 24
                
                risk_score = base_risk * temporal_risk * cluster['crash_count']
                
                if risk_score > min_crashes:
                    predictions.append({
                        'location': cluster['center'],
                        'risk_score': float(risk_score),
                        'radius_km': float(cluster['radius_km']),
                        'crash_count': int(cluster['crash_count']),
                        'prediction_time': current_time.isoformat(),
                        'valid_until': (current_time + timedelta(hours=time_window)).isoformat()
                    })
            
            return sorted(predictions, key=lambda x: x['risk_score'], reverse=True)
        
        except Exception as e:
            logger.error(f"Error predicting hotspots: {str(e)}")
            raise