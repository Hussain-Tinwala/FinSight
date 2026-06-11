import React, { useState, useEffect, useMemo } from 'react';
import { 
  ResponsiveContainer, ComposedChart, Line, Area, XAxis, YAxis, Tooltip, Legend, Scatter, ReferenceLine
} from 'recharts';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// --- UPGRADE 1: CUSTOM ENTERPRISE TOOLTIP ---
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#0a0f1c]/90 backdrop-blur-md border border-slate-700 p-4 rounded-xl shadow-2xl min-w-[200px]">
        <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-3 pb-2 border-b border-slate-800">
          {label}
        </p>
        {payload.map((entry, index) => {
          // Hide the confidence interval area from the tooltip to keep it clean
          // if (entry.dataKey === 'upper' || entry.dataKey === 'lower') return null;
            // Hide the confidence interval area and the raw date from the tooltip to keep it clean
          if (entry.dataKey === 'upper' || entry.dataKey === 'lower' || entry.dataKey === 'date') return null;
          
          return (
            <div key={index} className="flex items-center justify-between gap-4 mb-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full shadow-sm" style={{ backgroundColor: entry.color }} />
                <span className="text-slate-300 text-xs font-medium">{entry.name}</span>
              </div>
              <span className="text-white font-mono font-bold text-sm">
                ${Number(entry.value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          );
        })}
      </div>
    );
  }
  return null;
};

