import React from 'react';

export default function LandingView({ setViewMode, setIsLoginView }) {
  return (
    <div className="relative overflow-hidden">
      
      {/* BACKGROUND GLOW EFFECTS */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute top-[20%] right-[-10%] w-[40%] h-[40%] bg-cyan-600/10 rounded-full blur-[100px] pointer-events-none"></div>

      <div className="max-w-7xl mx-auto px-6 py-24 lg:py-32 relative z-10">
        
        {/* HERO SECTION */}
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 rounded-full text-xs font-bold tracking-wide text-indigo-400 uppercase mb-8 shadow-[0_0_10px_rgba(99,102,241,0.2)]">
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
            Enterprise Multi-Cloud Intelligence
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white mb-8 leading-[1.1]">
            Stop Guessing Your <br />
            <span className="bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">Multi-Cloud Run-Rates.</span>
          </h1>
          
          <p className="text-slate-400 text-lg md:text-xl mb-10 max-w-2xl mx-auto leading-relaxed">
            FinSight integrates directly into your infrastructure, deploying ensemble machine learning models to isolate structural cost anomalies and LLM agents to automatically deliver engineering root-cause analytics.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button 
              onClick={() => { setViewMode('AUTH'); setIsLoginView(false); }} 
              className="w-full sm:w-auto px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-all shadow-[0_0_20px_rgba(79,70,229,0.4)] border border-indigo-500 flex items-center justify-center gap-2 group">
              Provision Enterprise Tenant
              <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
            </button>
            <button 
              onClick={() => { setViewMode('AUTH'); setIsLoginView(true); }} 
              className="w-full sm:w-auto px-8 py-4 bg-slate-900/50 hover:bg-slate-800 border border-slate-700 text-slate-300 font-bold rounded-xl transition-all backdrop-blur-sm">
              Access Live Dashboard
            </button>
          </div>
        </div>

        {/* TRUST BADGES / STATS */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-24 border-y border-slate-800/50 py-10 bg-slate-900/20 backdrop-blur-sm rounded-3xl">
          <div className="text-center">
            <div className="text-3xl font-black text-white">99.8%</div>
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">Anomaly Detection Rate</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-black text-cyan-400">AWS | GCP</div>
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">Native Provider Support</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-black text-white">&lt; 50ms</div>
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">Telemetry Query Latency</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-black text-indigo-400">LangGraph</div>
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">Autonomous RCA Engine</div>
          </div>
        </div>

        {/* FEATURE GRID */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20">
          <div className="bg-slate-900/40 border border-slate-800 p-8 rounded-3xl hover:border-indigo-500/50 transition-colors group">
            <div className="w-12 h-12 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-6 text-indigo-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Ensemble Forecasting</h3>
            <p className="text-sm text-slate-400 leading-relaxed">We utilize a proprietary blend of Meta Prophet and LightGBM regressors to project 90-day cost vectors with strict confidence intervals.</p>
          </div>
          
          <div className="bg-slate-900/40 border border-slate-800 p-8 rounded-3xl hover:border-cyan-500/50 transition-colors group">
            <div className="w-12 h-12 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-6 text-cyan-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Tri-Layer Threat Detection</h3>
            <p className="text-sm text-slate-400 leading-relaxed">Statistical Z-Scoring, Isolation Forests, and PyTorch LSTM Autoencoders work in tandem to eliminate false positives in your incident feed.</p>
          </div>

          <div className="bg-slate-900/40 border border-slate-800 p-8 rounded-3xl hover:border-emerald-500/50 transition-colors group">
            <div className="w-12 h-12 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-6 text-emerald-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path></svg>
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Generative AI Triage</h3>
            <p className="text-sm text-slate-400 leading-relaxed">Deploy a LangGraph-orchestrated Gemini agent to automatically trace anomalies back to the exact engineering team and environment.</p>
          </div>
        </div>

      </div>
    </div>
  );
}