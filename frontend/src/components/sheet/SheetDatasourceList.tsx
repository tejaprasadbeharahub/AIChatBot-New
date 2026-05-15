import type { SheetDatasource } from '../../types/sheet_agent'
import { deleteSheetDatasource } from '../../api/sheet_agent'
import { useState } from 'react'

interface SheetDatasourceListProps {
  items: SheetDatasource[]
  isUploading?: boolean
  onDeleted?: (id: string) => void
  onSelect?: (datasource: SheetDatasource) => void
  selectedId?: string | null
}

function statusLabel(status: SheetDatasource['status']): string {
  switch (status) {
    case 'ready': return 'Ready'
    case 'processing': return 'Processing'
    case 'failed': return 'Failed'
    default: return 'Pending'
  }
}

function statusClass(status: SheetDatasource['status']): string {
  switch (status) {
    case 'ready': return 'sheet-ds-status ready'
    case 'processing': return 'sheet-ds-status processing'
    case 'failed': return 'sheet-ds-status failed'
    default: return 'sheet-ds-status pending'
  }
}

function sourceIcon(type: SheetDatasource['source_type']): string {
  switch (type) {
    case 'google_sheets': return '📊'
    case 'xlsx': return '📗'
    default: return '📄'
  }
}

function displayName(ds: SheetDatasource): string {
  if (ds.source_type === 'google_sheets') {
    return ds.sheet_tab ? `Google Sheet — ${ds.sheet_tab}` : 'Google Sheet'
  }
  return ds.file_name ?? 'Unknown file'
}

export function SheetDatasourceList({
  items,
  isUploading = false,
  onDeleted,
  onSelect,
  selectedId,
}: SheetDatasourceListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null)

  if (items.length === 0 && !isUploading) return null

  async function handleDelete(id: string, event: React.MouseEvent) {
    event.stopPropagation()
    if (!confirm('Remove this datasource?')) return
    setDeletingId(id)
    try {
      await deleteSheetDatasource(id)
      onDeleted?.(id)
    } catch {
      // silently ignore — parent can refresh list
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <section className="sheet-ds-list" aria-live="polite">
      <div className="sheet-ds-list-header">
        <p className="sheet-ds-title">Data Sources</p>
        {isUploading && <span className="sheet-ds-uploading">Uploading…</span>}
      </div>
      <div className="sheet-ds-items">
        {items.map((ds) => (
          <article
            key={ds.id}
            className={`sheet-ds-card${selectedId === ds.id ? ' selected' : ''}`}
            onClick={() => ds.status === 'ready' && onSelect?.(ds)}
            role={onSelect ? 'button' : undefined}
            tabIndex={onSelect && ds.status === 'ready' ? 0 : undefined}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                if (ds.status === 'ready') onSelect?.(ds)
              }
            }}
          >
            <div className="sheet-ds-icon">{sourceIcon(ds.source_type)}</div>
            <div className="sheet-ds-main">
              <p className="sheet-ds-name">{displayName(ds)}</p>
              {ds.row_count !== null && ds.column_count !== null ? (
                <p className="sheet-ds-meta">
                  {ds.row_count.toLocaleString()} rows · {ds.column_count} columns
                </p>
              ) : null}
              {ds.column_names && ds.column_names.length > 0 ? (
                <p className="sheet-ds-cols" title={ds.column_names.join(', ')}>
                  {ds.column_names.slice(0, 5).join(', ')}
                  {ds.column_names.length > 5 ? ` +${ds.column_names.length - 5} more` : ''}
                </p>
              ) : null}
              {ds.error_message ? <p className="sheet-ds-error">{ds.error_message}</p> : null}
            </div>
            <div className="sheet-ds-right">
              <span className={statusClass(ds.status)}>{statusLabel(ds.status)}</span>
              {onDeleted && (
                <button
                  type="button"
                  className="sheet-ds-delete"
                  onClick={(e) => handleDelete(ds.id, e)}
                  disabled={deletingId === ds.id}
                  aria-label="Delete datasource"
                >
                  {deletingId === ds.id ? '…' : '✕'}
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
