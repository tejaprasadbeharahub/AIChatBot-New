import React from 'react';
import type { FarmTicket } from '../../../api/tickets';
import { TicketStatusBadge } from './TicketStatusBadge';
import { StartProcessingButton } from './StartProcessingButton';
import { CloseTicketButton } from './CloseTicketButton';

interface Props {
  ticket: FarmTicket;
  expanded: boolean;
  actionLoading: boolean;
  onToggle: () => void;
  onStart: () => void;
  onClose: () => void;
}

export const TicketRow: React.FC<Props> = ({
  ticket,
  expanded,
  actionLoading,
  onToggle,
  onStart,
  onClose,
}) => {
  const isProcessing = ticket.ticket_status === 'IN_PROGRESS' && ticket.workflow_state === 'RUNNING';
  const isProcessed = ticket.ticket_status === 'CLOSED' || (ticket.ticket_status === 'IN_PROGRESS' && ticket.workflow_state !== 'RUNNING');
  const canClose = ticket.ticket_status === 'IN_PROGRESS' && ticket.workflow_state !== 'RUNNING';

  return (
    <>
      <tr className="border-b border-slate-100 transition-colors hover:bg-sky-50/40">
        <td className="px-4 py-3 text-sm font-semibold text-slate-800">
          <div className="inline-flex items-center gap-2">
            <button
              type="button"
              onClick={onToggle}
              aria-label={expanded ? 'Hide details' : 'View details'}
              title={expanded ? 'Hide details' : 'View details'}
              className="inline-flex items-center justify-center rounded-md p-1 text-sky-700 transition hover:bg-sky-50 hover:text-sky-900"
            >
              <span aria-hidden="true" className="text-[11px] leading-none">
                {expanded ? '▼' : '▶'}
              </span>
            </button>
            <span>#{ticket.ticket_id}</span>
          </div>
        </td>
        <td className="px-4 py-3 text-sm text-slate-700">{ticket.farmer_name}</td>
        <td className="px-4 py-3 text-sm text-slate-700">{ticket.crop_type}</td>
        <td className="max-w-52 truncate px-4 py-3 text-sm text-slate-600">{ticket.query}</td>
        <td className="px-4 py-3"><TicketStatusBadge status={ticket.ticket_status} workflowState={ticket.workflow_state} /></td>
        <td className="px-4 py-3">
          <div className="flex items-center gap-2 whitespace-nowrap">
            {ticket.ticket_status === 'OPEN' && (
              <StartProcessingButton onClick={onStart} isLoading={actionLoading} disabled={actionLoading} />
            )}
            {isProcessing && (
              <>
                <span className="inline-flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">
                  <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
                  Processing
                </span>
              </>
            )}
            {canClose && (
              <>
                <span className="inline-flex items-center rounded-lg border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                  Processed
                </span>
                <CloseTicketButton onClick={onClose} isLoading={actionLoading} disabled={actionLoading} />
              </>
            )}
            {ticket.ticket_status === 'CLOSED' && (
              <div className="flex gap-2">
                <button type="button" className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 transition hover:bg-slate-50">Download Report</button>
                <button type="button" className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 transition hover:bg-slate-50">View Report</button>
              </div>
            )}
            {ticket.ticket_status === 'IN_PROGRESS' && isProcessed && !canClose && (
              <span className="inline-flex items-center rounded-lg border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                Processed
              </span>
            )}
          </div>
        </td>
      </tr>
    </>
  );
};
