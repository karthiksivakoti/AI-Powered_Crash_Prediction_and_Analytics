// src/components/RiskPredictionPanel.jsx
import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell
} from 'recharts';

const RISK_COLORS = {
  HIGH: '#ff0000',
  MEDIUM: '#ffa500',
  LOW: '#00ff00'
};

const RiskPredictionPanel = ({ predictions, selectedLocation }) => {
  // Process predictions data for visualization
  const hourlyRiskData = Array.from({ length: 24 }, (_, hour) => {
    const risk = predictions.find(p => p.hour === hour) || { risk_level: 'LOW', probability: 0 };
    return {
      hour: `${hour}:00`,
      risk: risk.probability * 100,
      riskLevel: risk.risk_level
    };
  });

  const riskDistribution = Object.entries(
    predictions.reduce((acc, p) => {
      acc[p.risk_level] = (acc[p.risk_level] || 0) + 1;
      return acc;
    }, {})
  ).map(([level, count]) => ({
    name: level,
    value: count
  }));

  return (
    <div className="space-y-6 p-4">
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Risk Predictions</h2>
        
        {selectedLocation && (
          <div className="mb-4">
            <h3 className="font-medium">Selected Location</h3>
            <p>Latitude: {selectedLocation.latitude.toFixed(4)}</p>
            <p>Longitude: {selectedLocation.longitude.toFixed(4)}</p>
            <div className="mt-2">
              <div className={`
                inline-flex items-center px-3 py-1 rounded-full text-sm
                ${selectedLocation.risk_level === 'HIGH' ? 'bg-red-100 text-red-800' :
                  selectedLocation.risk_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-green-100 text-green-800'}
              `}>
                {selectedLocation.risk_level} Risk
              </div>
            </div>
          </div>
        )}

        <div className="h-64">
          <BarChart
            width={500}
            height={250}
            data={hourlyRiskData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis label={{ value: 'Risk %', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="risk" name="Risk Level">
              {hourlyRiskData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={RISK_COLORS[entry.riskLevel]} />
              ))}
            </Bar>
          </BarChart>
        </div>

        <div className="h-64 mt-6">
          <PieChart width={300} height={250}>
            <Pie
              data={riskDistribution}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label
            >
              {riskDistribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={RISK_COLORS[entry.name]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </div>
      </div>

      {selectedLocation?.contributing_factors && (
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-2">Contributing Factors</h3>
          <div className="space-y-2">
            {Object.entries(selectedLocation.contributing_factors).map(([factor, value]) => (
              <div key={factor} className="flex justify-between items-center">
                <span className="text-gray-600">{factor}</span>
                <span className="font-medium">{(value * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskPredictionPanel;