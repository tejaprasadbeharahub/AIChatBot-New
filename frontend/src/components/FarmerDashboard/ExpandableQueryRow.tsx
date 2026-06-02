import React, { useState } from 'react';
import type { FarmQuery } from '../../api/farm';
import { RiskBadge } from './RiskBadge';

interface ExpandableQueryRowProps {
  query: FarmQuery;
  isExpanded: boolean;
  onToggle: (id: string) => void;
}

export const ExpandableQueryRow: React.FC<ExpandableQueryRowProps> = ({
  query,
  isExpanded,
  onToggle,
}) => {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const analysis = query.analysis;
  const market = query.market_intelligence;

  const findFirstByKeys = (value: unknown, candidateKeys: string[]): unknown => {
    const normalized = new Set(candidateKeys.map((key) => key.toLowerCase()));

    const walk = (node: unknown): unknown => {
      if (node === null || node === undefined) return undefined;

      if (Array.isArray(node)) {
        for (const item of node) {
          const found = walk(item);
          if (found !== undefined) return found;
        }
        return undefined;
      }

      if (typeof node === 'object') {
        for (const [key, val] of Object.entries(node as Record<string, unknown>)) {
          if (normalized.has(key.toLowerCase())) return val;
        }

        for (const val of Object.values(node as Record<string, unknown>)) {
          const found = walk(val);
          if (found !== undefined) return found;
        }
      }

      return undefined;
    };

    return walk(value);
  };

  const asText = (value: unknown, fallback: string): string => {
    if (value === null || value === undefined) return fallback;
    if (typeof value === 'string') {
      const trimmed = value.trim();
      return trimmed ? trimmed : fallback;
    }
    if (typeof value === 'number' || typeof value === 'boolean') return String(value);
    if (Array.isArray(value)) {
      const parts = value
        .map((item) => (typeof item === 'string' || typeof item === 'number' ? String(item).trim() : ''))
        .filter((item) => item.length > 0);
      return parts.length > 0 ? parts.join(', ') : fallback;
    }
    return fallback;
  };

  const webhookSource = query.webhook_result ?? query.submitted_payload ?? {};
  const cropValue = asText(
    findFirstByKeys(webhookSource, ['crop', 'crop_type']) ?? analysis?.crop ?? market?.crop ?? query.crop_type,
    query.crop_type || 'not_provided'
  );
  const regionValue = asText(
    findFirstByKeys(webhookSource, ['region', 'location']) ?? query.location,
    'not_provided'
  );
  const riskLevelValue = asText(
    findFirstByKeys(webhookSource, ['risk_level', 'overall_risk_level']) ?? analysis?.overall_risk_level,
    'MEDIUM'
  ).toUpperCase();
  const confidenceValue = asText(
    findFirstByKeys(webhookSource, ['confidence', 'confidence_score']) ?? analysis?.confidence,
    '0'
  );
  const diseaseIssueValue = asText(
    findFirstByKeys(webhookSource, ['disease', 'disease_name', 'disease_issue', 'disease_risk_analysis']) ??
      analysis?.disease_risk_analysis,
    'Analysis completed based on crop symptoms and market-risk signals. Specific disease classification not available.'
  );
  const aiReasoningValue = asText(
    findFirstByKeys(webhookSource, ['ai_reasoning', 'reasoning', 'market_risk_analysis']) ?? analysis?.market_risk_analysis,
    'Market analysis could not be completed due to a service error.'
  );
  const immediateActionValue = asText(
    findFirstByKeys(webhookSource, ['immediate_action', 'farmer_alert_message']) ?? analysis?.farmer_alert_message,
    'Please consult your local mandi or agricultural officer for current price trends.'
  );
  const treatmentImmediateValue = asText(
    findFirstByKeys(webhookSource, ['treatment_immediate_action', 'immediate_treatment']) ??
      analysis?.preventive_actions?.immediate,
    'Inspect crop and remove affected leaves/fruits immediately'
  );
  const organicSolutionValue = asText(
    findFirstByKeys(webhookSource, ['organic_solution', 'organic_solutions']) ??
      findFirstByKeys(analysis, ['organic_solutions']),
    'Use neem oil spray or bio-pesticides (locally available)'
  );
  const preventionValue = asText(
    findFirstByKeys(webhookSource, ['prevention', 'preventive_measures']) ??
      analysis?.preventive_actions?.long_term,
    'Maintain proper spacing, irrigation control, and regular field monitoring'
  );
  const marketTrendValue = asText(
    findFirstByKeys(webhookSource, ['market_trend', 'price_trend', 'current_market_trend']) ?? market?.price_trend,
    'STABLE'
  ).toUpperCase();
  const recommendedActionValue = asText(
    findFirstByKeys(webhookSource, ['recommended_action', 'recommendation']) ?? market?.market_outlook,
    'HOLD'
  ).toUpperCase();
  const decisionCodeValue = asText(findFirstByKeys(webhookSource, ['decision_code', 'decision']), '2');

  const formatConfidencePercent = (value: unknown): string => {
    if (value === null || value === undefined) return '0%';

    const parsed = typeof value === 'number' ? value : Number(String(value).trim());
    if (!Number.isFinite(parsed)) return '0%';

    const normalized = parsed <= 1 ? parsed * 100 : parsed;
    const clamped = Math.max(0, Math.min(100, normalized));
    return `${Math.round(clamped)}%`;
  };

  const riskCandidate = findFirstByKeys(webhookSource, ['risk_level', 'overall_risk_level']) ?? analysis?.overall_risk_level;
  const actionCandidate =
    findFirstByKeys(webhookSource, ['recommended_action', 'market_action', 'action']) ??
    market?.market_outlook ??
    market?.price_trend;
  const confidenceCandidate =
    findFirstByKeys(webhookSource, ['confidence', 'confidence_score']) ?? analysis?.confidence;

  const hasRisk = asText(riskCandidate, '').length > 0;
  const hasAction = asText(actionCandidate, '').length > 0;
  const hasConfidence = confidenceCandidate !== null && confidenceCandidate !== undefined && String(confidenceCandidate).trim() !== '';

  const gridRiskLevel = hasRisk ? asText(riskCandidate, 'MEDIUM').toUpperCase() : 'MEDIUM';
  const gridMarketAction = hasAction ? asText(actionCandidate, 'HOLD').toUpperCase() : 'HOLD';
  const gridConfidence = hasConfidence ? formatConfidencePercent(confidenceCandidate) : '0%';

  const riskBadgeLevel = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].includes(gridRiskLevel)
    ? (gridRiskLevel as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL')
    : undefined;

  const toTitle = (value: string) => value.replace(/[_-]+/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

  const renderPrimitive = (value: string | number | boolean | null | undefined) => {
    if (value === null || value === undefined) return <span className="text-gray-400">-</span>;
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    return String(value);
  };

  const renderAnyValue = (value: unknown, depth = 0): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span className="text-gray-400">-</span>;
    }

    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      return <span>{renderPrimitive(value)}</span>;
    }

    if (Array.isArray(value)) {
      if (value.length === 0) return <span className="text-gray-400">None</span>;

      const allPrimitive = value.every((item) => ['string', 'number', 'boolean'].includes(typeof item));
      if (allPrimitive) {
        return (
          <ul className="list-disc list-inside ml-2">
            {value.map((item, idx) => (
              <li key={`${depth}-arr-${idx}`}>{renderPrimitive(item as string | number | boolean)}</li>
            ))}
          </ul>
        );
      }

      return (
        <div className="space-y-2">
          {value.map((item, idx) => (
            <div key={`${depth}-obj-${idx}`} className="p-2 bg-gray-50 border border-gray-200 rounded">
              {renderAnyValue(item, depth + 1)}
            </div>
          ))}
        </div>
      );
    }

    if (typeof value === 'object') {
      const entries = Object.entries(value as Record<string, unknown>);
      if (entries.length === 0) return <span className="text-gray-400">Empty object</span>;

      return (
        <div className="space-y-2">
          {entries.map(([key, val]) => (
            <div key={`${depth}-${key}`} className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
              <p className="font-semibold text-gray-700 md:col-span-1">{toTitle(key)}</p>
              <div className="md:col-span-2 text-gray-700">{renderAnyValue(val, depth + 1)}</div>
            </div>
          ))}
        </div>
      );
    }

    return <span>{String(value)}</span>;
  };

  const renderSubmissionDetails = () => (
    <div className="space-y-3">
      <div className="bg-white rounded-lg p-4 border border-green-300">
        <h4 className="font-semibold text-gray-900 mb-3">Farm Advisory Summary</h4>
        <div className="space-y-3 text-sm text-gray-800">
          <div>
            <p className="font-semibold">🌾 Crop Details</p>
            <p>Crop: {cropValue}</p>
            <p>Region: {regionValue}</p>
            <p>Risk Level: {riskLevelValue}</p>
            <p>Confidence: {confidenceValue}</p>
          </div>

          <div>
            <p className="font-semibold">🐛 Disease / Issue Detected</p>
            <p>{diseaseIssueValue}</p>
          </div>

          <div>
            <p className="font-semibold">🧠 AI Reasoning</p>
            <p>{aiReasoningValue}</p>
          </div>

          <div>
            <p className="font-semibold">⚠️ Immediate Action Required</p>
            <p>{immediateActionValue}</p>
          </div>

          <div>
            <p className="font-semibold">🌱 Recommended Treatment Plan</p>
            <p>Immediate Action: {treatmentImmediateValue}</p>
            <p>Organic Solution: {organicSolutionValue}</p>
            <p>Prevention: {preventionValue}</p>
          </div>

          <div>
            <p className="font-semibold">📊 Market Insight</p>
            <p>Market Trend: {marketTrendValue}</p>
            <p>Recommended Action: {recommendedActionValue}</p>
            <p>Decision Code: {decisionCodeValue}</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <tr
        onClick={() => onToggle(query.id)}
        className="border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition"
      >
        <td className="px-4 py-3 text-sm font-medium text-gray-900">{query.id.substring(0, 8)}...</td>
        <td className="px-4 py-3 text-sm text-gray-700 max-w-xs truncate">{query.query}</td>
        <td className="px-4 py-3 text-sm font-medium text-gray-800">{query.crop_type}</td>
        <td className="px-4 py-3">
          {riskBadgeLevel ? (
            <RiskBadge level={riskBadgeLevel} score={analysis?.confidence} />
          ) : (
            <span className="text-sm text-gray-500">{gridRiskLevel}</span>
          )}
        </td>
        <td className="px-4 py-3 text-sm text-gray-700">
          {gridMarketAction}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {gridConfidence}
        </td>
        <td className="px-4 py-3 text-xs text-gray-500">
          {new Date(query.created_at).toLocaleDateString()}
        </td>
        <td className="px-4 py-3 text-center">
          <span className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </td>
      </tr>

      {isExpanded && (
        <tr className="bg-gray-100 border-b border-gray-300">
          <td colSpan={8} className="px-4 py-4">
            {analysis ? (
              <div className="space-y-4">
                {/* Risk Analysis Section */}
                <div className="bg-white rounded-lg p-4 border border-red-200">
                  <button
                    onClick={() => toggleSection('risk')}
                    className="w-full flex items-center justify-between font-semibold text-gray-800 hover:text-red-600"
                  >
                    <span className="flex items-center gap-2">
                      <span>🔴 Risk Assessment</span>
                      <RiskBadge level={analysis.overall_risk_level} score={analysis.risk_score} />
                    </span>
                    <span className={`transition-transform ${expandedSection === 'risk' ? 'rotate-180' : ''}`}>
                      ▼
                    </span>
                  </button>

                  {expandedSection === 'risk' && (
                    <div className="mt-3 space-y-2 text-sm text-gray-700">
                      <p>
                        <strong>Overall Risk Level:</strong> {analysis.overall_risk_level}
                      </p>
                      <p>
                        <strong>Risk Score:</strong> {(analysis.risk_score * 100).toFixed(1)}%
                      </p>
                      <p>
                        <strong>Key Risks:</strong>
                      </p>
                      <ul className="list-disc list-inside ml-2">
                        {analysis.key_risks.map((risk, idx) => (
                          <li key={idx}>{risk}</li>
                        ))}
                      </ul>
                      <p>
                        <strong>Farmer Alert:</strong> {analysis.farmer_alert_message}
                      </p>
                    </div>
                  )}
                </div>

                {/* Disease Analysis Section */}
                <div className="bg-white rounded-lg p-4 border border-amber-200">
                  <button
                    onClick={() => toggleSection('disease')}
                    className="w-full flex items-center justify-between font-semibold text-gray-800 hover:text-amber-600"
                  >
                    <span>🌾 Disease & Weather Analysis</span>
                    <span className={`transition-transform ${expandedSection === 'disease' ? 'rotate-180' : ''}`}>
                      ▼
                    </span>
                  </button>

                  {expandedSection === 'disease' && (
                    <div className="mt-3 space-y-2 text-sm text-gray-700">
                      <p>
                        <strong>Disease Risk:</strong> {analysis.disease_risk_analysis}
                      </p>
                      <p>
                        <strong>Weather Risk:</strong> {analysis.weather_risk_analysis}
                      </p>
                      <p>
                        <strong>Short-term Forecast:</strong> {analysis.short_term_forecast}
                      </p>
                      <p>
                        <strong>Long-term Forecast:</strong> {analysis.long_term_forecast}
                      </p>
                    </div>
                  )}
                </div>

                {/* Preventive Actions Section */}
                <div className="bg-white rounded-lg p-4 border border-green-200">
                  <button
                    onClick={() => toggleSection('actions')}
                    className="w-full flex items-center justify-between font-semibold text-gray-800 hover:text-green-600"
                  >
                    <span>✅ Preventive Actions</span>
                    <span className={`transition-transform ${expandedSection === 'actions' ? 'rotate-180' : ''}`}>
                      ▼
                    </span>
                  </button>

                  {expandedSection === 'actions' && (
                    <div className="mt-3 space-y-2 text-sm text-gray-700">
                      <div>
                        <p className="font-semibold text-red-600">Immediate Actions:</p>
                        <ul className="list-disc list-inside ml-2">
                          {analysis.preventive_actions.immediate.map((action, idx) => (
                            <li key={idx}>{action}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="font-semibold text-amber-600">Short-term Actions (1-2 weeks):</p>
                        <ul className="list-disc list-inside ml-2">
                          {analysis.preventive_actions.short_term.map((action, idx) => (
                            <li key={idx}>{action}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="font-semibold text-blue-600">Long-term Actions (1+ months):</p>
                        <ul className="list-disc list-inside ml-2">
                          {analysis.preventive_actions.long_term.map((action, idx) => (
                            <li key={idx}>{action}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>

                {/* Market Intelligence Section */}
                {market && (
                  <div className="bg-white rounded-lg p-4 border border-blue-200">
                    <button
                      onClick={() => toggleSection('market')}
                      className="w-full flex items-center justify-between font-semibold text-gray-800 hover:text-blue-600"
                    >
                      <span>📈 Market Intelligence</span>
                      <span className={`transition-transform ${expandedSection === 'market' ? 'rotate-180' : ''}`}>
                        ▼
                      </span>
                    </button>

                    {expandedSection === 'market' && (
                      <div className="mt-3 space-y-2 text-sm text-gray-700">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="font-semibold">Current Price</p>
                            <p className="text-lg text-green-600">₹{market.current_price}/unit</p>
                          </div>
                          <div>
                            <p className="font-semibold">Price Trend</p>
                            <p className="text-lg">
                              {market.price_trend === 'increasing' ? '📈' : market.price_trend === 'decreasing' ? '📉' : '➡️'}{' '}
                              {market.price_trend}
                            </p>
                          </div>
                          <div>
                            <p className="font-semibold">Profit Potential</p>
                            <p className="text-lg text-green-600">{market.profit_potential}%</p>
                          </div>
                          <div>
                            <p className="font-semibold">Demand</p>
                            <p>{market.competition_level}</p>
                          </div>
                        </div>
                        <p>
                          <strong>Market Outlook:</strong> {market.market_outlook}
                        </p>
                        <p>
                          <strong>Selling Window:</strong> {market.selling_window}
                        </p>
                        <p>
                          <strong>Key Markets:</strong> {market.key_markets.join(', ')}
                        </p>
                        <p>
                          <strong>Demand Forecast:</strong> {market.demand_forecast}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {renderSubmissionDetails()}
              </div>
            ) : query.status === 'pending' ? (
              <div className="text-center py-4 text-gray-500">
                <p>⏳ Query submitted. Waiting for workflow response...</p>
              </div>
            ) : (
              renderSubmissionDetails()
            )}
          </td>
        </tr>
      )}
    </>
  );
};
