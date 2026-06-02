import React from 'react';

interface Props {
  trend: string;
  action: string;
  expectedProfit: string;
}

export const MarketIntelligenceCard: React.FC<Props> = ({ trend, action, expectedProfit }) => (
  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
    <h4 className="text-sm font-semibold text-slate-800">Market Intelligence</h4>
    <p className="mt-2 text-sm text-slate-600">Trend: {trend || 'STABLE'}</p>
    <p className="text-sm text-slate-600">Best Action: {action || 'HOLD'}</p>
    <p className="text-sm text-slate-600">Expected Profit: {expectedProfit || 'Not available'}</p>
  </div>
);
