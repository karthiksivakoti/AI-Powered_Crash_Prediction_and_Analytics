// src/App.jsx
import React from 'react';
import Layout from './components/Layout';
import CrashMap from './components/CrashMap';
import CrashStatistics from './components/CrashStatistics';
import AnalyticsPanel from './components/AnalyticsPanel';
import PredictionsContainer from './components/PredictionsContainer';

function App() {
  return (
    <Layout>
      <div className="space-y-6 p-4">
        <CrashStatistics />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-[800px]">
            <CrashMap />
          </div>
          <div className="overflow-y-auto">
            <AnalyticsPanel />
          </div>
        </div>
        <div className="mt-8">
          <h2 className="text-2xl font-bold mb-4">Predictions & Hotspots</h2>
          <PredictionsContainer />
        </div>
      </div>
    </Layout>
  );
}

export default App;