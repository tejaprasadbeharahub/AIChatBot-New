import React from 'react';
import { getRiskIcon, getRiskColor } from '../../api/farm';

interface RiskBadgeProps {
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  score?: number;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, score }) => {
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(level)}`}>
      <span>{getRiskIcon(level)}</span>
      <span>{level}</span>
      {score !== undefined && <span className="opacity-75">({(score * 100).toFixed(0)}%)</span>}
    </div>
  );
};
