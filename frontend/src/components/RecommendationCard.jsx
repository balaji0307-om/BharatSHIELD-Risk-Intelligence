import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, AlertOctagon } from 'lucide-react';

const RecommendationCard = ({ recommendation, riskLevel = 'LOW' }) => {
  const level = (riskLevel || 'LOW').toUpperCase();

  const configs = {
    LOW: {
      icon: ShieldCheck,
      color: 'emerald',
      badge: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400',
      box: 'border-emerald-500/20 bg-emerald-950/20',
      actionTitle: 'Straight-Through Processing (STP)',
    },
    MEDIUM: {
      icon: ShieldAlert,
      color: 'amber',
      badge: 'border-amber-500/30 bg-amber-500/10 text-amber-400',
      box: 'border-amber-500/20 bg-amber-950/20',
      actionTitle: 'Passive Identity Verification',
    },
    HIGH: {
      icon: AlertTriangle,
      color: 'orange',
      badge: 'border-orange-500/30 bg-orange-500/10 text-orange-400',
      box: 'border-orange-500/20 bg-orange-950/20',
      actionTitle: 'Mandatory Step-Up Challenge',
    },
    CRITICAL: {
      icon: AlertOctagon,
      color: 'rose',
      badge: 'border-rose-500/30 bg-rose-500/10 text-rose-400',
      box: 'border-rose-500/20 bg-rose-950/20',
      actionTitle: 'Immediate Security Hold',
    },
  };

  const cfg = configs[level] || configs.LOW;
  const Icon = cfg.icon;

  const action = recommendation?.action || 'Evaluate';
  const description = recommendation?.description || 'System policy guidance.';
  const details = recommendation?.details || [];

  return (
    <div className={`p-5 rounded-xl border ${cfg.box} backdrop-blur relative overflow-hidden`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg border ${cfg.badge}`}>
            <Icon size={22} />
          </div>
          <div>
            <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
              Automated Policy Recommendation
            </span>
            <h3 className="text-lg font-bold text-white mt-0.5">{action}</h3>
          </div>
        </div>

        <span className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider border ${cfg.badge}`}>
          {level} PRIORITY
        </span>
      </div>

      <p className="mt-3 text-sm text-slate-300 leading-relaxed">
        {description}
      </p>

      {details.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
            Operational Protocol Details:
          </span>
          <ul className="mt-2 space-y-1 text-xs text-slate-300">
            {details.map((item, idx) => (
              <li key={idx} className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default RecommendationCard;
