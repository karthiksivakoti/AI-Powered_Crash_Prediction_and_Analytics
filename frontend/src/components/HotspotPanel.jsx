// frontend/src/components/HotspotPanel.jsx
import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const HotspotPanel = ({ hotspot }) => {
  if (!hotspot) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Hotspot Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-gray-500 text-center">
            Select a hotspot on the map to see details
          </div>
        </CardContent>
      </Card>
    );
  }

  const getPatternPercentage = (value) => {
    return (value * 100).toFixed(1) + '%';
  };

  const getRiskColor = (score) => {
    if (score > 0.7) return 'text-red-600';
    if (score > 0.3) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Hotspot Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h3 className="font-semibold mb-2">Location</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>Latitude: {hotspot.location.coordinates[1].toFixed(4)}</div>
            <div>Longitude: {hotspot.location.coordinates[0].toFixed(4)}</div>
          </div>
        </div>

        <div>
          <h3 className="font-semibold mb-2">Statistics</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>Crash Count:</div>
            <div className="font-medium">{hotspot.crash_count}</div>
            <div>Risk Score:</div>
            <div className={`font-medium ${getRiskColor(hotspot.risk_score)}`}>
              {hotspot.risk_score.toFixed(2)}
            </div>
            <div>Radius:</div>
            <div>{(hotspot.radius_km * 1000).toFixed(0)} meters</div>
          </div>
        </div>

        {hotspot.time_patterns && (
          <div>
            <h3 className="font-semibold mb-2">Time Patterns</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {Object.entries(hotspot.time_patterns).map(([period, value]) => (
                <React.Fragment key={period}>
                  <div className="capitalize">{period}:</div>
                  <div>{getPatternPercentage(value)}</div>
                </React.Fragment>
              ))}
            </div>
          </div>
        )}

        {hotspot.weather_patterns && (
          <div>
            <h3 className="font-semibold mb-2">Weather Conditions</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {Object.entries(hotspot.weather_patterns)
                .sort(([, a], [, b]) => b - a)
                .map(([weather, value]) => (
                  <React.Fragment key={weather}>
                    <div>Weather {weather}:</div>
                    <div>{getPatternPercentage(value)}</div>
                  </React.Fragment>
                ))}
            </div>
          </div>
        )}

        {hotspot.road_conditions && (
          <div>
            <h3 className="font-semibold mb-2">Road Conditions</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {Object.entries(hotspot.road_conditions)
                .sort(([, a], [, b]) => b - a)
                .map(([condition, value]) => (
                  <React.Fragment key={condition}>
                    <div>Condition {condition}:</div>
                    <div>{getPatternPercentage(value)}</div>
                  </React.Fragment>
                ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default HotspotPanel;