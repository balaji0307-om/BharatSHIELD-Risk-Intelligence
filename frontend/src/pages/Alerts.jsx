import React, { useState, useEffect } from 'react';
import { AlertTriangle, AlertOctagon, CheckCircle2, RefreshCw, Zap, ShieldCheck } from 'lucide-react';
import AlertCard from '../components/AlertCard';
import { alertsAPI } from '../services/api';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [triggerStatus, setTriggerStatus] = useState(null);

  const fetchAlerts = async () => {
    setIsLoading(true);
    try {
      const data = await alertsAPI.listAlerts();
      setAlerts(data || []);
    } catch (err) {
      console.error('Error fetching alerts:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleAcknowledge = async (alertId) => {
    try {
      await alertsAPI.acknowledgeAlert(alertId, 'Acknowledged by risk officer');
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? { ...a, is_acknowledged: true } : a))
      );
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  const handleCheckSpikes = async () => {
    setTriggerStatus('Checking rolling window baselines...');
    try {
      const res = await alertsAPI.checkSpikes();
      setTriggerStatus(res.message || (res.title ? `Spike Detected: ${res.title}` : 'Check complete'));
      fetchAlerts();
    } catch (err) {
      setTriggerStatus('Error running spike detector');
    } finally {
      setTimeout(() => setTriggerStatus(null), 4000);
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    if (filter === 'ACTIVE') return !a.is_acknowledged;
    if (filter === 'RESOLVED') return a.is_acknowledged;
    if (filter === 'CRITICAL') return a.severity === 'CRITICAL';
    return true;
  });

  const activeCount = alerts.filter((a) => !a.is_acknowledged).length;

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black tracking-tight text-white">
              Fraud Spike & Anomaly Intelligence
            </h1>
            {activeCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                {activeCount} Active
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time rolling window velocity monitoring, transaction surge detection, and automated severity alerts.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleCheckSpikes}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
          >
            <Zap size={14} className="text-amber-400" />
            <span>Evaluate Baseline Now</span>
          </button>

          <button
            onClick={fetchAlerts}
            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700"
            title="Refresh"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {triggerStatus && (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
          {triggerStatus}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        {[
          { id: 'ALL', label: `All Alerts (${alerts.length})` },
          { id: 'ACTIVE', label: `Active Unresolved (${activeCount})` },
          { id: 'CRITICAL', label: 'Critical Only' },
          { id: 'RESOLVED', label: 'Resolved History' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilter(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              filter === tab.id
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Alert Feed */}
      {isLoading ? (
        <div className="py-12 text-center text-slate-400">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          Loading anomaly telemetry...
        </div>
      ) : filteredAlerts.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-xl border border-slate-800">
          <ShieldCheck size={36} className="text-emerald-400 mx-auto mb-3 opacity-80" />
          <h3 className="text-base font-bold text-white">No Anomaly Alerts</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            Rolling window transaction rates and high-risk ratios match expected baseline behavior.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredAlerts.map((alert) => (
            <AlertCard
              key={alert.alert_id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Alerts;
