import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import Papa from 'papaparse';

const StatCard = ({ title, value, description }) => (
  <Card className="bg-white">
    <CardHeader>
      <CardTitle>{title}</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      {description && <p className="text-sm text-gray-500">{description}</p>}
    </CardContent>
  </Card>
);

const CrashStatistics = () => {
  const [stats, setStats] = useState({
    totalCrashes: 0,
    fatalCrashes: 0,
    injuryCrashes: 0,
    vehicleCount: 0,
    totalInjuries: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const files = [
          { name: 'CRASH_2023.csv', path: '/data/CRASH_2023.csv' },
          { name: 'VEHICLE_2023.csv', path: '/data/VEHICLE_2023.csv' },
          { name: 'PERSON_2023.csv', path: '/data/PERSON_2023.csv' }
        ];

        const fileContents = await Promise.all(
          files.map(async file => {
            const response = await fetch(file.path);
            if (!response.ok) {
              throw new Error(`Failed to fetch ${file.name}`);
            }
            const content = await response.text();
            return { name: file.name, content };
          })
        );

        const parsedData = {};
        fileContents.forEach(file => {
          const parsed = Papa.parse(file.content, { 
            header: true, 
            dynamicTyping: true,
            skipEmptyLines: true
          });
          parsedData[file.name] = parsed.data;
        });

        const newStats = {
          totalCrashes: parsedData['CRASH_2023.csv'].length || 0,
          fatalCrashes: parsedData['CRASH_2023.csv'].filter(crash => crash.FATAL_COUNT > 0).length || 0,
          injuryCrashes: parsedData['CRASH_2023.csv'].filter(crash => crash.INJURY_COUNT > 0).length || 0,
          vehicleCount: parsedData['VEHICLE_2023.csv'].length || 0,
          totalInjuries: parsedData['PERSON_2023.csv'].filter(person => person.INJ_SEVERITY > 0).length || 0
        };

        setStats(newStats);
        setLoading(false);
      } catch (error) {
        console.error('Error loading crash statistics:', error);
        setError('Failed to load crash statistics');
        setLoading(false);
      }
    };

    loadStats();
  }, []);

  if (error) {
    return (
      <div className="text-red-500 p-4">
        Error: {error}
      </div>
    );
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
        {[...Array(5)].map((_, i) => (
          <Card key={i} className="bg-white animate-pulse">
            <CardHeader>
              <div className="h-6 bg-gray-200 rounded w-2/3"></div>
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
      <StatCard
        title="Total Crashes"
        value={stats.totalCrashes.toLocaleString()}
        description="Total recorded crashes in 2023"
      />
      <StatCard
        title="Fatal Crashes"
        value={stats.fatalCrashes.toLocaleString()}
        description="Crashes resulting in fatalities"
      />
      <StatCard
        title="Injury Crashes"
        value={stats.injuryCrashes.toLocaleString()}
        description="Crashes resulting in injuries"
      />
      <StatCard
        title="Vehicles Involved"
        value={stats.vehicleCount.toLocaleString()}
        description="Total vehicles in crashes"
      />
      <StatCard
        title="Total Injuries"
        value={stats.totalInjuries.toLocaleString()}
        description="Total number of injuries"
      />
    </div>
  );
};

export default CrashStatistics;