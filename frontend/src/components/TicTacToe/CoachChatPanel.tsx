import { useState } from 'react'
import type { TicTacToeChatHistoryItem } from '../../types/tictactoe'

interface CoachChatPanelProps {
  history: TicTacToeChatHistoryItem[]
  strategyHints: string[]
  isLoading: boolean
  disabled: boolean
  onAsk: (message: string) => Promise<void>
}

export function CoachChatPanel({
  history,
  strategyHints,
  isLoading,
  disabled,
  onAsk,
}: CoachChatPanelProps) {
  const [message, setMessage] = useState('')
  const visibleHistory = history.slice(-6)
  const quickPrompts = [
    'What is the best move now?',
    'How do I block the next threat?',
    'How can I force a draw from here?',
  ]

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const value = message.trim()
    if (!value || disabled || isLoading) return
    setMessage('')
    try {
      await onAsk(value)
    } catch {
      // Parent component surfaces error text; restoring draft helps quick retry.
      setMessage(value)
    }
  }

  return (
    <section className="rounded-2xl border border-slate-300 bg-white/85 p-5 shadow-sm">
      <h3 className="mb-1 text-base font-bold text-slate-800">AI Coach</h3>
      <p className="mb-4 text-sm text-slate-500">Ask strategy questions based on the live board state.</p>

      {strategyHints.length > 0 && (
        <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3.5">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-emerald-800">Strategy hints</p>
          <ul className="list-inside list-disc space-y-1 text-sm text-emerald-900">
            {strategyHints.map((hint, idx) => (
              <li key={`${hint}-${idx}`}>{hint}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mb-4 grid gap-2">
        {history.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-3 text-sm text-slate-500">
            Try: "How do I avoid losing next turn?"
          </p>
        ) : (
          visibleHistory.map((entry, idx) => (
            <div
              key={`${entry.role}-${idx}`}
              className={`rounded-xl border px-3 py-2.5 text-sm ${
                entry.role === 'user'
                  ? 'border-indigo-200 bg-indigo-50 text-indigo-900'
                  : 'border-slate-200 bg-slate-50 text-slate-800'
              }`}
            >
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide opacity-70">{entry.role}</p>
              <p>{entry.message}</p>
            </div>
          ))
        )}
        {history.length > visibleHistory.length && (
          <p className="text-xs text-slate-500">Showing latest {visibleHistory.length} messages.</p>
        )}
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        {quickPrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            disabled={disabled || isLoading}
            onClick={() => setMessage(prompt)}
            className="rounded-full border border-slate-300 bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-200 disabled:opacity-60"
          >
            {prompt}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask the AI coach..."
          disabled={disabled || isLoading}
          className="flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={disabled || isLoading || !message.trim()}
          className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? 'Thinking...' : 'Ask'}
        </button>
      </form>
    </section>
  )
}
