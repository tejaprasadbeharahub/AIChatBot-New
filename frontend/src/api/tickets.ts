import axios from 'axios';

export type TicketStatus = 'OPEN' | 'IN_PROGRESS' | 'CLOSED';
export type WorkflowState = 'WAITING' | 'RUNNING' | 'COMPLETED' | 'CLOSED';

export interface FarmTicket {
  ticket_id: number;
  farmer_name: string;
  farmer_email: string;
  query: string;
  crop_type: string;
  location: string;
  weather: string;
  ticket_status: TicketStatus;
  workflow_state: WorkflowState;
  risk_level?: string | null;
  ai_confidence?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
  resume_url?: string | null;
  extra?: Record<string, unknown>;
}

export interface TicketCreateRequest {
  farmer_name: string;
  farmer_email: string;
  query: string;
  crop_type: string;
  location: string;
  weather: string;
}

interface TicketListResponse {
  success: boolean;
  records: FarmTicket[];
}

interface TicketMutationResponse {
  success: boolean;
  message: string;
  record: FarmTicket;
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function fetchTickets(): Promise<FarmTicket[]> {
  const response = await api.get<TicketListResponse>('/api/tickets');
  return response.data.records || [];
}

export async function createTicket(payload: TicketCreateRequest): Promise<TicketMutationResponse> {
  const response = await api.post<TicketMutationResponse>('/api/tickets', payload);
  return response.data;
}

export async function resumeTicket(ticket_id: number): Promise<TicketMutationResponse> {
  const response = await api.post<TicketMutationResponse>('/api/resume-ticket', {
    ticket_id,
    ticket_status: 'IN_PROGRESS',
  });
  return response.data;
}

export async function closeTicket(ticket_id: number): Promise<TicketMutationResponse> {
  const response = await api.post<TicketMutationResponse>('/api/close-ticket', {
    ticket_id,
    ticket_status: 'CLOSED',
  });
  return response.data;
}
