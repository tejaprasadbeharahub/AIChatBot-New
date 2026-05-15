import { useState, useRef } from 'react'
import type { SheetDatasource } from '../../types/sheet_agent'
import { querySheetDatasource } from '../../api/sheet_agent'
import type { SheetQueryResponse } from '../../types/sheet_agent'

interface SheetComposerProps {
  chatId: string
  datasource: SheetDatasource
  onResult: (result: SheetQueryResponse) => void
  onClear: () => void
}

const SAMPLE_QUESTIONS = [
  'Show the first 10 rows',
  'What are the column names?',
  'What is the total of the numeric columns?',
  'Show a summary of the data',
]

export function SheetComposer({ chatId, datasource, onResult, onClear }: SheetComposerProps) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  async function handleSubmit(q?: string) {
    const text = (q ?? question).trim()
    if (!text || loading) return
    setLoading(true)
    setError(null)
    try {
      const result = await querySheetDatasource({
        datasource_id: datasource.id,
        question: text,
        chat_id: chatId,
      })
      onResult(result)
      setQuestion('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed')
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSubmit()
    }
  }

  const dsName =
    datasource.source_type === 'google_sheets'
      ? datasource.sheet_tab ?? 'Google Sheet'
      : datasource.file_name ?? 'Datasource'

  return (
    <div className="sheet-composer">
      <div className="sheet-composer-context">
        <span className="sheet-composer-icon">
          {datasource.source_type === 'google_sheets' ? '📊' : datasource.source_type === 'xlsx' ? '📗' : '📄'}
        </span>
        <span className="sheet-composer-dsname" title={dsName}>{dsName}</span>
        {datasource.row_count !== null ? (
          <span className="sheet-composer-meta">{datasource.row_count.toLocaleString()} rows</span>
        ) : null}
        <button
          type="button"
          className="sheet-composer-clear"
          onClick={onClear}
          title="Switch datasource"
        >
          ✕
        </button>
      </div>

      <div className="sheet-composer-samples">
        {SAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            className="sheet-sample-pill"
            onClick={() => void handleSubmit(q)}
            disabled={loading}
          >
            {q}
          </button>
        ))}
      </div>

      <div className="sheet-composer-input-row">
        <textarea
          ref={textareaRef}
          className="sheet-composer-textarea"
          placeholder="Ask a question about your data…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          rows={2}
        />
        <button
          type="button"
          className="sheet-composer-send"
          onClick={() => void handleSubmit()}
          disabled={loading || !question.trim()}
        >
          {loading ? '…' : 'Ask'}
        </button>
      </div>

      {error && <p className="sheet-composer-error">{error}</p>}
    </div>
  )
}
