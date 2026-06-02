import React from 'react';
import type { FarmTicket } from '../../../api/tickets';
import { WorkflowTimeline } from './WorkflowTimeline';
import { AIInsightsPanel } from './AIInsightsPanel';
import { TicketAuditTrail } from './TicketAuditTrail';

interface Props {
  ticket: FarmTicket;
}

export const ExpandableTicketDetails: React.FC<Props> = ({ ticket }) => (
  <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h4 className="text-sm font-semibold text-slate-900">Farmer Query</h4>
        <p className="mt-2 text-sm text-slate-600">{ticket.query}</p>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h4 className="text-sm font-semibold text-slate-900">Workflow State</h4>
        <p className="mt-1 text-xs text-slate-500">Workflow Paused is visible for OPEN tickets.</p>
        <div className="mt-3">
          <WorkflowTimeline status={ticket.ticket_status} workflowState={ticket.workflow_state} />
        </div>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h4 className="text-sm font-semibold text-slate-900">Ticket Timeline</h4>
        <div className="mt-3">
          <TicketAuditTrail createdAt={ticket.created_at} updatedAt={ticket.updated_at} status={ticket.ticket_status} />
        </div>
      </div>
    </div>

    <AIInsightsPanel ticket={ticket} />
  </div>
);
