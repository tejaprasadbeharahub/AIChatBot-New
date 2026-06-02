import React from 'react';

interface Props {
  status: string;
  workflowState: string;
}

const STEPS = ['OPEN', 'WAITING', 'IN_PROGRESS', 'AI_ANALYSIS', 'CLOSED'];

function isStepDone(step: string, status: string, workflowState: string): boolean {
  const doneMap: Record<string, boolean> = {
    OPEN: true,
    WAITING: status === 'OPEN' || workflowState === 'WAITING' || status === 'IN_PROGRESS' || status === 'CLOSED',
    IN_PROGRESS: status === 'IN_PROGRESS' || status === 'CLOSED',
    AI_ANALYSIS: workflowState === 'RUNNING' || workflowState === 'COMPLETED' || workflowState === 'CLOSED' || status === 'CLOSED',
    CLOSED: status === 'CLOSED',
  };
  return doneMap[step];
}

export const WorkflowTimeline: React.FC<Props> = ({ status, workflowState }) => (
  <ol className="space-y-2">
    {STEPS.map((step) => {
      const done = isStepDone(step, status, workflowState);
      return (
        <li key={step} className="flex items-center gap-2 text-sm">
          <span className={`h-2.5 w-2.5 rounded-full ${done ? 'bg-sky-600' : 'bg-slate-300'}`} />
          <span className={done ? 'text-slate-900 font-medium' : 'text-slate-500'}>{step}</span>
        </li>
      );
    })}
  </ol>
);
