import React, { useState } from 'react';
import { FlaskConical, Play, RotateCcw, AlertTriangle, ArrowRight, ShieldAlert } from 'lucide-react';
import RiskScore from '../components/RiskScore';
import RiskBadge from '../components/RiskBadge';
import { simulatorAPI } from '../services/api';

const RiskSimulator = () => {
  const [params, setParams] = useState({
    transaction_amount: 88500,
    failed_attempts: 4,
    is_new_device: true,
    is_new_location: true,
    transactions_last_5min: 12,
    distance_from_previous: 1450,
    device_age_days: 2,
    payment_method: 'UPI',
  });

  const [simulationResult, setSimulationResult] = useState(null);
  const [previousScore, setPreviousScore] = useState(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const data = await simulatorAPI.assess(params);
      if (simulationResult) {
        setPreviousScore(simulationResult.risk_score);
      }
      setSimulationResult(data);
    } catch (err) {
      console.error('Simulation execution failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setParams({
      transaction_amount: 5000,
      failed_attempts: 0,
      is_new_device: false,
      is_new_location: false,
      transactions_last_5min: 1,
      distance_from_previous: 10,
      device_age_days: 180,
      payment_method: 'UPI',
    });
    setSimulationResult(null);
    setPreviousScore(null);
  };

  const scoreDiff = simulationResult && previousScore !== null
    ? simulationResult.risk_score - previousScore
    : null;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header & Warning Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <FlaskConical className="text-emerald-400" size={26} />
            <h1 className="text-2xl font-bold tracking-tight text-white">
              What-If Risk Simulator
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Simulate parameter shifts to observe live XGBoost + SHAP score reactions in an isolated sandbox.
          </p>
        </div>

        <div className="px-3.5 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono flex items-center gap-2">
          <AlertTriangle size={14} />
          <span>Read-Only Sandbox (No DB / Audit writes)</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Column */}
        <div className="lg:col-span-7 space-y-5 bg-slate-900/40 p-6 rounded-2xl border border-slate-800">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Simulated Transaction Attributes
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Amount */}
            <div>
              <label className="text-xs text-slate-400 font-medium">Transaction Amount (₹)</label>
              <input
                type="number"
                value={params.transaction_amount}
                onChange={(e) => setParams({ ...params, transaction_amount: Number(e.target.value) })}
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>

            {/* Payment Method */}
            <div>
              <label className="text-xs text-slate-400 font-medium">Payment Method</label>
              <select
                value={params.payment_method}
                onChange={(e) => setParams({ ...params, payment_method: e.target.value })}
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
              >
                <option value="UPI">UPI</option>
                <option value="Credit Card">Credit Card</option>
                <option value="Debit Card">Debit Card</option>
                <option value="Net Banking">Net Banking</option>
                <option value="Wallet">Wallet</option>
              </select>
            </div>

            {/* Failed Attempts */}
            <div>
              <div className="flex justify-between text-xs text-slate-400 font-medium">
                <span>Failed Attempts</span>
                <span className="font-mono text-emerald-400">{params.failed_attempts}</span>
              </div>
              <input
                type="range"
                min="0"
                max="8"
                value={params.failed_attempts}
                onChange={(e) => setParams({ ...params, failed_attempts: Number(e.target.value) })}
                className="mt-2 w-full accent-emerald-500"
              />
            </div>

            {/* 5-Min Velocity */}
            <div>
              <div className="flex justify-between text-xs text-slate-400 font-medium">
                <span>5-Min Velocity Bursts</span>
                <span className="font-mono text-emerald-400">{params.transactions_last_5min}</span>
              </div>
              <input
                type="range"
                min="0"
                max="20"
                value={params.transactions_last_5min}
                onChange={(e) => setParams({ ...params, transactions_last_5min: Number(e.target.value) })}
                className="mt-2 w-full accent-emerald-500"
              />
            </div>

            {/* Distance */}
            <div>
              <div className="flex justify-between text-xs text-slate-400 font-medium">
                <span>Distance from Previous (km)</span>
                <span className="font-mono text-emerald-400">{params.distance_from_previous} km</span>
              </div>
              <input
                type="range"
                min="0"
                max="3000"
                step="50"
                value={params.distance_from_previous}
                onChange={(e) => setParams({ ...params, distance_from_previous: Number(e.target.value) })}
                className="mt-2 w-full accent-emerald-500"
              />
            </div>

            {/* Device Age */}
            <div>
              <div className="flex justify-between text-xs text-slate-400 font-medium">
                <span>Device Age (Days)</span>
                <span className="font-mono text-emerald-400">{params.device_age_days}d</span>
              </div>
              <input
                type="range"
                min="0"
                max="365"
                value={params.device_age_days}
                onChange={(e) => setParams({ ...params, device_age_days: Number(e.target.value) })}
                className="mt-2 w-full accent-emerald-500"
              />
            </div>
          </div>

          {/* Toggles */}
          <div className="flex gap-6 pt-2">
            <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-300">
              <input
                type="checkbox"
                checked={params.is_new_device}
                onChange={(e) => setParams({ ...params, is_new_device: e.target.checked })}
                className="w-4 h-4 rounded bg-slate-950 border-slate-800 accent-emerald-500"
              />
              New Device Signature
            </label>

            <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-300">
              <input
                type="checkbox"
                checked={params.is_new_location}
                onChange={(e) => setParams({ ...params, is_new_location: e.target.checked })}
                className="w-4 h-4 rounded bg-slate-950 border-slate-800 accent-emerald-500"
              />
              Unfamiliar Location
            </label>
          </div>

          {/* Buttons */}
          <div className="pt-4 flex items-center gap-3">
            <button
              onClick={runSimulation}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm transition"
            >
              <Play size={16} />
              <span>{loading ? 'Evaluating Model...' : 'Simulate Risk Score'}</span>
            </button>

            <button
              onClick={handleReset}
              className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              title="Reset Controls"
            >
              <RotateCcw size={16} />
            </button>
          </div>
        </div>

        {/* Output Column */}
        <div className="lg:col-span-5 space-y-5">
          <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-800 flex flex-col items-center justify-center text-center space-y-4">
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
              Predicted Risk Reaction
            </div>

            {simulationResult ? (
              <div className="space-y-3 w-full">
                <div className="flex justify-center">
                  <RiskScore score={simulationResult.risk_score} size="lg" />
                </div>

                <div className="flex items-center justify-center gap-2">
                  <RiskBadge level={simulationResult.risk_level} />
                  {scoreDiff !== null && scoreDiff !== 0 && (
                    <span
                      className={`text-xs font-mono font-bold ${
                        scoreDiff > 0 ? 'text-rose-400' : 'text-emerald-400'
                      }`}
                    >
                      {scoreDiff > 0 ? `+${scoreDiff}` : scoreDiff} pts vs prior
                    </span>
                  )}
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-left">
                  <span className="text-slate-500">Recommended Policy:</span>{' '}
                  <span className="font-semibold text-slate-200">
                    {simulationResult.recommended_action?.action || 'Allow'}
                  </span>
                  <p className="text-slate-400 text-[11px] mt-1">
                    {simulationResult.recommended_action?.description}
                  </p>
                </div>
              </div>
            ) : (
              <div className="py-12 text-slate-500 text-xs font-mono">
                Modify attributes and click "Simulate Risk Score" to trigger inference.
              </div>
            )}
          </div>

          {/* Top SHAP Drivers in Simulation (Primary View) */}
          {simulationResult && simulationResult.risk_factors && (
            <div className="bg-slate-900/40 p-5 rounded-2xl border border-slate-800 space-y-3">
              <div className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider flex items-center justify-between">
                <span>Top Model Risk Drivers</span>
                <span className="text-[10px] text-emerald-400">SHAP Engine</span>
              </div>

              <div className="space-y-2">
                {simulationResult.risk_factors.slice(0, 4).map((factor, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-950/40">
                    <span className="text-slate-300">{factor.display_name}</span>
                    <span className={`font-mono font-medium ${factor.direction === 'increases_risk' ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {factor.direction === 'increases_risk' ? '+' : '-'}{Number(factor.contribution).toFixed(1)} pts
                    </span>
                  </div>
                ))}
              </div>

              {/* Collapsible Full Model Weights */}
              {simulationResult.risk_factors.length > 4 && (
                <details className="mt-3 pt-3 border-t border-slate-800/80 text-xs group">
                  <summary className="cursor-pointer text-slate-400 hover:text-emerald-400 font-mono text-[11px] flex items-center justify-between transition select-none">
                    <span>View all {simulationResult.risk_factors.length} SHAP factor contributions</span>
                    <span className="text-[10px] group-open:rotate-180 transition-transform">▼</span>
                  </summary>
                  <div className="space-y-1 mt-2.5 max-h-48 overflow-y-auto pr-1">
                    {simulationResult.risk_factors.slice(4).map((factor, i) => (
                      <div key={i} className="flex items-center justify-between text-[11px] py-1 px-2 rounded bg-slate-950/60 font-mono">
                        <span className="text-slate-400">{factor.display_name || factor.feature}</span>
                        <span className={factor.direction === 'increases_risk' ? 'text-rose-400' : 'text-emerald-400'}>
                          {factor.direction === 'increases_risk' ? '+' : '-'}{Number(factor.contribution).toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskSimulator;
