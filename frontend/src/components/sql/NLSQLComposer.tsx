import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { listDBConnections } from '../../api/nl_sql'
import type { DBConnection } from '../../types/nl_sql'

type Props = {
  onSubmit: (connectionId: string, question: string) => void
  isLoading: boolean
  activeChatId?: string | null
  disabled?: boolean
}

export function NLSQLComposer({ onSubmit, isLoading, disabled }: Props) {
  const [connections, setConnections] = useState<DBConnection[]>([])
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>('')
  const [question, setQuestion] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listDBConnections()
      .then((items) => {
        const active = items.filter((c) => c.is_active)
        setConnections(active)
        if (active.length > 0 && !selectedConnectionId) {
          setSelectedConnectionId(active[0].id)
        }
      })
      .catch(() => {
        setConnections([])
      })
  }, [])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!selectedConnectionId) {
      setError('Select a database connection first')
      return
    }
    if (!question.trim()) {
      setError('Enter a question')
      return
    }
    setError(null)
    onSubmit(selectedConnectionId, question.trim())
  }

  if (connections.length === 0) {
    return (
      <p className="meta-text" style={{ padding: '8px 0' }}>
        No active database connections. Add one via <strong>Database Connections</strong> in the sidebar.
      </p>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="nl-sql-composer">
      <select
        className="nl-sql-connection-select"
        value={selectedConnectionId}
        onChange={(e) => setSelectedConnectionId(e.target.value)}
        disabled={isLoading || disabled}
      >
        {connections.map((conn) => (
          <option key={conn.id} value={conn.id}>
            {conn.name} ({conn.provider.toUpperCase()})
          </option>
        ))}
      </select>
      <textarea
        className="composer-input"
        rows={2}
        placeholder="Ask a database question in plain English…"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        disabled={isLoading || disabled}
      />
      <button
        type="submit"
        className="composer-send"
        disabled={isLoading || disabled || !question.trim() || !selectedConnectionId}
      >
        {isLoading ? 'Querying…' : 'Ask Database'}
      </button>
      {error && <p className="error-text">{error}</p>}
    </form>
  )
}
