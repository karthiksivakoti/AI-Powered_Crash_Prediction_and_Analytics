// frontend/src/App.jsx
import React, { useState } from 'react';
import Layout from './components/Layout';
import CrashMap from './components/CrashMap';
import HotspotMap from './components/HotspotMap';
import CrashStatistics from './components/CrashStatistics';
import AnalyticsPanel from './components/AnalyticsPanel';

function App() {
  const [activeMap, setActiveMap] = useState('crashes'); // 'crashes' or 'hotspots'

  return (
    <Layout>
      <div className="space-y-6 p-4">
        {/* Top row - Statistics */}
        <CrashStatistics />
        
        {/* Map Selection */}
        <div className="flex gap-4 items-center">
          <button
            onClick={() => setActiveMap('crashes')}
            className={`px-4 py-2 rounded ${
              activeMap === 'crashes'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            Crash Map
          </button>
          <button
            onClick={() => setActiveMap('hotspots')}
            className={`px-4 py-2 rounded ${
              activeMap === 'hotspots'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            Hotspot Analysis
          </button>
        </div>
        
        {/* Map Display */}
        <div className="h-[800px]">
          {activeMap === 'crashes' ? <CrashMap /> : <HotspotMap />}
        </div>
        
        {/* Bottom row - Analytics */}
        <div className="mt-8">
          <AnalyticsPanel />
        </div>
      </div>
    </Layout>
  );
}

export default App;