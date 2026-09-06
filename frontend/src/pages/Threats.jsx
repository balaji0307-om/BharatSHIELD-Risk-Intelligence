import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Siren, ShieldAlert, ArrowUpRight, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import RiskBadge from '../components/RiskBadge';

const Threats = () => {
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState(new Date());
  const navigate = useNavigate();

  const fetchThreats = async () => {
    try {
      const res = await axios.get('/api/threats/live?limit=30');
      setThreats(res.data || []);
      setLastRefreshed(new Date());
    } catch (err) {
      console.error('Error fetching live threats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchThreats();
    const interval = setInterval(fetchThreats, 10000); // 10s auto-refresh
    return () => clearInterval(interval);
  }, []);

  const criticalCount = threats.filter((t) => t.risk_level === 'CRITICAL').length;
  const highCount = threats.filter((t) => t.risk_level === 'HIGH').length;
  const mediumCount = threats.filter((t) => t.risk_level === 'MEDIUM').length;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500"></span>
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Siren className="text-rose-400" size={24} />
              Live Threat Feed
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time transaction risk streams detected by BharatSHIELD ML engines.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3.5 py-1.5 rounded-lg text-xs font-mono text-slate-400">
            <RefreshCw size={14} className="animate-spin text-emerald-400" />
            <span>Refreshed {lastRefreshed.toLocaleTimeString()}</span>
          </div>
          <button
            onClick={fetchThreats}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition"
          >
            Poll Now
          </button>
        </div>
      </div>

      {/* Summary Counter Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-900/40 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-rose-400 uppercase tracking-wider">Critical Threats</div>
            <div className="text-2xl font-black text-rose-200 mt-1">{criticalCount}</div>
          </div>
          <ShieldAlert className="text-rose-500" size={28} />
        </div>
        <div className="p-4 rounded-xl bg-orange-950/20 border border-orange-900/40 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-orange-400 uppercase tracking-wider">High Risk Ingress</div>
            <div className="text-2xl font-black text-orange-200 mt-1">{highCount}</div>
          </div>
          <ShieldAlert className="text-orange-500" size={28} />
        </div>
        <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-900/40 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Medium Watchlist</div>
            <div className="text-2xl font-black text-amber-200 mt-1">{mediumCount}</div>
          </div>
          <ShieldAlert className="text-amber-500" size={28} />
        </div>
      </div>

      {/* Feed Stream */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-12 text-center text-slate-500 font-mono text-sm">Streaming threat vectors...</div>
        ) : threats.length === 0 ? (
          <div className="p-12 text-center text-slate-400 bg-slate-900/40 border border-slate-800 rounded-xl">
            No active threat flags detected. All incoming transactions operating below alert threshold.
          </div>
        ) : (
          threats.map((threat) => {
            const isCritical = threat.risk_level === 'CRITICAL';
            const isHigh = threat.risk_level === 'HIGH';
            const borderClass = isCritical
              ? 'border-l-4 border-l-rose-500 bg-rose-950/10'
              : isHigh
              ? 'border-l-4 border-l-orange-500 bg-orange-950/10'
              : 'border-l-4 border-l-amber-500 bg-slate-900/40';

            return (
              <div
                key={threat.transaction_id}
                onClick={() => navigate(`/transactions/${threat.transaction_id}`)}
                className={`p-4 rounded-xl border border-slate-800/80 hover:border-slate-700 transition cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 ${borderClass}`}
              >
                <div className="flex items-center gap-4">
                  <div className="text-center shrink-0 w-14">
                    <div className="text-xl font-extrabold text-white font-mono">{threat.risk_score}</div>
                    <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Risk Score</div>
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-semibold text-slate-200">
                        {threat.transaction_id.slice(0, 12)}...
                      </span>
                      <RiskBadge level={threat.risk_level} />
                      <span className="text-xs text-slate-500">• {threat.payment_method || 'UPI'}</span>
                    </div>

                    <div className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                      <span>Top Risk Driver:</span>
                      <span className="text-slate-200 font-medium">{threat.top_risk_driver || 'Velocity burst detected'}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between md:justify-end gap-6 shrink-0">
                  <div className="text-right">
                    <div className="font-mono font-bold text-white text-base">
                      ₹{Number(threat.amount).toLocaleString('en-IN')}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      {threat.timestamp ? new Date(threat.timestamp).toLocaleTimeString() : 'Recent'}
                    </div>
                  </div>

                  <div className="p-2 rounded-lg bg-slate-800/60 text-slate-400 group-hover:text-white">
                    <ArrowUpRight size={18} />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default Threats;
