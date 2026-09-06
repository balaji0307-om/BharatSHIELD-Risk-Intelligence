import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Receipt,
  TrendingUp,
  Activity,
  ArrowUpRight,
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

import MetricCard from '../components/MetricCard';
import TransactionTable from '../components/TransactionTable';
import { analyticsAPI, transactionsAPI, alertsAPI } from '../services/api';

const Dashboard = () => {
  const [kpis, setKpis] = useState(null);
  const [trends, setTrends] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const [overviewData, trendData, txnData, alertData] = await Promise.all([
        analyticsAPI.getOverview(),
        analyticsAPI.getTrends(),
        transactionsAPI.listTransactions({ page: 1, page_size: 8 }),
        alertsAPI.listAlerts(),
      ]);

      setKpis(overviewData);
      setTrends(trendData.trends || []);
      setRecentTransactions(txnData.items || []);
      setActiveAlerts(alertData.filter((a) => !a.is_acknowledged));
    } catch (err) {
      console.error('Error fetching dashboard telemetry:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    // Auto-refresh every 15 seconds for live hackathon demo feel
    const interval = setInterval(fetchDashboardData, 15000);
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