export default function DashboardView({ token, orgId }) {
  const [activeProvider, setActiveProvider] = useState('AWS');
  const [activeCategory, setActiveCategory] = useState('COMPUTE');
  
  const [historyRange, setHistoryRange] = useState('180'); 
  const [forecastRange, setForecastRange] = useState('90');  
  
  const [chartData, setChartData] = useState([]);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [rcaReport, setRcaReport] = useState('');
  const [runningRca, setRunningRca] = useState(false);
  const [historicalCutoff, setHistoricalCutoff] = useState('');

  useEffect(() => {
    fetchTelemetryData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeProvider, activeCategory, historyRange, forecastRange]);

  const fetchTelemetryData = async () => {
    setLoadingMetrics(true);
    setRcaReport('');
    try {
      const endDateStr = '2026-06-30'; 
      const startDateObj = new Date(endDateStr);
      startDateObj.setDate(startDateObj.getDate() - parseInt(historyRange));
      const startDateStr = startDateObj.toISOString().split('T')[0];

      const spendRes = await fetch(
        `${API_BASE}/api/v1/spend?provider=${activeProvider}&category=${activeCategory}&start_date=${startDateStr}&end_date=${endDateStr}`, 
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const actualSpend = await spendRes.json();

      const forecastRes = await fetch(
        `${API_BASE}/api/v1/forecast`, 
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const forecastData = await forecastRes.json();

      const timelineMap = {};
      let maxHistoryDate = '';
      let lastActualValue = null;

      actualSpend.forEach(row => {
        const cleanDate = row.timestamp.split(' ')[0];
        if (cleanDate > maxHistoryDate) maxHistoryDate = cleanDate;
        
        lastActualValue = Number(Number(row.cost).toFixed(2));

        timelineMap[cleanDate] = {
          date: cleanDate,
          actual: lastActualValue,
          anomalyCost: row.is_anomaly === 1 ? lastActualValue : null,
          predicted: null, lower: null, upper: null,
          isAnomaly: row.is_anomaly, type: row.anomaly_type
        };
      });

      setHistoricalCutoff(maxHistoryDate);

      if (maxHistoryDate && timelineMap[maxHistoryDate]) {
         timelineMap[maxHistoryDate].predicted = timelineMap[maxHistoryDate].actual;
      }

      const forecastEndObj = new Date(maxHistoryDate || endDateStr);
      forecastEndObj.setDate(forecastEndObj.getDate() + parseInt(forecastRange));
      const forecastEndStr = forecastEndObj.toISOString().split('T')[0];

      forecastData.forEach(row => {
        if (row.cloud_provider === activeProvider && row.unified_category === activeCategory) {
          const cleanDate = row.date.split(' ')[0];
          
          if (cleanDate > maxHistoryDate && cleanDate <= forecastEndStr) {
            if (timelineMap[cleanDate]) {
              timelineMap[cleanDate].predicted = Number(Number(row.predicted_cost).toFixed(2));
              timelineMap[cleanDate].lower = Number(Number(row.lower_bound).toFixed(2));
              timelineMap[cleanDate].upper = Number(Number(row.upper_bound).toFixed(2));
            } else {
              timelineMap[cleanDate] = {
                date: cleanDate, actual: null, anomalyCost: null,
                predicted: Number(Number(row.predicted_cost).toFixed(2)),
                lower: Number(Number(row.lower_bound).toFixed(2)),
                upper: Number(Number(row.upper_bound).toFixed(2)),
                isAnomaly: 0, type: 'none'
              };
            }
          }
        }
      });

      const balancedTimeline = Object.values(timelineMap);
      balancedTimeline.sort((a, b) => new Date(a.date) - new Date(b.date));
      setChartData(balancedTimeline);
    } catch (err) {
      console.error("Data synchronization engine failure:", err);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const triggerAIInvestigation = async (incident) => {
    setSelectedIncident(incident);
    setRunningRca(true);
    setRcaReport('');
    try {
      const response = await fetch(`${API_BASE}/api/v1/anomaly/rca`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ date: incident.date, type: incident.type, stream: `${activeProvider}-${activeCategory}` })
      });
      const data = await response.json();
      setRcaReport(data.report);
    } catch (err) {
      setRcaReport("Analysis link dropped.");
    } finally {
      setRunningRca(false);
    }
  };

  const triggerLiveHack = async () => {
    try {
      await fetch(`${API_BASE}/api/v1/dev/simulate_anomaly`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      alert("AWS Webhook Simulated! Click 'Re-Sync' to see the live anomaly.");
    } catch (err) {
      console.error(err);
    }
  };

  const kpiData = useMemo(() => {
    let currentSpend = 0;
    let projectedSpend = 0;
    let anomalyCount = 0;

    chartData.forEach(d => {
      if (d.actual) currentSpend += d.actual;
      if (d.predicted && !d.actual) projectedSpend += d.predicted;
      if (d.isAnomaly) anomalyCount += 1;
    });

    return {
      current: currentSpend.toLocaleString('en-US', { style: 'currency', currency: 'USD' }),
      projected: projectedSpend.toLocaleString('en-US', { style: 'currency', currency: 'USD' }),
      anomalies: anomalyCount
    };
  }, [chartData]);

  return (
    <div className="p-4 md:p-8 space-y-8 max-w-7xl mx-auto min-h-screen bg-[#020617] text-slate-200">
      
      {/* 1. TOP CONTROL NAVIGATION */}
      <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center border-b border-slate-800 pb-6 gap-6">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-white bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">FinSight SOC</h2>
          <p className="text-sm text-slate-400 mt-1">Tenant ID: <span className="font-mono text-xs">{orgId}</span></p>
        </div>
        
        <div className="flex flex-wrap gap-3 items-center bg-slate-900/50 p-2 border border-slate-800 rounded-xl backdrop-blur-md">
          <button onClick={triggerLiveHack} className="px-3 py-2 bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20 text-xs font-bold rounded-lg transition-all shadow-[0_0_15px_rgba(239,68,68,0.1)]">
            🔥 Demo Anomaly
          </button>

          <div className="w-px h-6 bg-slate-700 mx-1"></div>

          <select value={activeProvider} onChange={e => setActiveProvider(e.target.value)} className="bg-slate-950 border border-slate-700 text-white text-xs font-semibold rounded-lg px-3 py-2 outline-none focus:border-indigo-500 hover:border-slate-500 transition-colors cursor-pointer">
            <option value="AWS">AWS</option>
            <option value="GCP">GCP</option>
            <option value="Azure">Azure</option>
          </select>
          
          <select value={activeCategory} onChange={e => setActiveCategory(e.target.value)} className="bg-slate-950 border border-slate-700 text-white text-xs font-semibold rounded-lg px-3 py-2 outline-none focus:border-indigo-500 hover:border-slate-500 transition-colors cursor-pointer">
            <option value="COMPUTE">COMPUTE</option>
            <option value="STORAGE">STORAGE</option>
            <option value="NETWORK">NETWORK</option>
          </select>

          <div className="w-px h-6 bg-slate-700 mx-1"></div>

          <select value={historyRange} onChange={e => setHistoryRange(e.target.value)} className="bg-slate-950 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-2 outline-none cursor-pointer">
            <option value="30">Last 30 Days</option>
            <option value="90">Last 90 Days</option>
            <option value="180">Last 6 Months</option>
          </select>

          <select value={forecastRange} onChange={e => setForecastRange(e.target.value)} className="bg-slate-950 border border-slate-700 text-cyan-300 text-xs rounded-lg px-3 py-2 outline-none cursor-pointer">
            <option value="14">Next 14 Days</option>
            <option value="30">Next 30 Days</option>
            <option value="90">Next 90 Days</option>
          </select>

          <button onClick={fetchTelemetryData} className="px-4 py-2 border border-indigo-500/50 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 font-bold text-xs rounded-lg transition-all shadow-[0_0_10px_rgba(99,102,241,0.1)]">
            🔄 Sync
          </button>
        </div>
      </header>

      {/* 2. KPI METRIC CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-2xl flex flex-col justify-center relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl group-hover:bg-indigo-500/20 transition-all"></div>
          <span className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">YTD {activeCategory} Spend</span>
          <span className="text-3xl font-extrabold text-white">{kpiData.current}</span>
        </div>
        
        <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-2xl flex flex-col justify-center relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 rounded-full blur-3xl group-hover:bg-cyan-500/20 transition-all"></div>
          <span className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">{forecastRange}-Day Predicted Run-Rate</span>
          <span className="text-3xl font-extrabold text-cyan-400">{kpiData.projected}</span>
        </div>

        <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-2xl flex flex-col justify-center relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-3xl group-hover:bg-red-500/20 transition-all"></div>
          <span className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Active Security Incidents</span>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-extrabold text-red-400">{kpiData.anomalies}</span>
            {kpiData.anomalies > 0 && <span className="flex h-3 w-3 relative"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span><span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span></span>}
          </div>
        </div>
      </div>

      {loadingMetrics ? (
        <div className="flex items-center justify-center py-32">
          <div className="animate-pulse flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
            <span className="text-slate-500 font-mono text-sm tracking-widest">ESTABLISHING SECURE DATALINK...</span>
          </div>
        </div>
      ) : (
        <>
          {/* --- UPGRADE 2: RECHARTS ENGINE WITH GRADIENTS --- */}
          <div className="border border-slate-800 bg-slate-900/40 rounded-2xl p-6 shadow-xl relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-slate-950/50 pointer-events-none"></div>
            
            <h3 className="text-sm font-bold text-slate-300 mb-6 flex items-center gap-2 relative z-10">
              <span className="w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
              Ensemble Model Predictions & Actuals
            </h3>
            
            <div className="h-[400px] w-full relative z-10">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                  
                  {/* SVG Gradients for beautiful area fills */}
                  <defs>
                    <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                    </linearGradient>
                  </defs>

                  <XAxis dataKey="date" stroke="#475569" fontSize={11} tickLine={false} axisLine={{ stroke: '#334155' }} minTickGap={30} />
                  <YAxis stroke="#475569" fontSize={11} tickLine={false} axisLine={{ stroke: '#334155' }} tickFormatter={(val) => `$${val.toLocaleString()}`} />
                  
                  <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#334155', strokeWidth: 1, strokeDasharray: '4 4' }} />
                  <Legend verticalAlign="top" height={36} fontSize={12} iconType="circle" wrapperStyle={{ color: '#cbd5e1' }} />
                  
                  {/* Confidence Interval (No lines, just fill) */}
                  <Area name="Confidence Bounds" type="monotone" dataKey="upper" rangeKey="lower" stroke="none" fill="url(#colorPredicted)" />
                  
                  {/* Predictive Line */}
                  <Line name="AI Forecast" type="monotone" dataKey="predicted" stroke="#06b6d4" strokeWidth={2.5} strokeDasharray="5 5" dot={false} activeDot={{ r: 6, fill: '#06b6d4', stroke: '#020617', strokeWidth: 2 }} connectNulls />
                  
                  {/* Actual Spend Line & Area */}
                  <Area name="Actual Spend Area" type="monotone" dataKey="actual" stroke="none" fill="url(#colorActual)" />
                  <Line name="Actual Spend" type="monotone" dataKey="actual" stroke="#6366f1" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#6366f1', stroke: '#020617', strokeWidth: 2 }} connectNulls />
                  
                  {historicalCutoff && (
                    <ReferenceLine x={historicalCutoff} stroke="#475569" strokeDasharray="3 3" label={{ value: 'TODAY', fill: '#94a3b8', fontSize: 10, position: 'top' }} />
                  )}
                  
                  {/* Anomalies */}
                  <Scatter name="Consensus Machine Learning Anomaly" dataKey="anomalyCost" fill="#ef4444" shape="circle" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="border border-slate-800 bg-slate-900/40 rounded-2xl p-6 space-y-4 max-h-[500px] overflow-y-auto">
              <h4 className="font-bold text-slate-300 text-sm uppercase tracking-wider flex items-center gap-2">
                <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                Incident Queue
              </h4>
              {chartData.filter(d => d.isAnomaly === 1).map((incident, idx) => (
                <div key={idx} className="border border-red-900/30 bg-red-950/20 hover:bg-red-950/40 transition-colors rounded-xl p-4 flex flex-col justify-between items-start gap-4 group">
                  <div className="w-full flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-bold text-red-400">
                        <span>Threshold Breach ({incident.type})</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-2 font-mono">Date: {incident.date}</p>
                    </div>
                    <span className="text-red-400 font-mono text-sm font-bold bg-red-950 px-2 py-1 rounded border border-red-900/50">
                      ${incident.actual?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <button onClick={() => triggerAIInvestigation(incident)} className="w-full py-2.5 bg-slate-800 hover:bg-indigo-600 text-slate-200 hover:text-white border border-slate-700 hover:border-indigo-500 font-semibold rounded-lg text-xs transition-all flex justify-center items-center gap-2 shadow-[0_0_0_rgba(79,70,229,0)] hover:shadow-[0_0_15px_rgba(79,70,229,0.3)]">
                    Initialize LangGraph Triage
                  </button>
                </div>
              ))}
              {chartData.filter(d => d.isAnomaly === 1).length === 0 && (
                  <div className="text-xs font-mono text-emerald-500/70 p-4 border border-emerald-900/30 bg-emerald-950/20 rounded-xl">SYSTEM NORMAL: Zero active deviations detected.</div>
              )}
            </div>

            <div className="border border-slate-800 bg-[#0a0f1c] rounded-2xl p-6 flex flex-col relative overflow-hidden shadow-inner">
              <h4 className="font-bold text-slate-300 text-sm uppercase tracking-wider mb-4 flex items-center gap-2">
                <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path></svg>
                Autonomous Investigation Terminal
              </h4>
              {runningRca ? (
                <div className="flex-1 flex flex-col items-center justify-center text-indigo-400 text-xs gap-4 py-10 font-mono">
                  <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                  <span className="animate-pulse">Parsing telemetry and executing LLM logic tree...</span>
                </div>
              ) : rcaReport ? (
                <pre className="flex-1 font-mono text-xs text-emerald-400 bg-black/50 p-4 rounded-xl overflow-auto whitespace-pre-wrap max-h-[400px] border border-emerald-900/30 leading-relaxed shadow-inner">{rcaReport}</pre>
              ) : (
                <div className="flex-1 flex items-center justify-center text-xs font-mono text-slate-600 border-2 border-dashed border-slate-800/50 rounded-xl py-12 bg-slate-900/20">
                  &gt; STANDBY: Waiting for manual triage execution...
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}