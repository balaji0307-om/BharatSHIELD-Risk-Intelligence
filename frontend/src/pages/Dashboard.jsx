import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Receipt,
  TrendingUp,
  Activity,
  ArrowUpRight,
  Siren,
  Laptop,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { useNavigate } from 'react-router-dom';

import MetricCard from '../components/MetricCard';
import TransactionTable from '../components/TransactionTable';
import RiskBadge from '../components/RiskBadge';
import RiskScore from '../components/RiskScore';
import { analyticsAPI, transactionsAPI, alertsAPI } from '../services/api';

const Dashboard = () => {
  const [kpis, setKpis] = useState(null);
  const [posture, setPosture] = useState(null);
  const [liveThreats, setLiveThreats] = useState([]);
  const [trends, setTrends] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const [overviewData, trendData, txnData, alertData, postureRes, threatsRes] = await Promise.all([
        analyticsAPI.getOverview(),
        analyticsAPI.getTrends(),
        transactionsAPI.listTransactions({ page: 1, page_size: 8 }),
        alertsAPI.listAlerts(),
        axios.get('/api/merchant/posture').catch(() => ({ data: null })),
        axios.get('/api/threats/live?limit=4').catch(() => ({ data: [] })),
      ]);

      setKpis(overviewData);
      setTrends(trendData.trends || []);
      setRecentTransactions(txnData.items || []);
      setActiveAlerts(alertData.filter((a) => !a.is_acknowledged));
      setPosture(postureRes.data);
      setLiveThreats(threatsRes.data || []);
    } catch (err) {
      console.error('Error fetching dashboard telemetry:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 12000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
            Merchant Risk Intelligence Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time transaction risk scoring, SHAP explainability, and velocity spike monitoring.
          </p>
        </div>

        {activeAlerts.length > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
            <ShieldAlert size={16} />
            <span>{activeAlerts.length} Active Anomaly Alerts Detected</span>
          </div>
        )}
      </div>

      {/* Merchant Risk Posture Banner */}
      {posture && (
        <div className="p-6 rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900/80 to-slate-950 shadow-xl">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="flex items-center gap-6">
              <div className="shrink-0 flex flex-col items-center">
                <RiskScore score={posture.overall_risk_score} size="md" />
                <div className="text-[10px] text-slate-400 uppercase font-mono tracking-wider mt-1 font-semibold">
                  Posture Score
                </div>
              </div>

              <div>
                <div className="flex items-center gap-2.5">
                  <h2 className="text-lg font-bold text-white tracking-tight">MERCHANT RISK POSTURE</h2>
                  <RiskBadge level={posture.overall_risk_level} />
                </div>
                <p className="text-xs text-slate-400 mt-1 max-w-md">
                  Active security telemetry computed across live payment gateways and device associations.
                </p>

                <div className="flex flex-wrap gap-4 mt-3 text-xs font-mono">
                  <div>
                    <span className="text-slate-500">Total Txns:</span>{' '}
                    <span className="text-white font-semibold">{posture.total_transactions?.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Fraud Rate:</span>{' '}
                    <span className="text-rose-400 font-semibold">{posture.fraud_rate}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Active Threats:</span>{' '}
                    <span className="text-amber-400 font-semibold">{posture.active_threats}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Open Cases:</span>{' '}
                    <span className="text-sky-400 font-semibold">{posture.open_cases}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Top Risk Drivers Mini Bars */}
            <div className="lg:w-72 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80 space-y-2">
              <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider font-semibold">
                Top Risk Drivers (SHAP)
              </div>
              <div className="space-y-1.5">
                {posture.top_risk_drivers?.slice(0, 3).map((driver, i) => (
                  <div key={i} className="text-[11px]">
                    <div className="flex justify-between text-slate-300 font-medium">
                      <span className="truncate max-w-[170px]">{driver.driver}</span>
                      <span className="font-mono text-emerald-400">{driver.percentage}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full mt-0.5 overflow-hidden">
                      <div
                        className="bg-emerald-500 h-full rounded-full"
                        style={{ width: `${driver.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Live Threat Feed Preview Panel */}
      {liveThreats.length > 0 && (
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
              </span>
              <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-1.5">
                <Siren className="text-rose-400" size={16} />
                LIVE THREAT INGRESS
              </h3>
            </div>
            <button
              onClick={() => navigate('/threats')}
              className="text-xs text-emerald-400 hover:underline font-mono flex items-center gap-1"
            >
              <span>View All Threats</span>
              <ArrowUpRight size={14} />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {liveThreats.map((threat) => (
              <div
                key={threat.transaction_id}
                onClick={() => navigate(`/transactions/${threat.transaction_id}`)}
                className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition cursor-pointer space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-slate-300">
                    TXN-{threat.transaction_id.slice(0, 8)}
                  </span>
                  <RiskBadge level={threat.risk_level} />
                </div>
                <div className="font-mono text-sm font-bold text-white">
                  ₹{Number(threat.amount).toLocaleString('en-IN')}
                </div>
                <div className="text-[11px] text-slate-400 truncate">
                  {threat.top_risk_driver || 'Velocity burst'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4 KPI Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Total Transactions"
          value={kpis ? kpis.total_transactions.toLocaleString() : '---'}
          subtitle="All evaluated payments (30d)"
          icon={Receipt}
          color="blue"
        />
        <MetricCard
          title="Fraud Detected"
          value={kpis ? kpis.fraud_detected_count.toLocaleString() : '---'}
          subtitle={`Fraud rate: ${kpis ? kpis.fraud_rate_percentage : 0}%`}
          icon={ShieldAlert}
          color="rose"
          trendType="up"
          trend="Score >= 75"
        />
        <MetricCard
          title="High Risk (Step-Up)"
          value={kpis ? kpis.high_risk_count.toLocaleString() : '---'}
          subtitle="Mandated 2FA / Biometric"
          icon={AlertTriangle}
          color="amber"
          trendType="neutral"
          trend="Score 50–74"
        />
        <MetricCard
          title="Avg Risk Score"
          value={kpis ? `${kpis.average_risk_score} / 100` : '---'}
          subtitle="Portfolio average exposure"
          icon={Activity}
          color="emerald"
        />
      </div>

      {/* Trend Charts: Risk Trend & Fraud Volume */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Trend Chart */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                24-Hour Average Risk Score Exposure
              </h3>
              <p className="text-xs text-slate-400">Mean risk score variation across hourly buckets</p>
            </div>
            <span className="text-xs font-mono text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              Live Stream
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="avg_risk" name="Avg Risk Score" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#riskGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Fraud vs Legit Volume Chart */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Transaction Volume & Fraud Spikes
              </h3>
              <p className="text-xs text-slate-400">Total volume vs. flagged critical fraud events</p>
            </div>
            <span className="text-xs font-mono text-rose-400 font-semibold bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
              Spike Monitor
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="total_transactions" name="Total Volume" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="fraud_count" name="Critical Frauds" fill="#f43f5e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Risky Transactions Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">
              Recent Risky Transactions
            </h2>
            <p className="text-xs text-slate-400">
              Transactions processed by the BharatSHIELD Risk Engine with color-coded risk bands
            </p>
          </div>
        </div>

        <TransactionTable transactions={recentTransactions} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default Dashboard;
