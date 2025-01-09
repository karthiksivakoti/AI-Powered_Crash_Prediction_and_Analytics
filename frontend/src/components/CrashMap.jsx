import React, { useState, useEffect, useMemo } from 'react';
import { Card } from './ui/card';
import { DeckGL } from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { Map as MapGL } from 'react-map-gl';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import Papa from 'papaparse';

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
  const [selectedTimeRange, setSelectedTimeRange] = useState('all');
  const [selectedSeverity, setSelectedSeverity] = useState('all');

  useEffect(() => {
    const loadData = async () => {
      try {
        const [crashResponse, flagResponse] = await Promise.all([
          fetch('/data/CRASH_2023.csv'),
          fetch('/data/FLAG_2023.csv')
        ]);

        const crashText = await crashResponse.text();
        const flagText = await flagResponse.text();

        const crashResults = Papa.parse(crashText, {
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true
        });

        const flagResults = Papa.parse(flagText, {
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true
        });

        // Create lookup object
        const flagLookup = {};
        flagResults.data.forEach(flag => {
          if (flag.CRN) {
            flagLookup[flag.CRN] = flag;
          }
        });

        const combinedData = crashResults.data
          .filter(crash => {
            const isValid = crash.DEC_LAT && 
                          crash.DEC_LONG && 
                          !isNaN(crash.DEC_LAT) && 
                          !isNaN(crash.DEC_LONG);
            return isValid;
          })
          .map(crash => ({
            ...crash,
            flags: flagLookup[crash.CRN] || {},
            weight: calculateWeight(crash),
            position: [Number(crash.DEC_LONG), Number(crash.DEC_LAT)]
          }));

        setData(combinedData);
        setLoading(false);
      } catch (error) {
        console.error('Error loading data:', error);
        setError(error.message);
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const calculateWeight = (crash) => {
    return (crash.FATAL_COUNT || 0) * 10 + 
           (crash.INJURY_COUNT || 0) * 5 + 
           (crash.POSSIBLE_INJ_COUNT || 0) * 2 + 1;
  };

  const filteredData = useMemo(() => {
    return data.filter(d => {
      if (selectedTimeRange === 'all') return true;
      const hour = d.HOUR_OF_DAY;
      switch(selectedTimeRange) {
        case 'morning':
          return hour >= 6 && hour < 12;
        case 'afternoon':
          return hour >= 12 && hour < 18;
        case 'evening':
          return hour >= 18 && hour < 24;
        case 'night':
          return hour >= 0 && hour < 6;
        default:
          return true;
      }
    }).filter(d => {
      if (selectedSeverity === 'all') return true;
      switch(selectedSeverity) {
        case 'fatal':
          return d.FATAL_COUNT > 0;
        case 'injury':
          return d.INJURY_COUNT > 0;
        default:
          return true;
      }
    });
  }, [data, selectedTimeRange, selectedSeverity]);

  const layers = [
    new ScatterplotLayer({
      id: 'scatter-plot',
      data: filteredData,
      pickable: true,
      opacity: 0.8,
      stroked: true,
      filled: true,
      radiusScale: 10,
      radiusMinPixels: 6,
      radiusMaxPixels: 20,
      lineWidthMinPixels: 1,
      getPosition: d => d.position,
      getFillColor: d => {
        if (d.FATAL_COUNT > 0) return [255, 0, 0, 255];  // Red for fatal
        if (d.INJURY_COUNT > 0) return [255, 140, 0, 255];  // Orange for injury
        return [255, 255, 0, 255];  // Yellow for others
      },
      getLineColor: [0, 0, 0, 255],
      getRadius: d => Math.sqrt(calculateWeight(d)) * 5,
      updateTriggers: {
        getFillColor: [selectedSeverity],
        getRadius: [selectedSeverity]
      }
    })
  ];

  return (
    <Card className="w-full h-full relative">
      <div className="absolute top-4 left-4 z-10 bg-white p-4 rounded shadow-lg">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Time Range</label>
          <select
            value={selectedTimeRange}
            onChange={e => setSelectedTimeRange(e.target.value)}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            <option value="all">All Time</option>
            <option value="morning">Morning (6AM-12PM)</option>
            <option value="afternoon">Afternoon (12PM-6PM)</option>
            <option value="evening">Evening (6PM-12AM)</option>
            <option value="night">Night (12AM-6AM)</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
          <select
            value={selectedSeverity}
            onChange={e => setSelectedSeverity(e.target.value)}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            <option value="all">All Severities</option>
            <option value="fatal">Fatal Crashes</option>
            <option value="injury">Injury Crashes</option>
          </select>
        </div>
      </div>

      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        layers={layers}
        getTooltip={({object}) => object && {
          html: `
            <div style="padding: 10px;">
              <div>Time: ${object.HOUR_OF_DAY}:00</div>
              <div>Fatal: ${object.FATAL_COUNT}</div>
              <div>Injuries: ${object.INJURY_COUNT}</div>
            </div>
          `
        }}
      >
        <MapGL
          mapLib={maplibregl}
          mapStyle={MAPSTYLE}
          attributionControl={true}
        />
      </DeckGL>

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 text-white">
          Loading crash data...
        </div>
      )}

      {error && (
        <div className="absolute bottom-4 left-4 bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded">
          Error: {error}
        </div>
      )}

      <div className="absolute bottom-4 right-4 bg-white p-2 rounded shadow text-xs">
        Points loaded: {filteredData.length}
      </div>
    </Card>
  );
};

export default CrashMap;