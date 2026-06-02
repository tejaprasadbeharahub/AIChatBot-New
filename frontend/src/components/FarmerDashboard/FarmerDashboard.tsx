import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { closeTicket, createTicket, fetchTickets, resumeTicket } from '../../api/tickets';
import type { FarmTicket, TicketCreateRequest } from '../../api/tickets';
import { QueryInputPanel } from './QueryInputPanel';
import { TicketTable } from './tickets/TicketTable';
import { ConfirmationModal } from './tickets/ConfirmationModal';
import { LoadingOverlay } from './tickets/LoadingOverlay';
import { ToastNotifications } from './tickets/ToastNotifications';
import type { ToastMessage } from './tickets/ToastNotifications';

function kpiValue(value: number): string {
  return value.toLocaleString();
}

type TicketFilter = 'ALL' | 'OPEN' | 'IN_PROGRESS' | 'CLOSED';

export const FarmerDashboard: React.FC = () => {
  const queryClient = useQueryClient();
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [activeActionTicket, setActiveActionTicket] = useState<number | null>(null);
  const [confirm, setConfirm] = useState<{ type: 'resume' | 'close'; ticket: FarmTicket } | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [activeFilter, setActiveFilter] = useState<TicketFilter>('ALL');

  const { data: tickets = [], isLoading, isFetching } = useQuery({
    queryKey: ['farm-tickets'],
    queryFn: fetchTickets,
  });

  const addToast = (type: ToastMessage['type'], text: string) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((prev) => [...prev, { id, type, text }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 3500);
  };

  const createMutation = useMutation({
    mutationFn: createTicket,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['farm-tickets'] });
      addToast('success', 'Ticket created and workflow paused successfully.');
    },
    onError: () => addToast('error', 'Failed to create ticket.'),
  });

  const resumeMutation = useMutation({
    mutationFn: (ticketId: number) => resumeTicket(ticketId),
    onMutate: async (ticketId) => {
      setActiveActionTicket(ticketId);
      await queryClient.cancelQueries({ queryKey: ['farm-tickets'] });
      const previous = queryClient.getQueryData<FarmTicket[]>(['farm-tickets']) || [];
      queryClient.setQueryData<FarmTicket[]>(
        ['farm-tickets'],
        previous.map((ticket) =>
          ticket.ticket_id === ticketId
            ? { ...ticket, ticket_status: 'IN_PROGRESS', workflow_state: 'RUNNING' }
            : ticket
        )
      );
      return { previous };
    },
    onError: (_error, _ticketId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['farm-tickets'], context.previous);
      }
      addToast('error', 'Failed to resume workflow.');
    },
    onSuccess: (response) => {
      queryClient.setQueryData<FarmTicket[]>(
        ['farm-tickets'],
        (prev = []) => prev.map((ticket) => (ticket.ticket_id === response.record.ticket_id ? response.record : ticket))
      );
      addToast('success', 'Workflow resumed successfully.');
    },
    onSettled: () => {
      setActiveActionTicket(null);
      void queryClient.invalidateQueries({ queryKey: ['farm-tickets'] });
    },
  });

  const closeMutation = useMutation({
    mutationFn: (ticketId: number) => closeTicket(ticketId),
    onMutate: async (ticketId) => {
      setActiveActionTicket(ticketId);
      await queryClient.cancelQueries({ queryKey: ['farm-tickets'] });
      const previous = queryClient.getQueryData<FarmTicket[]>(['farm-tickets']) || [];
      queryClient.setQueryData<FarmTicket[]>(
        ['farm-tickets'],
        previous.map((ticket) =>
          ticket.ticket_id === ticketId
            ? { ...ticket, ticket_status: 'CLOSED', workflow_state: 'CLOSED' }
            : ticket
        )
      );
      return { previous };
    },
    onError: (_error, _ticketId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['farm-tickets'], context.previous);
      }
      addToast('error', 'Failed to close ticket.');
    },
    onSuccess: (response) => {
      queryClient.setQueryData<FarmTicket[]>(
        ['farm-tickets'],
        (prev = []) => prev.map((ticket) => (ticket.ticket_id === response.record.ticket_id ? response.record : ticket))
      );
      addToast('success', 'Ticket closed successfully.');
    },
    onSettled: () => {
      setActiveActionTicket(null);
      void queryClient.invalidateQueries({ queryKey: ['farm-tickets'] });
    },
  });

  const metrics = useMemo(() => {
    const total = tickets.length;
    const open = tickets.filter((ticket) => ticket.ticket_status === 'OPEN').length;
    const inProgress = tickets.filter((ticket) => ticket.ticket_status === 'IN_PROGRESS').length;
    const closed = tickets.filter((ticket) => ticket.ticket_status === 'CLOSED').length;

    return [
      {
        label: 'Open',
        value: kpiValue(open),
        trend: 'Needs action',
        icon: '📬',
        tone: 'from-sky-100 via-cyan-50 to-white',
        filter: 'OPEN' as TicketFilter,
      },
      {
        label: 'In Progress',
        value: kpiValue(inProgress),
        trend: 'Running',
        icon: '⚙️',
        tone: 'from-amber-100 via-yellow-50 to-white',
        filter: 'IN_PROGRESS' as TicketFilter,
      },
      {
        label: 'Closed',
        value: kpiValue(closed),
        trend: 'Completed',
        icon: '✅',
        tone: 'from-emerald-100 via-lime-50 to-white',
        filter: 'CLOSED' as TicketFilter,
      },
      {
        label: 'All Tickets',
        value: kpiValue(total),
        trend: 'Total volume',
        icon: '🧾',
        tone: 'from-fuchsia-100 via-rose-50 to-white',
        filter: 'ALL' as TicketFilter,
      },
    ];
  }, [tickets]);

  const visibleTickets = useMemo(
    () => (activeFilter === 'ALL' ? tickets : tickets.filter((ticket) => ticket.ticket_status === activeFilter)),
    [activeFilter, tickets]
  );

  const activeFilterLabel = useMemo(() => {
    if (activeFilter === 'IN_PROGRESS') return 'In Progress';
    if (activeFilter === 'ALL') return 'All Tickets';
    return `${activeFilter.charAt(0)}${activeFilter.slice(1).toLowerCase()}`;
  }, [activeFilter]);

  const handleCreateTicket = (payload: TicketCreateRequest) => {
    createMutation.mutate(payload);
  };

  const handleStartProcessing = (ticket: FarmTicket) => {
    setConfirm({ type: 'resume', ticket });
  };

  const handleCloseTicket = (ticket: FarmTicket) => {
    setConfirm({ type: 'close', ticket });
  };

  const confirmAction = () => {
    if (!confirm) return;
    if (confirm.type === 'resume') {
      resumeMutation.mutate(confirm.ticket.ticket_id);
    } else {
      closeMutation.mutate(confirm.ticket.ticket_id);
    }
    setConfirm(null);
  };

  const toggleExpand = (ticketId: number) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(ticketId)) next.delete(ticketId);
      else next.add(ticketId);
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.30),_transparent_45%),radial-gradient(circle_at_18%_30%,_rgba(20,184,166,0.25),_transparent_42%),radial-gradient(circle_at_bottom_left,_rgba(244,114,182,0.24),_transparent_38%),linear-gradient(155deg,_#f8fafc_0%,_#eef6ff_48%,_#f8fafc_100%)] p-4 md:p-6">
      <ToastNotifications toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((toast) => toast.id !== id))} />
      <ConfirmationModal
        open={Boolean(confirm)}
        title={confirm?.type === 'resume' ? 'Resume Workflow' : 'Close Ticket'}
        message={
          confirm?.type === 'resume'
            ? `Start AI processing for ticket #${confirm?.ticket.ticket_id}?`
            : `Close ticket #${confirm?.ticket.ticket_id}?`
        }
        confirmLabel={confirm?.type === 'resume' ? 'Start Processing' : 'Close Ticket'}
        onCancel={() => setConfirm(null)}
        onConfirm={confirmAction}
      />

      <main className="mx-auto max-w-[1500px] space-y-6">
        <header className="relative overflow-hidden rounded-3xl border border-white/70 bg-white/80 p-6 shadow-[0_20px_65px_-34px_rgba(15,23,42,0.65)] backdrop-blur-xl">
          <div className="pointer-events-none absolute -right-24 -top-20 h-56 w-56 rounded-full bg-gradient-to-br from-cyan-300/40 to-sky-300/0 blur-2xl" />
          <div className="pointer-events-none absolute -left-20 -bottom-20 h-52 w-52 rounded-full bg-gradient-to-br from-pink-300/30 to-rose-200/0 blur-2xl" />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">Farm Tickets</h1>
              <p className="mt-1 text-sm text-slate-600">Click tiles to filter the grid by status. Data updates when you refresh the page.</p>
            </div>
            <span className="inline-flex items-center rounded-full border border-sky-200/70 bg-gradient-to-r from-sky-50 to-cyan-50 px-3 py-1 text-xs font-semibold text-sky-700 shadow-sm">
              Manual refresh mode
            </span>
          </div>
        </header>

        <section className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <button
              key={metric.label}
              type="button"
              onClick={() => setActiveFilter((prev) => (prev === metric.filter ? 'ALL' : metric.filter))}
              className={`group relative overflow-hidden rounded-2xl border p-5 text-left shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/60 ${
                activeFilter === metric.filter
                  ? `border-sky-300/90 bg-gradient-to-br ${metric.tone} shadow-[0_18px_36px_-22px_rgba(14,165,233,0.75)]`
                  : `border-slate-200/80 bg-gradient-to-br ${metric.tone}`
              }`}
            >
              <span className="pointer-events-none absolute -right-10 -top-10 h-24 w-24 rounded-full bg-white/40 blur-xl transition duration-200 group-hover:scale-110" />
              <div className="flex items-start justify-between">
                <p className="text-xs uppercase tracking-wide text-slate-500">{metric.label}</p>
                <span className="text-lg">{metric.icon}</span>
              </div>
              <p className="mt-2 text-3xl font-bold leading-none text-slate-900">{metric.value}</p>
              <p className="mt-2 text-xs font-medium text-slate-500">{metric.trend}</p>
              <p className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-sky-700/80">
                {activeFilter === metric.filter ? 'Active filter' : 'Click to filter'}
              </p>
            </button>
          ))}
        </section>

        <section className="grid grid-cols-1 gap-6 xl:grid-cols-12 relative">
          <div className="xl:col-span-3">
            <QueryInputPanel onSubmit={handleCreateTicket} isLoading={createMutation.isPending} />
          </div>

          <div className="relative xl:col-span-9">
            <LoadingOverlay visible={isLoading || isFetching} message="Loading ticket records..." />
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-white/70 bg-white/70 px-4 py-3 text-sm text-slate-700 shadow-sm backdrop-blur">
              <p>
                Showing <span className="font-semibold text-slate-900">{visibleTickets.length}</span> ticket(s) for{' '}
                <span className="font-semibold text-sky-700">{activeFilterLabel}</span>
              </p>
              <button
                type="button"
                onClick={() => void queryClient.invalidateQueries({ queryKey: ['farm-tickets'] })}
                className="rounded-lg border border-sky-200 bg-gradient-to-r from-sky-50 to-cyan-50 px-3 py-1.5 text-xs font-semibold text-sky-700 transition hover:from-sky-100 hover:to-cyan-100"
              >
                Refresh grid
              </button>
            </div>
            <TicketTable
              tickets={visibleTickets}
              expandedRows={expandedRows}
              actionLoadingId={activeActionTicket}
              onToggleExpand={toggleExpand}
              onStartProcessing={handleStartProcessing}
              onCloseTicket={handleCloseTicket}
            />
          </div>
        </section>
      </main>
    </div>
  );
};
