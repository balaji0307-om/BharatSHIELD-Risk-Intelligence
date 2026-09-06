import React from 'react';

const RiskBadge = ({ level, score }) => {
  const normalizedLevel = (level || 'LOW').toUpperCase();

  const config = {
    LOW: {
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-400',
      border: 'border-emerald-500/30',
      dot: 'bg-emerald-400',
    },
    MEDIUM: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-400',
      border: 'border-amber-500/30',
      dot: 'bg-amber-400',
    },
    HIGH: {
      bg: 'bg-orange-500/10',
      text: 'text-orange-400',
      border: 'border-orange-500/30',
      dot: 'bg-orange-400',
    },
    CRITICAL: {
      bg: 'bg-rose-500/10',
      text: 'text-rose-400',
      border: 'border-rose-500/30',
      dot: 'bg-rose-400',
    },
  };

  const current = config[normalizedLevel] || config.LOW;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${current.bg} ${current.text} ${current.border}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${current.dot} animate-pulse`} />
      {normalizedLevel}
      {score !== undefined && <span className="opacity-75 font-mono">({score})</span>}
    </span>
  );
};

export default RiskBadge;
