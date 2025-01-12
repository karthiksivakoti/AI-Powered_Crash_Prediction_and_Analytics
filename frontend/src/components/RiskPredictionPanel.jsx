// frontend/src/components/RiskPredictionPanel.jsx
import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import axios from 'axios';

const RiskPredictionPanel = ({ selectedLocation }) => {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Effect to get prediction when location changes
  React.useEffect(() => {
    if (selectedLocation) {
      getPrediction();
    }
  }, [selectedLocation]);

  const getPrediction = async () => {
    if (!selectedLocation) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('http://localhost:8000/api/v1/predictions/predict/risk', {
        latitude: selectedLocation.latitude,
        longitude: selectedLocation.longitude,
        weather: "1",
        road_condition: "1",
        timestamp: new Date().toISOString()
      });

      setPrediction(response.data);
    } catch (err) {
      setError(err.message);
      console.error('Error getting prediction:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'HIGH':
        return 'text-red-600';
      case 'MEDIUM':
        return 'text-yellow-600';
      case 'LOW':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Risk Prediction</CardTitle>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="flex items-center justify-center p-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-100 text-red-700 p-4 rounded-md">
            Error getting prediction: {error}
          </div>
        )}

        {prediction && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Risk Level:</span>
              <span className={`font-bold ${getRiskColor(prediction.risk_level)}`}>
                {prediction.risk_level}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span>Crash Probability:</span>
              <span className="font-bold">
                {(prediction.severe_crash_probability * 100).toFixed(1)}%
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span>Severity Score:</span>
              <span className="font-bold">
                {prediction.expected_severity_score.toFixed(2)}
              </span>
            </div>

            <div className="mt-4 p-4 bg-gray-50 rounded-md">
              <h4 className="font-semibold mb-2">Conditions:</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>Time: {prediction.features_used.time}:00</div>
                <div>Month: {prediction.features_used.month}</div>
                <div>Weather Risk: {prediction.features_used.weather_risk}</div>
                <div>Road Risk: {prediction.features_used.road_risk}</div>
                <div>Weekend: {prediction.features_used.is_weekend ? 'Yes' : 'No'}</div>
              </div>
            </div>
          </div>
        )}

        {!prediction && !loading && !error && (
          <div className="text-gray-500 text-center p-4">
            Select a location on the map to see risk prediction
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RiskPredictionPanel;