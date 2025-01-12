# app/services/ml/risk_prediction.py
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.crash import Crash
import joblib
import os

class RiskPredictor:
    def __init__(self, model_dir: str = "models"):
        self.model_dir = os.path.join(os.path.dirname(__file__), model_dir)
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.severity_model = None
        self.count_model = None
        self.scaler = StandardScaler()
        
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features for crash prediction"""
        # Temporal features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day']/24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day']/24)
        df['month'] = pd.to_datetime(df['crash_datetime']).dt.month
        df['month_sin'] = np.sin(2 * np.pi * df['month']/12)
        df['month_cos'] = np.cos(2 * np.pi * df['month']/12)
        df['day_of_week'] = pd.to_datetime(df['crash_datetime']).dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Weather and road conditions
        weather_risk = {
            '1': 1,  # Clear
            '2': 2,  # Cloudy
            '3': 3,  # Rain
            '4': 4,  # Snow
            '5': 4,  # Sleet/Hail
            '6': 3,  # Fog
            '7': 2   # Other
        }
        df['weather_risk'] = df['weather'].map(weather_risk).fillna(1)
        
        road_risk = {
            '1': 1,  # Dry
            '2': 3,  # Wet
            '3': 4,  # Snow/Slush
            '4': 4,  # Ice
            '5': 2   # Other
        }
        df['road_risk'] = df['road_condition'].map(road_risk).fillna(1)
        
        return df
    
    def train(self, db: Session) -> Dict:
        """Train the risk prediction models"""
        print("Starting risk model training...")
        
        # Get crash data with spatial info
        crashes = db.query(
            Crash,
            func.ST_X(Crash.location).label('longitude'),
            func.ST_Y(Crash.location).label('latitude')
        ).all()
        
        print(f"Loaded {len(crashes)} crash records")
        
        # Convert to dataframe
        df = pd.DataFrame([{
            'crash_datetime': c.Crash.crash_datetime,
            'hour_of_day': c.Crash.hour_of_day,
            'weather': c.Crash.weather,
            'road_condition': c.Crash.road_condition,
            'fatal_count': c.Crash.fatal_count,
            'injury_count': c.Crash.injury_count,
            'longitude': c.longitude,
            'latitude': c.latitude,
            'county': c.Crash.county
        } for c in crashes])
        
        print("Converting data and engineering features...")
        
        # Engineer features
        df = self._engineer_features(df)
        
        # Create target variables
        df['severity_score'] = df['fatal_count'] * 3 + df['injury_count']
        df['is_severe'] = (df['severity_score'] > 0).astype(int)
        
        # Prepare features
        feature_cols = [
            'hour_sin', 'hour_cos', 'month_sin', 'month_cos',
            'is_weekend', 'weather_risk', 'road_risk',
            'longitude', 'latitude'
        ]
        # Continuation of RiskPredictor class
        X = df[feature_cols]
        y_severity = df['is_severe']
        y_count = df['severity_score']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        print("Splitting data into train/test sets...")
        X_train, X_test, y_sev_train, y_sev_test, y_cnt_train, y_cnt_test = train_test_split(
            X_scaled, y_severity, y_count, test_size=0.2, random_state=42
        )
        
        # Train severity model (classification)
        print("Training severity classification model...")
        self.severity_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight='balanced',
            random_state=42
        )
        self.severity_model.fit(X_train, y_sev_train)
        
        # Train count model (regression)
        print("Training severity regression model...")
        self.count_model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.count_model.fit(X_train, y_cnt_train)
        
        # Save models
        print("Saving trained models...")
        joblib.dump(self.severity_model, os.path.join(self.model_dir, 'severity_model.joblib'))
        joblib.dump(self.count_model, os.path.join(self.model_dir, 'count_model.joblib'))
        joblib.dump(self.scaler, os.path.join(self.model_dir, 'risk_scaler.joblib'))
        
        # Return evaluation metrics
        return {
            'severity_score': self.severity_model.score(X_test, y_sev_test),
            'count_rmse': np.sqrt(np.mean((self.count_model.predict(X_test) - y_cnt_test) ** 2))
        }
    
    def load_models(self):
        """Load pretrained models"""
        try:
            model_files = {
                'severity_model': os.path.join(self.model_dir, 'severity_model.joblib'),
                'count_model': os.path.join(self.model_dir, 'count_model.joblib'),
                'scaler': os.path.join(self.model_dir, 'risk_scaler.joblib')
            }
            
            # Check if all model files exist
            for path in model_files.values():
                if not os.path.exists(path):
                    print(f"Model file not found: {path}")
                    return False
            
            # Load models
            self.severity_model = joblib.load(model_files['severity_model'])
            self.count_model = joblib.load(model_files['count_model'])
            self.scaler = joblib.load(model_files['scaler'])
            
            print("Models loaded successfully")
            return True
        except Exception as e:
            print(f"Error loading models: {str(e)}")
            return False

    def predict_risk(self, features: Dict) -> Dict:
        """Predict crash risk for given conditions"""
        try:
            # Ensure models are loaded
            if not self.severity_model or not self.count_model or not self.scaler:
                success = self.load_models()
                if not success:
                    raise ValueError("Models not loaded. Please train the models first.")
            
            # Create feature DataFrame with current timestamp if not provided
            current_time = datetime.now()
            timestamp = features.get('timestamp', current_time)
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('T', ' '))
            
            df = pd.DataFrame([{
                'crash_datetime': timestamp,
                'hour_of_day': timestamp.hour,
                'weather': str(features.get('weather', '1')),
                'road_condition': str(features.get('road_condition', '1')),
                'longitude': float(features['longitude']),
                'latitude': float(features['latitude'])
            }])
            
            # Engineer features
            df = self._engineer_features(df)
            
            # Prepare features
            feature_cols = [
                'hour_sin', 'hour_cos', 'month_sin', 'month_cos',
                'is_weekend', 'weather_risk', 'road_risk',
                'longitude', 'latitude'
            ]
            X = df[feature_cols]
            
            # Print feature values for debugging
            print("Feature values:")
            print(X.to_dict('records')[0])
            
            # Check for NaN values
            if X.isna().any().any():
                missing_cols = X.columns[X.isna().any()].tolist()
                raise ValueError(f"Missing values in columns: {missing_cols}")
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Make predictions
            severity_prob = float(self.severity_model.predict_proba(X_scaled)[0][1])
            count_pred = float(max(0, self.count_model.predict(X_scaled)[0]))
            
            return {
                'severe_crash_probability': severity_prob,
                'expected_severity_score': count_pred,
                'risk_level': 'HIGH' if severity_prob > 0.7 else 'MEDIUM' if severity_prob > 0.3 else 'LOW',
                'features_used': {
                    'time': int(df['hour_of_day'].iloc[0]),
                    'weather_risk': float(df['weather_risk'].iloc[0]),
                    'road_risk': float(df['road_risk'].iloc[0]),
                    'is_weekend': bool(df['is_weekend'].iloc[0]),
                    'month': int(timestamp.month)
                }
            }
        except Exception as e:
            print(f"Error in predict_risk: {str(e)}")
            raise