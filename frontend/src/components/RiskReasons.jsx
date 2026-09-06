import React from 'react';
import { AlertCircle, ShieldAlert, ArrowUpRight, ArrowDownRight } from 'lucide-react';

const RiskReasons = ({ factors = [] }) => {
  if (!factors || factors.length === 0) {
    return (
      <div className="text-center py-6 text-slate-400 text-sm">
        No critical risk factors identified. Transaction behaviors align with baseline profile.
      </div>
    );
  }

  // Calculate maximum contribution to scale bars
  const maxContribution = Math.max(...factors.map((f) => f.contribution || 1), 10);

  return (
    <div className="space-y-3">
      {factors.map((factor, index) => {
        const isIncrease = factor.direction === 'increases_risk';
        const contribution = Math.round((factor.contribution || 0) * 10) / 10;
        const percentage = Math.min(100, Math.round((contribution / maxContribution) * 100));

        return (
          <div
            key={index}
            className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg hover:border-slate-700 transition-colors"
          >
            <div className="flex items-center justify-between text-sm mb-1.5">
              <div className="flex items-center gap-2">
                {isIncrease ? (
                  <ArrowUpRight className="text-rose-400" size={16} />
                ) : (
                  <ArrowDownRight className="text-emerald-400" size={16} />
                )}
                <span className="font-semibold text-slate-200">
                  {factor.display_name || factor.feature}
                </span>
                {factor.value !== undefined && factor.value !== null && factor.value !== '' && (
                  <span className="text-xs font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">
                    val: {String(factor.value)}
                  </span>
                )}
              </div>
              <span
                className={`font-mono font-bold text-xs ${
                  isIncrease ? 'text-rose-400' : 'text-emerald-400'
                }`}
              >
                {isIncrease ? `+${contribution} pts` : `-${contribution} pts`}
              </span>
            </div>

            {/* Visual Contribution Bar */}
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  isIncrease ? 'bg-gradient-to-r from-orange-500 to-rose-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RiskReasons;
