import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Smartphone,
  MapPin,
  Clock,
  ShieldCheck,
  ShieldAlert,
  CreditCard,
  Hash,
  Share2,
  FileText,
  Activity,
  Zap,
} from 'lucide-react';

import RiskScore from '../components/RiskScore';
import RiskBadge from '../components/RiskBadge';
import RiskReasons from '../components/RiskReasons';
import RecommendationCard from '../components/RecommendationCard';
import { transactionsAPI } from '../services/api';

const TransactionDetails = () => {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [related, setRelated] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDetails = async () => {
      setIsLoading(true);
      try {
        const [txnData, relatedData] = await Promise.all([
          transactionsAPI.getTransaction(id),
          transactionsAPI.getRelated(id),
        ]);
        setData(txnData);
        setRelated(relatedData.related_transactions || []);
      } catch (err) {
        console.error('Error fetching transaction detail:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDetails();
  }, [id]);

  if (isLoading) {
    return (
      <div className="p-12 text-center text-slate-400">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        Reconstructing transaction risk audit trail...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 text-center text-slate-400">
        <p>Transaction not found.</p>
        <Link to="/transactions" className="mt-4 inline-block text-emerald-400 text-sm font-semibold">
          Return to Transactions
        </Link>
      </div>
    );
  }

  const { transaction: txn, risk_assessment: risk, audit_log: audit } = data;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Back link & Title */}
      <div>
        <Link
          to="/transactions"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition mb-3"
        >
          <ArrowLeft size={14} /> Back to Ledger
        </Link>

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black tracking-tight text-white font-mono">
                Txn #{txn.transaction_id.slice(0, 16)}...
              </h1>
              <RiskBadge level={risk.risk_level} score={risk.risk_score} />
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Evaluated at {new Date(txn.timestamp).toLocaleString()} | Merchant: {txn.merchant_id}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-3 py-1 rounded bg-slate-800 border border-slate-700 font-mono text-sm text-emerald-400 font-bold">
              Status: {txn.status}
            </span>
          </div>
        </div>
      </div>

      {/* Top Banner: Risk Gauge + Financial Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Score Radial Tile */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur flex items-center justify-around">
          <RiskScore score={risk.risk_score} size={130} strokeWidth={12} />
          <div className="space-y-1">
            <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
              Risk Assessment
            </span>
            <div className="text-xl font-black text-white">{risk.risk_level} RISK</div>
            <p className="text-xs text-slate-400">
              Fraud Probability: <span className="font-mono text-white font-bold">{(risk.fraud_probability * 100).toFixed(1)}%</span>
            </p>
          </div>
        </div>

        {/* Transaction Summary Tile */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
          <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
            Financial & Payment Context
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
            <div>
              <span className="text-xs text-slate-400">Amount</span>
              <div className="text-lg font-bold font-mono text-white mt-0.5">
                ₹{Number(txn.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div>
              <span className="text-xs text-slate-400">Method</span>
              <div className="text-sm font-semibold text-white mt-1">
                {txn.payment_method}
              </div>
            </div>
            <div>
              <span className="text-xs text-slate-400">Currency</span>
              <div className="text-sm font-semibold text-white mt-1">
                {txn.currency}
              </div>
            </div>
            <div>
              <span className="text-xs text-slate-400">Location</span>
              <div className="text-sm font-semibold text-white mt-1 flex items-center gap-1">
                <MapPin size={12} className="text-slate-400" />
                {txn.location}
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-400">Failed Auth Attempts</span>
              <div className="font-mono font-bold text-rose-400 mt-0.5">{txn.failed_attempts}</div>
            </div>
            <div>
              <span className="text-slate-400">Device Age</span>
              <div className="font-mono text-white mt-0.5">{txn.device_age_days} days</div>
            </div>
            <div>
              <span className="text-slate-400">5-Min Velocity</span>
              <div className="font-mono text-white mt-0.5">{txn.transactions_last_5min} txns</div>
            </div>
            <div>
              <span className="text-slate-400">Distance Shift</span>
              <div className="font-mono text-white mt-0.5">{txn.distance_from_previous.toFixed(1)} km</div>
            </div>
          </div>
        </div>
      </div>

      {/* Explainable AI: SHAP Factors + Recommendation Card */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SHAP Factor Breakdown */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Explainable Risk Attribution (SHAP)
              </h3>
              <p className="text-xs text-slate-400">
                Itemized ranking of features influencing the final risk score
              </p>
            </div>
            <span className="text-xs font-mono text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
              TreeExplainer
            </span>
          </div>

          <RiskReasons factors={risk.risk_factors} />
        </div>

        {/* Policy Recommendation */}
        <div className="space-y-6">
          <RecommendationCard
            recommendation={risk.recommended_action}
            riskLevel={risk.risk_level}
          />

          {/* Immutable Audit Log Reference */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 backdrop-blur">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
              <FileText size={16} className="text-emerald-400" />
              Immutable Audit Trail Confirmation
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Log Reference: <span className="font-mono text-emerald-400">{audit.log_id || 'AUD_GEN_001'}</span>
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Summary Trail: <span className="text-slate-200">{audit.reasons_summary}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Related Transactions / Entity Resolution */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Share2 size={16} className="text-emerald-400" />
          Related Entity Activity (Linked by Device Fingerprint & Geographic Proximity)
        </h3>

        {related.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-400 bg-slate-900/40 rounded-xl border border-slate-800">
            No related transactions found in the ±24h observation window.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {related.map((rel) => (
              <div
                key={rel.transaction_id}
                className="p-4 rounded-xl border border-slate-800 bg-slate-900/50 hover:border-slate-700 transition"
              >
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-mono text-slate-400">{rel.transaction_id.slice(0, 8)}...</span>
                  <RiskBadge level={rel.risk_level} score={rel.risk_score} />
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="font-bold text-white font-mono">
                    ₹{Number(rel.amount).toLocaleString('en-IN')}
                  </span>
                  <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    {rel.shared_link}
                  </span>
                </div>
                <div className="mt-2 text-[10px] text-slate-400 font-mono">
                  {new Date(rel.timestamp).toLocaleString()}
                </div>
                <Link
                  to={`/transactions/${rel.transaction_id}`}
                  className="mt-3 block text-center py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition"
                >
                  View Details
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TransactionDetails;
