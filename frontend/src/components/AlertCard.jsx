import React from 'react';
import { AlertTriangle, AlertOctagon, Zap, CheckCircle } from 'lucide-react';

const AlertCard = ({ alert, onAcknowledge }) => {
  const isCritical = alert.severity === 'CRITICAL';
  const isHigh = alert.severity === 'HIGH';

  const severityStyles = {
    CRITICAL: 'border-rose-500/30 bg-rose-950/20 text-rose-400',
    HIGH: 'border-orange-500/30 bg-orange-950/20 text-orange-400',
    MEDIUM: 'border-amber-500/30 bg-amber-950/20 text-amber-400',
    LOW: 'border-slate-700 bg-slate-800/40 text-slate-300',
  };

  const Icon = isCritical ? AlertOctagon : isHigh ? AlertTriangle : Zap;

  return (
    <div
      className={`p-4 rounded-xl border ${
        severityStyles[alert.severity] || severityStyles.MEDIUM
      } backdrop-blur relative transition-all hover:border-slate-600`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-700/50 mt-0.5">
            <Icon size={18} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
                {alert.alert_type}
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase border border-current">
                {alert.severity}
              </span>
            </div>
            <h4 className="text-sm font-bold text-white mt-1">{alert.title}</h4>
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">{alert.description}</p>
          </div>
        </div>

        <div>
          {alert.is_acknowledged ? (
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded border border-emerald-500/30">
              <CheckCircle size={14} /> Resolved
            </span>
          ) : (
            <button
              onClick={() => onAcknowledge && onAcknowledge(alert.alert_id)}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 rounded border border-slate-700 transition"
            >
              Acknowledge
            </button>
          )}
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <span>Merchant: {alert.merchant_id}</span>
        <span>{new Date(alert.created_at).toLocaleString()}</span>
      </div>
    </div>
  );
};

export default AlertCard;
