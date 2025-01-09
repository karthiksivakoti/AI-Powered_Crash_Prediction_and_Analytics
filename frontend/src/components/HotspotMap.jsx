// src/components/HotspotMap.jsx
import React, { useState, useEffect } from 'react';
import { Map } from 'react-map-gl';
import DeckGL from '@deck.gl/react';
import { HexagonLayer, ScatterplotLayer } from '@deck.gl/layers';
import { HeatmapLayer } from '@deck.gl/aggregation-layers';

const INITIAL_VIEW_STATE = {
  longitude: -77.1945,
  latitude: 41.2033,
  zoom: 6.5,
  pitch: 0,
  bearing: 0
};

const MAPSTYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';

const HotspotMap = ({ hotspots, riskPredictions }) => {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  const [hoveredObject, setHoveredObject] = useState(null);

  // Create hotspot layer
  const hotspotLayer = new ScatterplotLayer({
    id: 'hotspots',
    data: hotspots,
    pickable: true,
    opacity: 0.8,
    stroked: true,
    filled: true,
    radiusScale: 6,
    radiusMinPixels: 3,
    radiusMaxPixels: 30,
    lineWidthMinPixels: 1,
    getPosition: d => [d.location.longitude, d.location.latitude],
    getRadius: d => Math.sqrt(d.risk_score) * 100,
    getFillColor: d => [255, 0, 0, 150],
    getLineColor: [0, 0, 0],
    onHover: ({ object }) => setHoveredObject(object)
  });

  // Create heatmap layer for risk predictions
  const heatmapLayer = new HeatmapLayer({
    id: 'heatmap',
    data: riskPredictions,
    getPosition: d => [d.longitude, d.latitude],
    getWeight: d => d.risk_score,
    radiusPixels: 60,
    intensity: 1,
    threshold: 0.05
  });

  const layers = [heatmapLayer, hotspotLayer];

  return (
    <div className="relative w-full h-full">
      <DeckGL
        initialViewState={viewState}
        controller={true}
        layers={layers}
      >
        <Map
          mapStyle={MAPSTYLE}
          preventStyleDiffing={true}
        />
      </DeckGL>

      {hoveredObject && (
        <div className="absolute top-0 left-0 bg-white p-4 m-4 rounded shadow-lg max-w-sm">
          <h3 className="font-bold text-lg">Hotspot Details</h3>
          <p>Risk Score: {hoveredObject.risk_score.toFixed(2)}</p>
          <p>Total Crashes: {hoveredObject.crash_history.total_crashes}</p>
          <p>Fatal Crashes: {hoveredObject.crash_history.fatal_crashes}</p>
          <p>Injury Crashes: {hoveredObject.crash_history.injury_crashes}</p>
          <div className="mt-2">
            <h4 className="font-semibold">Common Factors:</h4>
            <ul className="list-disc list-inside">
              {Object.entries(hoveredObject.patterns.weather)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 3)
                .map(([weather, freq]) => (
                  <li key={weather}>Weather: {weather} ({(freq * 100).toFixed(1)}%)</li>
                ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default HotspotMap;