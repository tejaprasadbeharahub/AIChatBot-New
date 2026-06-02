import React, { useState } from 'react';
import type { FarmTicket } from '../../../api/tickets';
import { TicketRow } from './TicketRow';
import { ExpandableTicketDetails } from './ExpandableTicketDetails';

const PAGE_SIZE = 10;

interface Props {
  tickets: FarmTicket[];
  expandedRows: Set<number>;
  actionLoadingId: number | null;
  onToggleExpand: (id: number) => void;
  onStartProcessing: (ticket: FarmTicket) => void;
  onCloseTicket: (ticket: FarmTicket) => void;
}

const COLUMNS: { label: string; icon: string }[] = [
  { label: 'Ticket ID',    icon: '🎫' },
  { label: 'Farmer Name',  icon: '👤' },
  { label: 'Crop',         icon: '🌾' },
  { label: 'Query',        icon: '💬' },
  { label: 'Status',       icon: '🔖' },
  { label: 'Actions',      icon: '⚡' },
];

export const TicketTable: React.FC<Props> = ({
  tickets,
  expandedRows,
  actionLoadingId,
  onToggleExpand,
  onStartProcessing,
  onCloseTicket,
}) => {
  const [page, setPage] = useState(1);

  const totalPages = Math.max(1, Math.ceil(tickets.length / PAGE_SIZE));
  const safePage   = Math.min(page, totalPages);
  const start      = (safePage - 1) * PAGE_SIZE;
  const pageSlice  = tickets.slice(start, start + PAGE_SIZE);

  if (tickets.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500">
        No tickets found in farm_tickets table.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white/95 shadow-sm backdrop-blur">
      {/* ── Table ── */}
      <div className="overflow-x-auto">
        <table className="min-w-full text-left">
          <thead>
            <tr className="bg-gradient-to-r from-sky-600 via-cyan-500 to-teal-500 text-white">
              {COLUMNS.map((col) => (
                <th
                  key={col.label}
                  className="px-4 py-3 text-xs font-semibold uppercase tracking-wider"
                >
                  <span className="inline-flex items-center gap-1.5">
                    <span>{col.icon}</span>
                    <span>{col.label}</span>
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageSlice.map((ticket) => {
              const expanded = expandedRows.has(ticket.ticket_id);
              return (
                <React.Fragment key={ticket.ticket_id}>
                  <TicketRow
                    ticket={ticket}
                    expanded={expanded}
                    actionLoading={actionLoadingId === ticket.ticket_id}
                    onToggle={() => onToggleExpand(ticket.ticket_id)}
                    onStart={() => onStartProcessing(ticket)}
                    onClose={() => onCloseTicket(ticket)}
                  />
                  {expanded && (
                    <tr className="border-b border-slate-200 bg-slate-50">
                      <td colSpan={6} className="px-4 py-4">
                        <ExpandableTicketDetails ticket={ticket} />
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ── Pagination ── */}
      <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50/80 px-5 py-3">
        <p className="text-xs text-slate-500">
          Showing <span className="font-semibold text-slate-700">{start + 1}</span>–
          <span className="font-semibold text-slate-700">{Math.min(start + PAGE_SIZE, tickets.length)}</span>{' '}
          of <span className="font-semibold text-slate-700">{tickets.length}</span> tickets
        </p>
        <div className="flex items-center gap-1.5">
          {/* First */}
          <button
            type="button"
            onClick={() => setPage(1)}
            disabled={safePage === 1}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 transition hover:border-sky-300 hover:text-sky-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            «
          </button>
          {/* Prev */}
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={safePage === 1}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 transition hover:border-sky-300 hover:text-sky-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            ‹
          </button>
          {/* Page numbers */}
          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter((p) => p === 1 || p === totalPages || Math.abs(p - safePage) <= 1)
            .reduce<(number | '…')[]>((acc, p, idx, arr) => {
              if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push('…');
              acc.push(p);
              return acc;
            }, [])
            .map((item, idx) =>
              item === '…' ? (
                <span key={`ellipsis-${idx}`} className="px-1 text-xs text-slate-400">…</span>
              ) : (
                <button
                  key={item}
                  type="button"
                  onClick={() => setPage(item as number)}
                  className={`min-w-[28px] rounded-lg border px-2.5 py-1 text-xs font-semibold transition ${
                    safePage === item
                      ? 'border-sky-500 bg-sky-600 text-white shadow-sm'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-sky-300 hover:text-sky-700'
                  }`}
                >
                  {item}
                </button>
              )
            )}
          {/* Next */}
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={safePage === totalPages}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 transition hover:border-sky-300 hover:text-sky-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            ›
          </button>
          {/* Last */}
          <button
            type="button"
            onClick={() => setPage(totalPages)}
            disabled={safePage === totalPages}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 transition hover:border-sky-300 hover:text-sky-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            »
          </button>
        </div>
      </div>
    </div>
  );
};
