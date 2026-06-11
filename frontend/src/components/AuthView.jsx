import React, { useState } from 'react';

// Dynamically fetch the API URL from the environment
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function AuthView({ isLoginView, setIsLoginView, setToken, setOrgId, setViewMode }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [authError, setAuthError] = useState('');

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    const endpoint = isLoginView ? '/api/v1/auth/login' : '/api/v1/auth/signup';
    
    const payload = isLoginView 
      ? { email, password }
      : { email, password, first_name: firstName, last_name: lastName, organization_name: organizationName };

    try {
      // Replaced hardcoded localhost with dynamic API_BASE
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Authentication failed.');

      if (isLoginView) {
        localStorage.setItem('finsight_token', data.access_token);
        localStorage.setItem('finsight_org_id', data.organization_id);
        setToken(data.access_token);
        setOrgId(data.organization_id);
        setViewMode('DASHBOARD');
      } else {
        setIsLoginView(true);
        setAuthError('Organization registered! Please sign in.');
      }
    } catch (err) {
      setAuthError(err.message);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-24">
      <div className="border border-slate-900 bg-slate-900/40 backdrop-blur rounded-2xl p-8 shadow-2xl">
        <h2 className="text-2xl font-bold text-center tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
          {isLoginView ? 'Sign In to Your Workspace' : 'Provision Your Enterprise Tenant'}
        </h2>
        {authError && <div className="mt-4 px-4 py-2 bg-red-950/40 border border-red-900 text-red-400 text-xs font-semibold rounded-lg text-center">{authError}</div>}
        <form onSubmit={handleAuthSubmit} className="space-y-4 mt-6">
          {!isLoginView && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 font-semibold block mb-1">First Name</label>
                  <input type="text" required value={firstName} onChange={e => setFirstName(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100" />
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-semibold block mb-1">Last Name</label>
                  <input type="text" required value={lastName} onChange={e => setLastName(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100" />
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-400 font-semibold block mb-1">Organization Name</label>
                <input type="text" required value={organizationName} onChange={e => setOrganizationName(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100" />
              </div>
            </>
          )}
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Corporate Email Address</label>
            <input type="email" required value={email} onChange={e => setEmail(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100" />
          </div>
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Account Password</label>
            <input type="password" required value={password} onChange={e => setPassword(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100" />
          </div>
          <button type="submit" className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 font-bold rounded-lg text-sm mt-6 transition-all">
            {isLoginView ? 'Establish Connection Access' : 'Initialize Enterprise Space'}
          </button>
        </form>
        <div className="mt-6 text-center">
          <button onClick={() => { setIsLoginView(!isLoginView); setAuthError(''); }} className="text-xs font-semibold text-indigo-400 hover:text-indigo-300">
            {isLoginView ? "Don't have an organization workspace? Initialize here" : 'Already have a secure workspace? Access here'}
          </button>
        </div>
      </div>
    </div>
  );
}