import React from 'react';
import { Link } from 'react-router-dom';
import { ExternalLink, Smartphone, MapPin } from 'lucide-react';
import RiskBadge from './RiskBadge';

const TransactionTable = ({ transactions = [], isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="py-12 text-center text-slate-400">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        Loading transaction telemetry...
      </div>
    );
  }

  if (!transactions || transactions.length === 0) {
    return (
      <div className="py-12 text-center text-slate-400 bg-slate-800/30 rounded-xl border border-slate-800">
        No transactions found matching the current filter criteria.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur">
      <table className="w-full text-left text-sm text-slate-300">
        <thead className="bg-slate-800/80 text-xs uppercase font-semibold text-slate-400 tracking-wider border-b border-slate-700">
          <tr>
            <th scope="col" className="px-5 py-3.5">Transaction Ref</th>
            <th scope="col" className="px-5 py-3.5">Amount (INR)</th>
            <th scope="col" className="px-5 py-3.5">Method</th>
            <th scope="col" className="px-5 py-3.5">Risk Level</th>
            <th scope="col" className="px-5 py-3.5">Status</th>
            <th scope="col" className="px-5 py-3.5">Location / Context</th>
            <th scope="col" className="px-5 py-3.5">Timestamp</th>
            <th scope="col" className="px-5 py-3.5 text-right">Inspect</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800 font-normal">
          {transactions.map((txn) => {
            const dateStr = new Date(txn.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            });
            const fullDateStr = new Date(txn.timestamp).toLocaleDateString([], {
              month: 'short',
              day: 'numeric',
            });

            return (
              <tr
                key={txn.transaction_id}
                className="hover:bg-slate-800/50 transition-colors group"
              >
                <td className="px-5 py-3.5 font-mono text-xs text-slate-300">
                  <div className="font-semibold text-white">
                    {txn.transaction_id.slice(0, 8)}...
                  </div>
                  <div className="text-[10px] text-slate-500 font-sans">
                    {txn.merchant_id}
                  </div>
                </td>

                <td className="px-5 py-3.5 font-mono font-bold text-white">
                  ₹{Number(txn.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </td>

                <td className="px-5 py-3.5">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-xs text-slate-300 font-medium">
                    {txn.payment_method}
                  </span>
                </td>

                <td className="px-5 py-3.5">
                  <RiskBadge level={txn.risk_level} score={txn.risk_score} />
                </td>

                <td className="px-5 py-3.5 text-xs font-semibold">
                  <span
                    className={
                      txn.status === 'ALLOWED'
                        ? 'text-emerald-400'
                        : txn.status === 'HOLD_FOR_REVIEW'
                        ? 'text-rose-400'
                        : 'text-amber-400'
                    }
                  >
                    {txn.status}
                  </span>
                </td>

                <td className="px-5 py-3.5 text-xs text-slate-400">
                  <div className="flex items-center gap-1">
                    <MapPin size={12} className="text-slate-500" />
                    <span>{txn.location || 'Mumbai'}</span>
                  </div>
                  {txn.is_new_device && (
                    <div className="flex items-center gap-1 text-[10px] text-amber-400 mt-0.5">
                      <Smartphone size={10} />
                      <span>New Device</span>
                    </div>
                  )}
                </td>

                <td className="px-5 py-3.5 text-xs text-slate-400 font-mono">
                  <div>{dateStr}</div>
                  <div className="text-[10px] text-slate-500">{fullDateStr}</div>
                </td>

                <td className="px-5 py-3.5 text-right">
                  <Link
                    to={`/transactions/${txn.transaction_id}`}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs font-medium text-emerald-400 border border-slate-700 transition"
                  >
                    Deep Dive <ExternalLink size={12} />
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default TransactionTable;
