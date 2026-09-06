import React from 'react';

const MetricCard = ({ title, value, subtitle, icon: Icon, trend, trendType = 'neutral', color = 'emerald' }) => {
  const colorMap = {
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    rose: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    blue: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  };

  const trendColors = {
    up: 'text-rose-400',
    down: 'text-emerald-400',
    neutral: 'text-slate-400',
  };

  return (
    <div className="bg-slate-800/80 border border-slate-700/60 backdrop-blur rounded-xl p-5 shadow-lg relative overflow-hidden">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-400 tracking-wide">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-lg border ${colorMap[color] || colorMap.emerald}`}>
            <Icon size={18} />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-3xl font-bold font-mono text-white tracking-tight">{value}</span>
        {trend && (
          <span className={`text-xs font-semibold ${trendColors[trendType]}`}>
            {trend}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
      )}
    </div>
  );
};

export default MetricCard;
