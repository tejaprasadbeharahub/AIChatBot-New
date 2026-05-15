import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { createDBConnection, deleteDBConnection, listDBConnections, updateDBConnection, validateDBConnection } from '../../api/nl_sql'
import type { DBConnection, DBConnectionCreateRequest, DBProvider } from '../../types/nl_sql'

type Props = {
  onConnectionSelected?: (connectionId: string) => void
  selectedConnectionId?: string | null
}

const PROVIDERS: { value: DBProvider; label: string }[] = [
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'mysql', label: 'MySQL' },
  { value: 'sqlserver', label: 'SQL Server' },
  { value: 'sqlite', label: 'SQLite' },
]

const defaultForm: DBConnectionCreateRequest = {
  name: '',
  provider: 'postgresql',
  host: '',
  port: undefined,
  database_name: '',
  username: '',
  password: '',
}

type ValidationState = { [id: string]: { success: boolean; message: string } | undefined }

export function DBConnectionManager({ onConnectionSelected, selectedConnectionId }: Props) {
  const [connections, setConnections] = useState<DBConnection[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isAddingNew, setIsAddingNew] = useState(false)
  const [form, setForm] = useState<DBConnectionCreateRequest>(defaultForm)
  const [saving, setSaving] = useState(false)
  const [validationState, setValidationState] = useState<ValidationState>({})
  const [validating, setValidating] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    listDBConnections()
      .then((items) => setConnections(items))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Failed to load connections'))
      .finally(() => setLoading(false))
  }, [])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (!form.name.trim()) return
    setSaving(true)
    setError(null)
    try {
      const created = await createDBConnection(form)
      setConnections((prev) => [created, ...prev])
      setIsAddingNew(false)
      setForm(defaultForm)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create connection')
    } finally {
      setSaving(false)
    }
  }

  async function handleValidate(id: string) {
    setValidating(id)
    try {
      const result = await validateDBConnection(id)
      setValidationState((prev) => ({ ...prev, [id]: result }))
      if (result.success) {
        setConnections((prev) =>
          prev.map((conn) =>
            conn.id === id ? { ...conn, last_validated_at: new Date().toISOString() } : conn,
          ),
        )
      }
    } catch (err: unknown) {
      setValidationState((prev) => ({
        ...prev,
        [id]: { success: false, message: err instanceof Error ? err.message : 'Validation failed' },
      }))
    } finally {
      setValidating(null)
    }
  }

  async function handleToggleActive(conn: DBConnection) {
    try {
      const updated = await updateDBConnection(conn.id, { is_active: !conn.is_active })
      setConnections((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update connection')
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm('Delete this database connection?')) return
    setDeleting(id)
    try {
      await deleteDBConnection(id)
      setConnections((prev) => prev.filter((c) => c.id !== id))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete connection')
    } finally {
      setDeleting(null)
    }
  }

  const isSQLite = form.provider === 'sqlite'

  return (
    <div className="db-manager">
      <div className="db-manager-header">
        <h3>Database Connections</h3>
        <button
          type="button"
          className="ghost-btn"
          onClick={() => {
            setIsAddingNew((v) => !v)
            setForm(defaultForm)
          }}
        >
          {isAddingNew ? '✕ Cancel' : '+ Add Connection'}
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}

      {isAddingNew && (
        <form onSubmit={(e) => void handleCreate(e)} className="db-form">
          <label className="db-label">
            Name
            <input
              className="db-input"
              placeholder="My Database"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              required
            />
          </label>
          <label className="db-label">
            Provider
            <select
              className="db-input"
              value={form.provider}
              onChange={(e) => setForm((f) => ({ ...f, provider: e.target.value as DBProvider }))}
            >
              {PROVIDERS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </label>

          {isSQLite ? (
            <label className="db-label">
              File Path
              <input
                className="db-input"
                placeholder="/path/to/database.db"
                value={form.sqlite_path ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, sqlite_path: e.target.value }))}
              />
            </label>
          ) : (
            <>
              <div className="db-row">
                <label className="db-label db-label-flex">
                  Host
                  <input
                    className="db-input"
                    placeholder="localhost"
                    value={form.host ?? ''}
                    onChange={(e) => setForm((f) => ({ ...f, host: e.target.value }))}
                  />
                </label>
                <label className="db-label db-label-sm">
                  Port
                  <input
                    className="db-input"
                    type="number"
                    placeholder="5432"
                    value={form.port ?? ''}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, port: e.target.value ? parseInt(e.target.value, 10) : undefined }))
                    }
                  />
                </label>
              </div>
              <label className="db-label">
                Database Name
                <input
                  className="db-input"
                  placeholder="my_database"
                  value={form.database_name ?? ''}
                  onChange={(e) => setForm((f) => ({ ...f, database_name: e.target.value }))}
                />
              </label>
              <label className="db-label">
                Username
                <input
                  className="db-input"
                  placeholder="db_user"
                  value={form.username ?? ''}
                  onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                />
              </label>
              <label className="db-label">
                Password
                <input
                  className="db-input"
                  type="password"
                  placeholder="(optional)"
                  value={form.password ?? ''}
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                />
              </label>
            </>
          )}

          <button type="submit" className="auth-submit" style={{ marginTop: '8px' }} disabled={saving}>
            {saving ? 'Saving...' : 'Save Connection'}
          </button>
        </form>
      )}

      {loading && <p className="meta-text">Loading connections...</p>}

      {!loading && connections.length === 0 && !isAddingNew && (
        <p className="meta-text">No database connections yet. Add one to get started.</p>
      )}

      <div className="db-connection-list">
        {connections.map((conn) => {
          const vs = validationState[conn.id]
          const isSelected = selectedConnectionId === conn.id
          return (
            <div
              key={conn.id}
              className={`db-connection-item${isSelected ? ' db-connection-item--selected' : ''}`}
              onClick={() => onConnectionSelected?.(conn.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') onConnectionSelected?.(conn.id)
              }}
            >
              <div className="db-connection-info">
                <span className="db-connection-name">{conn.name}</span>
                <span className="db-connection-meta">
                  {conn.provider.toUpperCase()}{conn.host ? ` · ${conn.host}` : ''}
                  {conn.database_name ? ` / ${conn.database_name}` : ''}
                </span>
                {vs && (
                  <span className={`sql-badge ${vs.success ? 'sql-badge--success' : 'sql-badge--error'}`} style={{ fontSize: '11px', marginTop: '4px' }}>
                    {vs.message}
                  </span>
                )}
              </div>
              <div className="db-connection-actions">
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={(e) => { e.stopPropagation(); void handleValidate(conn.id) }}
                  disabled={validating === conn.id}
                >
                  {validating === conn.id ? 'Testing...' : 'Test'}
                </button>
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={(e) => { e.stopPropagation(); void handleToggleActive(conn) }}
                >
                  {conn.is_active ? 'Disable' : 'Enable'}
                </button>
                <button
                  type="button"
                  className="ghost-btn"
                  style={{ color: '#b02020' }}
                  onClick={(e) => { e.stopPropagation(); void handleDelete(conn.id) }}
                  disabled={deleting === conn.id}
                >
                  Delete
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
