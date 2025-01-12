// frontend/src/components/CrashMap.jsx
import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { DeckGL } from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl';
import maplibregl from 'maplibre-gl';
import Papa from 'papaparse';
import RiskPredictionPanel from './RiskPredictionPanel';

const INITIAL_VIEW_STATE = {
  longitude: -77.1945,
  latitude: 41.2033,
  zoom: 6.5,
  pitch: 0,
  bearing: 0
};

const MAPSTYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';

const CrashMap = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const response = await fetch('/data/CRASH_2023.csv');
      const text = await response.text();
      
      const results = Papa.parse(text, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true
      });

      const validData = results.data
        .filter(row => row.DEC_LAT && row.DEC_LONG)
        .map(row => ({
          position: [row.DEC_LONG, row.DEC_LAT],
          severity: row.FATAL_COUNT > 0 ? 'FATAL' : 
                   row.INJURY_COUNT > 0 ? 'INJURY' : 'PDO',
          color: row.FATAL_COUNT > 0 ? [255, 0, 0] : 
                row.INJURY_COUNT > 0 ? [255, 140, 0] : [255, 255, 0]
        }));

      setData(validData);
      setLoading(false);
    } catch (err) {
      console.error('Error loading crash data:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const handleClick = (info) => {
    if (info.coordinate) {
      const [longitude, latitude] = info.coordinate;
      setSelectedLocation({ latitude, longitude });
    }
  };

  const layers = [
    new ScatterplotLayer({
      id: 'crashes',
      data,
      pickable: true,
      opacity: 0.8,
      stroked: true,
      filled: true,
      radiusScale: 6,
      radiusMinPixels: 3,
      radiusMaxPixels: 30,
      lineWidthMinPixels: 1,
      getPosition: d => d.position,
      getFillColor: d => d.color,
      getLineColor: [0, 0, 0],
    }),

    selectedLocation && new ScatterplotLayer({
      id: 'selected-location',
      data: [selectedLocation],
      pickable: true,
      opacity: 0.8,
      stroked: true,
      filled: true,
      radiusScale: 10,
      radiusMinPixels: 5,
      radiusMaxPixels: 30,
      lineWidthMinPixels: 2,
      getPosition: d => [d.longitude, d.latitude],
      getFillColor: [0, 255, 0],
      getLineColor: [0, 0, 0],
    })
  ];

  return (
    <div className="flex h-full gap-4">
      <div className="flex-grow">
        <Card className="w-full h-full relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 text-white z-10">
              Loading crash data...
            </div>
          )}

          {error && (
            <div className="absolute bottom-4 left-4 bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded">
              Error: {error}
            </div>
          )}

          <DeckGL
            initialViewState={viewState}
            controller={true}
            layers={layers}
            onClick={handleClick}
          >
            <Map
              mapLib={maplibregl}
              mapStyle={MAPSTYLE}
              attributionControl={true}
            />
          </DeckGL>

          <div className="absolute bottom-4 right-4 bg-white p-2 rounded shadow text-xs">
            Points loaded: {data.length}
          </div>
        </Card>
      </div>
      
      <div className="w-96">
        <RiskPredictionPanel selectedLocation={selectedLocation} />
      </div>
    </div>
  );
};

export default CrashMap;