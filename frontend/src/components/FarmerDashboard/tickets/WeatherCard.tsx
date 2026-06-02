import React from 'react';

interface Props {
  weather: string;
  riskLevel: string;
}

export const WeatherCard: React.FC<Props> = ({ weather, riskLevel }) => (
  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
    <h4 className="text-sm font-semibold text-slate-800">Weather Intelligence</h4>
    <p className="mt-2 text-sm text-slate-600">Condition: {weather || 'N/A'}</p>
    <p className="text-sm text-slate-600">Disease Risk: {riskLevel || 'MEDIUM'}</p>
  </div>
);
