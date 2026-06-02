import React from 'react';
import type { TicketStatus } from '../../../api/tickets';
import type { WorkflowState } from '../../../api/tickets';

interface Props {
  status: TicketStatus;
  workflowState?: WorkflowState;
}

const styles: Record<TicketStatus, string> = {
  OPEN: 'border-sky-200 bg-sky-50 text-sky-700',
  IN_PROGRESS: 'border-amber-200 bg-amber-50 text-amber-700',
  CLOSED: 'border-emerald-200 bg-emerald-50 text-emerald-700',
};

function getDisplayStatus(status: TicketStatus, workflowState?: WorkflowState): string {
  if (status === 'CLOSED') return 'CLOSED';
  if (status === 'IN_PROGRESS' && workflowState !== 'RUNNING') return 'PROCESSED';
  if (status === 'IN_PROGRESS') return 'PROCESSING';
  return status;
}

export const TicketStatusBadge: React.FC<Props> = ({ status, workflowState }) => (
  <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${styles[status]}`}>
    {getDisplayStatus(status, workflowState)}
  </span>
);
