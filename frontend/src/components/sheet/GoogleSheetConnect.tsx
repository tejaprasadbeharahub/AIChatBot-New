import { useState } from 'react'
import { connectGoogleSheet } from '../../api/sheet_agent'
import type { SheetDatasource } from '../../types/sheet_agent'

interface GoogleSheetConnectProps {
  chatId: string
  onConnected: (datasource: SheetDatasource) => void
}

export function GoogleSheetConnect({ chatId, onConnected }: GoogleSheetConnectProps) {
  const [open, setOpen] = useState(false)
  const [url, setUrl] = useState('')
  const [tab, setTab] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleConnect() {
    if (!url.trim()) return
    setLoading(true)
    setError(null)
    try {
      const datasource = await connectGoogleSheet({
        chat_id: chatId,
        sheet_url: url.trim(),
        sheet_tab: tab.trim() || undefined,
      })
      onConnected(datasource)
      setOpen(false)
      setUrl('')
      setTab('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect Google Sheet')
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        className="composer-send sheet-gsheet-btn"
        onClick={() => setOpen(true)}
        title="Connect a Google Sheet"
      >
        Connect Google Sheet
      </button>
    )
  }

  return (
    <div
      className="sheet-gsheet-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Connect Google Sheet"
      onClick={() => {
        if (!loading) {
          setOpen(false)
          setError(null)
        }
      }}
    >
      <div className="sheet-gsheet-panel" onClick={(e) => e.stopPropagation()}>
        <div className="sheet-gsheet-header">
          <span className="sheet-gsheet-title">Connect Google Sheet</span>
          <button
            type="button"
            className="sheet-gsheet-close"
            onClick={() => { setOpen(false); setError(null) }}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <label className="sheet-gsheet-label" htmlFor="gsheet-url">
          Sheet URL
          <input
            id="gsheet-url"
            type="url"
            className="sheet-gsheet-input"
            placeholder="https://docs.google.com/spreadsheets/d/..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
          />
        </label>

        <label className="sheet-gsheet-label" htmlFor="gsheet-tab">
          Tab name (optional)
          <input
            id="gsheet-tab"
            type="text"
            className="sheet-gsheet-input"
            placeholder="Sheet1"
            value={tab}
            onChange={(e) => setTab(e.target.value)}
            disabled={loading}
          />
        </label>

        {error && <p className="sheet-gsheet-error">{error}</p>}

        <div className="sheet-gsheet-actions">
          <button
            type="button"
            className="sheet-gsheet-cancel"
            onClick={() => { setOpen(false); setError(null) }}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="button"
            className="sheet-gsheet-connect"
            onClick={handleConnect}
            disabled={loading || !url.trim()}
          >
            {loading ? 'Connecting…' : 'Connect'}
          </button>
        </div>
      </div>
    </div>
  )
}
