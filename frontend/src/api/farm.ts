import { getStoredToken } from './auth'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export interface FarmQueryRequest {
  query: string
  crop_type: string
  location: string
  weather: string
}

export interface RiskAnalysis {
  crop: string
  location: string
  overall_risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  risk_score: number
  key_risks: string[]
  weather_risk_analysis: string
  disease_risk_analysis: string
  market_risk_analysis: string
  short_term_forecast: string
  long_term_forecast: string
  preventive_actions: {
    immediate: string[]
    short_term: string[]
    long_term: string[]
  }
  farmer_alert_message: string
  confidence: number
}

export interface MarketIntelligence {
  crop: string
  location: string
  current_price: number
  price_trend: 'increasing' | 'decreasing' | 'stable'
  market_outlook: string
  profit_potential: number
  selling_window: string
  key_markets: string[]
  competition_level: 'low' | 'medium' | 'high'
  demand_forecast: string
  confidence: number
}

export interface FarmQuery {
  id: string
  farmer_id: string
  query: string
  crop_type: string
  location: string
  weather: string
  analysis?: RiskAnalysis
  market_intelligence?: MarketIntelligence
  submitted_payload?: Record<string, unknown>
  webhook_message?: string
  webhook_result?: unknown
  created_at: string
  status: 'pending' | 'completed' | 'error'
}

export interface FarmQuerySubmissionResult {
  analysis?: RiskAnalysis
  market_intelligence?: MarketIntelligence
  submitted_payload?: Record<string, unknown>
  webhook_message?: string
  webhook_result?: unknown
}

export interface FarmCurrentQueryResult {
  success: boolean
  source: string
  record_id: string
  created_at: string
  initial_input: Record<string, unknown>
}

function authHeaders(): HeadersInit {
  const token = getStoredToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Public farm submission endpoint: backend forwards this to N8N_WEBHOOK_URL from .env
export const submitFarmQuery = async (payload: FarmQueryRequest): Promise<FarmQuerySubmissionResult> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/farm/submit-query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders(),
      },
      body: JSON.stringify({
        query: payload.query,
        crop_type: payload.crop_type,
        location: payload.location,
        weather: payload.weather,
      }),
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`)
    }

    const data = await response.json()
    const result = data?.result ?? {}
    return {
      analysis: data?.analysis ?? result?.analysis,
      market_intelligence: data?.market_intelligence ?? result?.market_intelligence,
      submitted_payload: data?.submitted_payload,
      webhook_message: data?.message,
      webhook_result: result,
    }
  } catch (error) {
    console.error('Error submitting farm query:', error)
    throw error
  }
}

export const getCurrentFarmQuery = async (): Promise<FarmCurrentQueryResult> => {
  const response = await fetch(`${API_BASE_URL}/api/farm/current-query`, {
    method: 'GET',
    headers: {
      ...authHeaders(),
    },
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

// Simulate fetching all farm queries (mock for now)
export const fetchAllFarmQueries = async (): Promise<FarmQuery[]> => {
  return []
}

// Format risk level for display
export const getRiskColor = (level: string): string => {
  switch (level?.toUpperCase()) {
    case 'CRITICAL':
      return 'bg-red-900 text-white'
    case 'HIGH':
      return 'bg-red-500 text-white'
    case 'MEDIUM':
      return 'bg-amber-500 text-white'
    case 'LOW':
      return 'bg-green-500 text-white'
    default:
      return 'bg-gray-500 text-white'
  }
}

export const getRiskIcon = (level: string): string => {
  switch (level?.toUpperCase()) {
    case 'CRITICAL':
      return '🚨'
    case 'HIGH':
      return '🔴'
    case 'MEDIUM':
      return '🟠'
    case 'LOW':
      return '🟢'
    default:
      return '⚪'
  }
}
