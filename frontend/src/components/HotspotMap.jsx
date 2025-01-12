// frontend/src/components/HotspotMap.jsx
import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Map } from 'react-map-gl';
import DeckGL from '@deck.gl/react';
import { HexagonLayer, ScatterplotLayer } from '@deck.gl/layers';
import { HeatmapLayer } from '@deck.gl/aggregation-layers';
import axios from 'axios';
import maplibregl from 'maplibre-gl';
import HotspotPanel from './HotspotPanel';

const INITIAL_VIEW_STATE = {
  longitude: -77.1945,
  latitude: 41.2033,
  zoom: 6.5,
  pitch: 45,  // Added pitch for better 3D visualization
  bearing: 0
};

const MAPSTYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';

const HotspotMap = () => {
  const [hotspots, setHotspots] = useState([]);
  const [selectedHotspot, setSelectedHotspot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeWindow, setTimeWindow] = useState(24);
  const [minCrashes, setMinCrashes] = useState(3);

  useEffect(() => {
    fetchHotspots();
  }, [timeWindow, minCrashes]);

  const fetchHotspots = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:8000/api/v1/analytics/hotspots/current`, {
        params: {
          time_window: timeWindow,
          min_crashes: minCrashes
        }
      });
      
      setHotspots(response.data.hotspots);
    } catch (err) {
      console.error('Error fetching hotspots:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleHotspotClick = (info) => {
    if (info.object) {
      setSelectedHotspot(info.object);
    }
  };

  const layers = [
    // Heatmap layer for general crash density
    new HeatmapLayer({
      id: 'heatmap',
      data: hotspots,
      getPosition: d => [d.location.coordinates[0], d.location.coordinates[1]],
      getWeight: d => d.crash_count,
      radiusPixels: 60,
      intensity: 1,
      threshold: 0.1,
      colorRange: [
        [255, 255, 178],
        [254, 204, 92],
        [253, 141, 60],
        [240, 59, 32],
        [189, 0, 38]
      ]
    }),

    // Hexagon layer for 3D visualization of risk zones
    new HexagonLayer({
      id: 'hexagon',
      data: hotspots,
      getPosition: d => [d.location.coordinates[0], d.location.coordinates[1]],
      radius: 1000,
      elevationScale: 100,
      extruded: true,
      getElevationWeight: d => d.risk_score,
      getFillColor: d => {
        const score = d.points[0]?.risk_score || 0;
        if (score > 0.7) return [255, 0, 0];
        if (score > 0.3) return [255, 140, 0];
        return [255, 255, 0];
      },
      pickable: true,
      onClick: handleHotspotClick
    }),

    // Scatter plot for hotspot centers
    new ScatterplotLayer({
      id: 'hotspots',
      data: hotspots,
      pickable: true,
      opacity: 0.8,
      stroked: true,
      filled: true,
      radiusScale: 6,
      radiusMinPixels: 5,
      radiusMaxPixels: 30,
      lineWidthMinPixels: 1,
      getPosition: d => [d.location.coordinates[0], d.location.coordinates[1]],
      getFillColor: d => {
        if (d.risk_score > 0.7) return [255, 0, 0];
        if (d.risk_score > 0.3) return [255, 140, 0];
        return [255, 255, 0];
      },
      getLineColor: [0, 0, 0],
      onClick: handleHotspotClick
    })
  ];

  return (
    <div className="flex h-full gap-4">
      <div className="flex-grow">
        <Card className="w-full h-full relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 text-white z-10">
              Loading hotspot data...
            </div>
          )}

          {error && (
            <div className="absolute bottom-4 left-4 bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded">
              Error: {error}
            </div>
          )}

          <DeckGL
            initialViewState={INITIAL_VIEW_STATE}
            controller={true}
            layers={layers}
          >
            <Map
              mapLib={maplibregl}
              mapStyle={MAPSTYLE}
              attributionControl={true}
            />
          </DeckGL>

          <div className="absolute top-4 left-4 bg-white p-4 rounded shadow z-10">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Time Window (hours)</label>
                <input
                  type="range"
                  min="1"
                  max="72"
                  value={timeWindow}
                  onChange={(e) => setTimeWindow(parseInt(e.target.value))}
                  className="w-full"
                />
                <span className="text-sm text-gray-500">{timeWindow} hours</span>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Minimum Crashes</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={minCrashes}
                  onChange={(e) => setMinCrashes(parseInt(e.target.value))}
                  className="w-full"
                />
                <span className="text-sm text-gray-500">{minCrashes} crashes</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div className="w-96">
        <HotspotPanel hotspot={selectedHotspot} />
      </div>
    </div>
  );
};

export default HotspotMap;