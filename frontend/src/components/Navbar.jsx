import React, { useState } from 'react';
import { Bell, Sparkles, RefreshCw, ShieldAlert, Check, LogOut } from 'lucide-react';
import { transactionsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const Navbar = ({ onTransactionInjected }) => {
  const { user, merchantId, logout } = useAuth();
  const [isSimulating, setIsSimulating] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const simulateHighRiskTxn = async () => {
    setIsSimulating(true);
    setFeedback(null);
    try {
      const payload = {
        merchant_id: 'MER_razorpay_001',
        transaction_amount: 88500.0,
        payment_method: 'UPI',
        transaction_hour: 2,
        device_age_days: 1,
        failed_attempts: 4,
        transactions_last_5min: 9,
        transactions_last_10min: 15,
        transactions_last_1hr: 28,
        amount_last_1hr: 150000.0,
        is_new_device: true,
        is_new_location: true,
        device_transaction_count: 1,
        avg_transaction_amount: 12000.0,
        amount_deviation: 7.37,
        historical_frequency: 1.5,
        location_change: 3,
        distance_from_previous: 1450.0,
      };

      const res = await transactionsAPI.scoreTransaction(payload);
      setFeedback(`Live Txn Flagged: Score ${res.risk_score} [${res.risk_level}]`);
      if (onTransactionInjected) {
        onTransactionInjected(res);
      }
    } catch (err) {
      setFeedback('Simulation error');
    } finally {
      setIsSimulating(false);
      setTimeout(() => setFeedback(null), 4000);
    }
  };

  return (
    <header className="h-16 bg-slate-900/80 border-b border-slate-800 px-8 flex items-center justify-between sticky top-0 z-10 backdrop-blur">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs font-mono">
          <span className="text-slate-400">Active Merchant:</span>
          <span className="text-emerald-400 font-bold">MER_razorpay_001</span>
        </div>

        {feedback && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/20 border border-rose-500/40 text-xs text-rose-300 font-semibold animate-bounce">
            <ShieldAlert size={14} />
            <span>{feedback}</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Simulate Live Transaction Button (Demo Optimizer) */}
        <button
          onClick={simulateHighRiskTxn}
          disabled={isSimulating}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold shadow-md shadow-emerald-900/20 transition active:scale-95 disabled:opacity-50"
        >
          {isSimulating ? (
            <RefreshCw size={14} className="animate-spin" />
          ) : (
            <Sparkles size={14} />
          )}
          <span>Simulate Incoming Attack</span>
        </button>

        {/* Replay Cinematic Intro button */}
        <button
          onClick={() => {
            sessionStorage.removeItem('bharatshield_intro_seen');
            window.location.reload();
          }}
          className="px-2.5 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900/60 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-mono transition"
          title="Replay Cinematic Intro"
        >
          Intro ⟳
        </button>

        {/* User Account & Logout */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="flex flex-col items-end">
            <span className="text-xs font-semibold text-slate-200">
              {user?.email || 'Merchant Admin'}
            </span>
            <span className="text-[10px] font-mono text-emerald-400">
              {merchantId || 'MER_razorpay_001'}
            </span>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg border border-slate-800 hover:border-rose-500/50 hover:bg-rose-500/10 text-slate-400 hover:text-rose-300 transition"
            title="Log Out of BharatSHIELD"
          >
            <LogOut size={16} />
          </button>
        </div>

        {/* Live indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-800 text-xs text-slate-300">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="font-mono">IST Live</span>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
