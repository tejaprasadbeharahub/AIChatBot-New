import React from 'react';
import type { WorkflowState } from '../../../api/tickets';

interface Props {
  state: WorkflowState;
}

const styles: Record<WorkflowState, string> = {
  WAITING: 'border-violet-200 bg-violet-50 text-violet-700',
  RUNNING: 'border-amber-200 bg-amber-50 text-amber-700',
  COMPLETED: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  CLOSED: 'border-slate-300 bg-slate-100 text-slate-700',
};

function getWorkflowLabel(state: WorkflowState): string {
  if (state === 'RUNNING') return 'PROCESSING';
  if (state === 'COMPLETED') return 'PROCESSED';
  if (state === 'CLOSED') return 'CLOSED';
  return state;
}

export const WorkflowStateBadge: React.FC<Props> = ({ state }) => (
  <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${styles[state]}`}>
    {getWorkflowLabel(state)}
  </span>
);
