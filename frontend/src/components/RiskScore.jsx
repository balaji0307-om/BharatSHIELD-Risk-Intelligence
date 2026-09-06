import React from 'react';

const RiskScore = ({ score = 0, size = 120, strokeWidth = 10 }) => {
  const normalizedScore = Math.max(0, Math.min(100, Math.round(score)));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  let strokeColor = '#10b981'; // green
  let glowColor = 'rgba(16, 185, 129, 0.3)';
  if (normalizedScore >= 75) {
    strokeColor = '#f43f5e'; // red
    glowColor = 'rgba(244, 63, 94, 0.4)';
  } else if (normalizedScore >= 50) {
    strokeColor = '#f97316'; // orange
    glowColor = 'rgba(249, 115, 22, 0.4)';
  } else if (normalizedScore >= 25) {
    strokeColor = '#f59e0b'; // amber
    glowColor = 'rgba(245, 158, 11, 0.3)';
  }

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#1e293b"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        {/* Animated Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          style={{
            transition: 'stroke-dashoffset 0.8s ease-out, stroke 0.5s ease',
            filter: `drop-shadow(0 0 6px ${glowColor})`,
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-center">
        <span className="text-2xl font-black font-mono tracking-tight text-white">
          {normalizedScore}
        </span>
        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
          / 100
        </span>
      </div>
    </div>
  );
};

export default RiskScore;
