import React from 'react';
import Layout from './components/Layout';
import CrashMap from './components/CrashMap';
import CrashStatistics from './components/CrashStatistics';
import AnalyticsPanel from './components/AnalyticsPanel';

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
      </div>
    </Layout>
  );
}

export default App;