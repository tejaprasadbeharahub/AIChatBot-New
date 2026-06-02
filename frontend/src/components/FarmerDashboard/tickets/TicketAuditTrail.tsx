import React from 'react';

interface Props {
  createdAt?: string | null;
  updatedAt?: string | null;
  status: string;
}

export const TicketAuditTrail: React.FC<Props> = ({ createdAt, updatedAt, status }) => {
  const events = [
    { title: 'Ticket Created', ts: createdAt },
    { title: 'Workflow Paused', ts: createdAt },
    { title: 'Admin Started Processing', ts: status !== 'OPEN' ? updatedAt : null },
    { title: 'AI Analysis Completed', ts: status === 'CLOSED' ? updatedAt : null },
    { title: 'Ticket Closed', ts: status === 'CLOSED' ? updatedAt : null },
  ];

  return (
    <ul className="space-y-2 text-sm">
      {events.map((event) => (
        <li key={event.title} className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2">
          <span className="text-slate-700">{event.title}</span>
          <span className="text-xs text-slate-500">{event.ts ? new Date(event.ts).toLocaleString() : 'Pending'}</span>
        </li>
      ))}
    </ul>
  );
};
