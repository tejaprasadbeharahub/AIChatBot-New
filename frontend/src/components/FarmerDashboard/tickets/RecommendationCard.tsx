import React from 'react';

interface Props {
  recommendation: string;
}

export const RecommendationCard: React.FC<Props> = ({ recommendation }) => (
  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
    <h4 className="text-sm font-semibold text-slate-800">AI Recommendations</h4>
    <p className="mt-2 text-sm text-slate-600">{recommendation || 'AI recommendation is pending after workflow execution.'}</p>
  </div>
);
