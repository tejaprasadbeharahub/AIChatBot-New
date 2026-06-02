import React from 'react';
import type { FarmTicket } from '../../../api/tickets';
import { WeatherCard } from './WeatherCard';
import { MarketIntelligenceCard } from './MarketIntelligenceCard';
import { RecommendationCard } from './RecommendationCard';

interface Props {
  ticket: FarmTicket;
}

export const AIInsightsPanel: React.FC<Props> = ({ ticket }) => {
  const trend = (ticket.extra?.current_market_trend as string | undefined) || 'STABLE';
  const action = (ticket.extra?.recommended_action as string | undefined) || (ticket.ticket_status === 'CLOSED' ? 'SELL_NOW' : 'HOLD');
  const expectedProfit = String(ticket.extra?.expected_profit ?? 'Not available');
  const recommendation = String(ticket.extra?.farmer_alert_message ?? 'Awaiting full AI pipeline completion.');
  const riskLevel = (ticket.risk_level || 'MEDIUM').toUpperCase();

  return (
    <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
      <WeatherCard weather={ticket.weather} riskLevel={riskLevel} />
      <MarketIntelligenceCard trend={trend} action={action} expectedProfit={expectedProfit} />
      <RecommendationCard recommendation={recommendation} />
    </div>
  );
};
