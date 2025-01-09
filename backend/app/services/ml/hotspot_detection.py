# app/services/ml/hotspot_detection.py
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models.crash import Crash
import joblib
import os

class HotspotDetector:
    def __init__(self, model_dir: str = "models"):
        self.model_dir = os.path.join(os.path.dirname(__file__), model_dir)
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.spatial_scaler = StandardScaler()
        self.temporal_weights = None
        self.clusters = None
        
    def _calculate_temporal_weights(self, df: pd.DataFrame) -> Dict[int, float]:
        """Calculate crash frequency weights by hour"""
        hourly_counts = df.groupby('hour_of_day').size()
        total_crashes = len(df)
        return (hourly_counts / total_crashes).to_dict()
    
    def _get_cluster_stats(self, df: pd.DataFrame, labels: np.ndarray) -> List[Dict]:
        """Calculate statistics for each cluster"""
        clusters = []
        unique_labels = np.unique(labels)
        
        for label in unique_labels:
            if label == -1:  # Skip noise points
                continue
                
            mask = labels == label
            cluster_points = df[mask]
            
            # Calculate cluster center
            center_lat = cluster_points['latitude'].mean()
            center_lon = cluster_points['longitude'].mean()
            
            # Calculate crash statistics
            stats = {
                'cluster_id': int(label),
                'crash_count': len(cluster_points),
                'fatal_count': cluster_points['fatal_count'].sum(),
                'injury_count': cluster_points['injury_count'].sum(),
                'center': {
                    'latitude': float(center_lat),
                    'longitude': float(center_lon)
                },
                'radius': float(np.max(np.sqrt(
                    (cluster_points['latitude'] - center_lat)**2 +
                    (cluster_points['longitude'] - center_lon)**2
                )) * 111)  # Convert to kilometers
            }
            
            # Calculate temporal patterns
            hour_dist = cluster_points.groupby('hour_of_day').size()
            total = len(cluster_points)
            stats['temporal_pattern'] = (hour_dist / total).to_dict()
            
            # Calculate weather patterns
            weather_dist = cluster_points.groupby('weather').size()
            stats['weather_pattern'] = (weather_dist / total).to_dict()
            
            # Calculate road condition patterns
            road_dist = cluster_points.groupby('road_condition').size()
            stats['road_pattern'] = (road_dist / total).to_dict()
            
            clusters.append(stats)
            
        return clusters
    
    def train(self, db: Session) -> Dict:
        """Train the hotspot detection model"""
        print("Starting hotspot detection training...")
        
        # Get crash data
        crashes = db.query(
            Crash,
            func.ST_X(Crash.location).label('longitude'),
            func.ST_Y(Crash.location).label('latitude')
        ).all()
        
        print(f"Loaded {len(crashes)} crash records")
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'crash_datetime': c.Crash.crash_datetime,
            'hour_of_day': c.Crash.hour_of_day,
            'weather': c.Crash.weather,
            'road_condition': c.Crash.road_condition,
            'fatal_count': c.Crash.fatal_count,
            'injury_count': c.Crash.injury_count,
            'longitude': c.longitude,
            'latitude': c.latitude
        } for c in crashes])
        
        # Calculate temporal weights
        self.temporal_weights = self._calculate_temporal_weights(df)
        
        # Prepare spatial features
        X = df[['latitude', 'longitude']].values
        X_scaled = self.spatial_scaler.fit_transform(X)
        
        # Perform DBSCAN clustering
        print("Performing spatial clustering...")
        clustering = DBSCAN(
            eps=0.3,  # ~500 meters in scaled space
            min_samples=5,
            metric='euclidean'
        ).fit(X_scaled)
        
        # Calculate cluster statistics
        print("Calculating cluster statistics...")
        self.clusters = self._get_cluster_stats(df, clustering.labels_)
        
        # Save model data
        print("Saving model data...")
        joblib.dump({
            'spatial_scaler': self.spatial_scaler,
            'temporal_weights': self.temporal_weights,
            'clusters': self.clusters
        }, os.path.join(self.model_dir, 'hotspot_model.joblib'))
        
        return {
            'n_clusters': len(self.clusters),
            'total_crashes_in_hotspots': sum(c['crash_count'] for c in self.clusters),
            'clusters': self.clusters
        }
    
    def predict_hotspots(
        self,
        db: Session,
        time_window: int = 24,
        min_crashes: int = 3
    ) -> List[Dict]:
        """
        Predict crash hotspots for the next time window
        
        Args:
            db: Database session
            time_window: Hours to look ahead
            min_crashes: Minimum crashes to consider a hotspot
            
        Returns:
            List of predicted hotspots with risk scores
        """
        if not self.clusters:
            try:
                model_data = joblib.load(os.path.join(self.model_dir, 'hotspot_model.joblib'))
                self.clusters = model_data['clusters']
                self.temporal_weights = model_data['temporal_weights']
            except Exception as e:
                print(f"Error loading model data: {str(e)}")
                return []
        
        current_time = datetime.now()
        predictions = []
        
        for cluster in self.clusters:
            # Calculate temporal risk based on time of day
            next_hours = [(current_time + timedelta(hours=h)).hour for h in range(time_window)]
            temporal_risk = np.mean([self.temporal_weights.get(h, 0) for h in next_hours])
            
            # Calculate severity risk
            total_crashes = cluster['crash_count']
            severity_risk = (
                (cluster['fatal_count'] * 3 + cluster['injury_count']) / 
                total_crashes if total_crashes > 0 else 0
            )
            
            # Calculate overall risk score
            risk_score = (temporal_risk * 0.4 + severity_risk * 0.6) * total_crashes
            
            if risk_score > min_crashes:
                predictions.append({
                    'location': cluster['center'],
                    'radius_km': cluster['radius'],
                    'risk_score': float(risk_score),
                    'crash_history': {
                        'total_crashes': cluster['crash_count'],
                        'fatal_crashes': cluster['fatal_count'],
                        'injury_crashes': cluster['injury_count']
                    },
                    'patterns': {
                        'temporal': cluster['temporal_pattern'],
                        'weather': cluster['weather_pattern'],
                        'road': cluster['road_pattern']
                    },
                    'prediction_time': current_time.isoformat(),
                    'valid_until': (current_time + timedelta(hours=time_window)).isoformat()
                })
        
        return sorted(predictions, key=lambda x: x['risk_score'], reverse=True)
    
    def load_model(self):
        """Load the trained model"""
        try:
            model_data = joblib.load(os.path.join(self.model_dir, 'hotspot_model.joblib'))
            self.spatial_scaler = model_data['spatial_scaler']
            self.temporal_weights = model_data['temporal_weights']
            self.clusters = model_data['clusters']
            return True
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return False