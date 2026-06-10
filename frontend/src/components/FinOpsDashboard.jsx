import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, 
  ComposedChart, 
  Line, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  Scatter 
} from 'recharts';

const FinOpsDashboard = () => {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [rcaReport, setRcaReport] = useState("");
  const [runningRca, setRunningRca] = useState(false);

  // Simulating API Ingestion and Synchronization from Module 11/13 endpoints
  useEffect(() => {
    // In production, you would trigger concurrent axios/fetch lookups:
    // Promise.all([fetch('/api/v1/spend?...'), fetch('/api/v1/forecast')])
    
    const mockSynchronizedPayload = [
      { date: '2026-02-12', actual: 1210, predicted: 1200, lower: 1100, upper: 1300, isAnomaly: 0 },
      { date: '2026-02-13', actual: 1190, predicted: 1205, lower: 1105, upper: 1305, isAnomaly: 0 },
      { date: '2026-02-14', actual: 1200, predicted: 1210, lower: 1110, upper: 1310, isAnomaly: 0 },
      // Tier 1/2 consensus anomaly event injected here
      { date: '2026-02-15', actual: 4200, predicted: 1215, lower: 1115, upper: 1315, isAnomaly: 1, type: "Sudden Spike" },
      { date: '2026-02-16', actual: 1250, predicted: 1220, lower: 1120, upper: 1320, isAnomaly: 0 },
      { date: '2026-02-17', actual: 1230, predicted: 1225, lower: 1125, upper: 1325, isAnomaly: 0 },
    ];

    setChartData(mockSynchronizedPayload);
    setLoading(false);
  }, []);

  const triggerAIInvestigation = async (incident) => {
    setSelectedIncident(incident);
    setRunningRca(true);
    setRcaReport("");

    try {
      // Direct integration binding to Module 13 API Framework
      const response = await fetch('http://localhost:8000/api/v1/anomaly/rca', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: incident.date,
          type: incident.type,
          stream: "AWS-COMPUTE"
        })
      });
      const data = await response.json();
      setRcaReport(data.report);
    } catch (err) {
      setRcaReport("Failed to contact backend LangGraph RCA Engine. Ensure api_main.py is live.");
    } finally {
      setRunningRca(false);
    }
  };

  if (loading) return <div className="p-8 text-slate-400">Loading FinOps Metrics Engine...</div>;

  // Isolate anomaly coordinate points natively for the Scatter overlay layer
  const anomalyPoints = chartData.filter(d => d.isAnomaly === 1);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Cloud FinOps Intelligence System</h1>
        <p className="text-slate-400 mt-1">Multi-Vendor Cost Profiling & Automated Machine Learning Forecast Routings</p>
      </header>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 gap-8">
        
        {/* Core Visualization Engine Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4 text-slate-200">Cost Baseline Projections & Outlier Flags (AWS-COMPUTE)</h2>
          
          <div className="h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <XAxis dataKey="date" stroke="#64748b" tickLine={false} />
                <YAxis stroke="#64748b" tickLine={false} unit="$" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
                />
                <Legend verticalAlign="top" height={36} />
                
                {/* 1. Shaded Background Corridor (Forecast Range) */}
                <Area 
                  name="90% Forecast Confidence Range"
                  dataKey="upper"
                  rangeKey="lower"
                  stroke="none"
                  fill="#38bdf8"
                  fillOpacity={0.08}
                />
                
                {/* 2. Ensemble Predicted Center Path */}
                <Line 
                  name="Routed Predictive Forecast"
                  type="monotone"
                  dataKey="predicted"
                  stroke="#38bdf8"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                />
                
                {/* 3. Real-Time Ingested Spend Layer */}
                <Line 
                  name="Actual Unblended Cost"
                  type="monotone"
                  dataKey="actual"
                  stroke="#6366f1"
                  strokeWidth={3}
                  dot={false}
                />
                
                {/* 4. Superimposed Isolated Outlier Flags */}
                <Scatter 
                  name="Verified Cost Anomalies"
                  data={anomalyPoints}
                  fill="#ef4444"
                  shape="circle"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Real-time Incident Interaction Feed */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4 text-slate-200">Active Anomaly Security Feed</h3>
            {chartData.filter(d => d.isAnomaly === 1).map((incident, idx) => (
              <div key={idx} className="border border-red-900/50 bg-red-950/20 rounded-lg p-4 flex flex-col justify-between items-start gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                    <span className="font-bold text-red-400">{incident.type} Detected</span>
                  </div>
                  <p className="text-sm text-slate-400 mt-1">Date: {incident.date} | Variance: +${incident.actual - incident.predicted}</p>
                </div>
                <button 
                  onClick={() => triggerAIInvestigation(incident)}
                  className="px-4 py-2 bg-red-600 hover:bg-red-500 active:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors shadow-lg"
                >
                  Trigger LangGraph Agent RCA
                </button>
              </div>
            ))}
          </div>

          {/* AI Root Cause Analysis Report Panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col">
            <h3 className="text-lg font-semibold mb-4 text-slate-200">LangGraph Agent Control Room</h3>
            {runningRca && (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-400 space-y-2 py-8">
                <span className="text-sm">Agent executing iterative state loops via Gemini...</span>
              </div>
            )}
            {!runningRca && rcaReport && (
              <pre className="flex-1 font-mono text-xs text-emerald-400 bg-slate-950 border border-slate-800 p-4 rounded-lg overflow-auto max-h-64 whitespace-pre-wrap">
                {rcaReport}
              </pre>
            )}
            {!runningRca && !rcaReport && (
              <div className="flex-1 flex items-center justify-center text-slate-500 text-sm py-8 border border-dashed border-slate-800 rounded-lg">
                Select an active incident from the feed to deploy AI agents.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default FinOpsDashboard;