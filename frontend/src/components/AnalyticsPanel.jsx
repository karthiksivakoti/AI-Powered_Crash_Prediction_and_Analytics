import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer
} from 'recharts';
import Papa from 'papaparse';

const AnalyticsPanel = () => {
  const [data, setData] = useState({
    timeDistribution: [],
    severityDistribution: [],
    weatherDistribution: [],
    monthlyTrends: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [crashResponse, flagResponse] = await Promise.all([
          fetch('/data/CRASH_2023.csv'),
          fetch('/data/FLAG_2023.csv')
        ]);

        const crashText = await crashResponse.text();
        const flagText = await flagResponse.text();

        const crashes = Papa.parse(crashText, {
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true
        }).data;

        const flags = Papa.parse(flagText, {
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true
        }).data;

        // Process time distribution
        const timeDistribution = processTimeDistribution(crashes);
        const severityDistribution = processSeverityDistribution(crashes);
        const weatherDistribution = processWeatherDistribution(crashes);
        const monthlyTrends = processMonthlyTrends(crashes);

        setData({
          timeDistribution,
          severityDistribution,
          weatherDistribution,
          monthlyTrends
        });
        setLoading(false);
      } catch (error) {
        console.error('Error loading analytics data:', error);
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const processTimeDistribution = (crashes) => {
    const distribution = Array(24).fill(0);
    crashes.forEach(crash => {
      if (crash.HOUR_OF_DAY >= 0 && crash.HOUR_OF_DAY < 24) {
        distribution[crash.HOUR_OF_DAY]++;
      }
    });
    return distribution.map((count, hour) => ({
      hour: `${hour.toString().padStart(2, '0')}:00`,
      crashes: count
    }));
  };

  const processSeverityDistribution = (crashes) => {
    const distribution = {
      fatal: crashes.filter(c => c.FATAL_COUNT > 0).length,
      injury: crashes.filter(c => c.INJURY_COUNT > 0 && c.FATAL_COUNT === 0).length,
      property: crashes.filter(c => c.FATAL_COUNT === 0 && c.INJURY_COUNT === 0).length
    };
    return Object.entries(distribution).map(([type, count]) => ({
      type,
      count
    }));
  };

  const processWeatherDistribution = (crashes) => {
    const weatherMap = {
      1: 'Clear',
      2: 'Cloudy',
      3: 'Rain',
      4: 'Snow',
      5: 'Sleet/Hail',
      6: 'Fog',
      7: 'Rain & Fog',
      8: 'Snow & Fog',
      98: 'Other',
      99: 'Unknown'
    };
    
    const weatherCounts = {};
    crashes.forEach(crash => {
      const weather = weatherMap[crash.WEATHER1] || 'Unknown';
      weatherCounts[weather] = (weatherCounts[weather] || 0) + 1;
    });
    
    return Object.entries(weatherCounts)
      .map(([weather, count]) => ({ weather, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10); // Top 10 weather conditions
  };

  const processMonthlyTrends = (crashes) => {
    const monthlyData = Array(12).fill(0).map(() => ({
      total: 0,
      fatal: 0,
      injury: 0
    }));

    crashes.forEach(crash => {
      if (crash.CRASH_MONTH >= 1 && crash.CRASH_MONTH <= 12) {
        const idx = crash.CRASH_MONTH - 1;
        monthlyData[idx].total++;
        if (crash.FATAL_COUNT > 0) monthlyData[idx].fatal++;
        if (crash.INJURY_COUNT > 0) monthlyData[idx].injury++;
      }
    });

    return monthlyData.map((data, idx) => ({
      month: new Date(2023, idx).toLocaleString('default', { month: 'short' }),
      ...data
    }));
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-pulse">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="h-64 bg-gray-100" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card className="w-full h-[400px]">
        <CardHeader>
          <CardTitle>Crashes by Time of Day</CardTitle>
        </CardHeader>
        <CardContent className="h-[300px]"> 
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.timeDistribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="crashes" stroke="#8884d8" name="Number of crashes" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="w-full h-[400px]">
        <CardHeader>
          <CardTitle>Monthly Trends</CardTitle>
        </CardHeader>
        <CardContent className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.monthlyTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="total" fill="#8884d8" name="Total Crashes" />
              <Bar dataKey="fatal" fill="#ff0000" name="Fatal Crashes" />
              <Bar dataKey="injury" fill="#ffc658" name="Injury Crashes" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="w-full h-[400px]">
        <CardHeader>
          <CardTitle>Crash Severity Distribution</CardTitle>
        </CardHeader>
        <CardContent className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data.severityDistribution}
                dataKey="count"
                nameKey="type"
                cx="50%"
                cy="50%"
                outerRadius={100}
                fill="#8884d8"
                label={{
                    position: 'outside',
                    offset: 20,
                    fill: '#666'
                }}
              >
                {data.severityDistribution.map((entry, index) => (
                  <Cell key={index} fill={['#ff0000', '#ffc658', '#82ca9d'][index]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="w-full h-[400px]">
        <CardHeader>
          <CardTitle>Weather Conditions</CardTitle>
        </CardHeader>
        <CardContent className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.weatherDistribution} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="weather" type="category" width={100} />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#82ca9d" name="Number of Crashes" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsPanel;