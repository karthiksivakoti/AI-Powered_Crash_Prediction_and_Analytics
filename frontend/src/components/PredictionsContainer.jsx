// src/components/PredictionsContainer.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import HotspotMap from './HotspotMap';
import RiskPredictionPanel from './RiskPredictionPanel';

const PredictionsContainer = () => {
  const [hotspots, setHotspots] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch hotspots
        const hotspotsResponse = await axios.get('/api/v1/predict/hotspots');
        setHotspots(hotspotsResponse.data.hotspots);
        
        // Fetch initial predictions for the current time
        const now = new Date();
        const defaultLocation = {
          latitude: 41.2033,
          longitude: -77.1945,
          timestamp: now.toISOString(),
          hour: now.getHours()
        };
        const predictionsResponse = await axios.post('/api/v1/predict/risk', defaultLocation);
        setPredictions([predictionsResponse.data]);
        
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleLocationSelect = async (location) => {
    try {
      const response = await axios.post('/api/v1/predict/risk', {
        latitude: location.latitude,
        longitude: location.longitude,
        timestamp: new Date().toISOString()
      });
      
      setSelectedLocation({
        ...location,
        ...response.data
      });
      
      // Update predictions for next 24 hours at this location
      const hourlyPredictions = await Promise.all(
        Array.from({ length: 24 }, async (_, i) => {
          const timestamp = new Date();
          timestamp.setHours(timestamp.getHours() + i);
          
          const hourResponse = await axios.post('/api/v1/predict/risk', {
            latitude: location.latitude,
            longitude: location.longitude,
            timestamp: timestamp.toISOString()
          });
          
          return {
            ...hourResponse.data,
            hour: timestamp.getHours()
          };
        })
      );
      
      setPredictions(hourlyPredictions);
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-md">
        <div className="text-red-700">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-grow">
        <div className="h-[600px]">
          <HotspotMap
            hotspots={hotspots}
            riskPredictions={predictions}
            onLocationSelect={handleLocationSelect}
          />
        </div>
        <div className="overflow-y-auto">
          <RiskPredictionPanel
            predictions={predictions}
            selectedLocation={selectedLocation}
          />
        </div>
      </div>
    </div>
  );
};

export default PredictionsContainer;