import React, { useState, useEffect } from 'react';
import LandingView from './components/LandingView';
import AuthView from './components/AuthView';
import DashboardView from './components/DashboardView';

export default function App() {
  const [viewMode, setViewMode] = useState('LANDING');
  const [isLoginView, setIsLoginView] = useState(true);
  
  const [token, setToken] = useState(localStorage.getItem('finsight_token') || '');
  const [orgId, setOrgId] = useState(localStorage.getItem('finsight_org_id') || '');

  // Auto-route users with an active token directly to the dashboard
  useEffect(() => {
    if (token) {
      setViewMode('DASHBOARD');
    }
  }, [token]);

  const handleLogout = () => {
    localStorage.removeItem('finsight_token');
    localStorage.removeItem('finsight_org_id');
    setToken(''); 
    setOrgId(''); 
    setViewMode('LANDING');
  };

  return (
    <div className="min-h-screen bg-[#0a0f1c] text-slate-100 font-sans selection:bg-indigo-500/30">
      
      {/* GLOBAL ENTERPRISE TOP NAVIGATION */}
      <nav className="border-b border-slate-800 bg-[#0a0f1c]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex justify-between items-center shadow-lg shadow-black/20">
        <div className="flex items-center gap-3 cursor-pointer group" onClick={() => setViewMode('LANDING')}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center font-black text-white text-lg shadow-[0_0_15px_rgba(99,102,241,0.4)] group-hover:shadow-[0_0_25px_rgba(6,182,212,0.6)] transition-all duration-300">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
          </div>
          <span className="text-xl font-extrabold tracking-tight text-white group-hover:text-cyan-400 transition-colors">FinSight<span className="text-indigo-500 text-sm ml-1 font-mono tracking-widest uppercase">OS</span></span>
        </div>
        <div>
          {token ? (
            <button onClick={handleLogout} className="px-4 py-2 border border-slate-700 hover:border-slate-500 hover:bg-slate-800 rounded-lg text-sm font-semibold transition-all text-slate-300">Disconnect Environment</button>
          ) : (
            <div className="flex gap-4">
              <button onClick={() => { setViewMode('AUTH'); setIsLoginView(true); }} className="hidden sm:block px-4 py-2 text-sm font-semibold text-slate-300 hover:text-white transition-colors">Sign In</button>
              <button onClick={() => { setViewMode('AUTH'); setIsLoginView(false); }} className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-lg text-sm transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)] hover:shadow-[0_0_25px_rgba(79,70,229,0.5)] border border-indigo-500">Deploy FinSight</button>
            </div>
          )}
        </div>
      </nav>

      {/* VIEW ROUTER */}
      <main className="w-full">
        {viewMode === 'LANDING' && <LandingView setViewMode={setViewMode} setIsLoginView={setIsLoginView} />}
        
        {viewMode === 'AUTH' && (
          <AuthView 
            isLoginView={isLoginView} 
            setIsLoginView={setIsLoginView} 
            setToken={setToken} 
            setOrgId={setOrgId} 
            setViewMode={setViewMode} 
          />
        )}
        
        {viewMode === 'DASHBOARD' && <DashboardView token={token} orgId={orgId} />}
      </main>
      
    </div>
  );
}