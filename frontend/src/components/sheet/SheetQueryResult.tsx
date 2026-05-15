import { useState } from 'react'
import type { SheetQueryResponse } from '../../types/sheet_agent'

interface SheetQueryResultProps {
  result: SheetQueryResponse
}

const PAGE_SIZE = 25

export function SheetQueryResult({ result }: SheetQueryResultProps) {
  const [page, setPage] = useState(0)
  const { answer, table, execution_duration_ms } = result

  const totalPages = table ? Math.ceil(table.rows.length / PAGE_SIZE) : 0
  const pageRows = table ? table.rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE) : []

  return (
    <div className="sheet-result-card">
      <div className="sheet-result-header">
        <span className="sheet-result-badge">Sheet Query</span>
        <span className="sheet-result-meta">{execution_duration_ms} ms</span>
        {table && (
          <span className="sheet-result-meta">{table.rows.length} row{table.rows.length !== 1 ? 's' : ''}</span>
        )}
      </div>

      <div className="sheet-result-answer">
        {answer}
      </div>

      {table && table.columns.length > 0 && (
        <div className="sheet-table-wrapper">
          <table className="sheet-result-table">
            <thead>
              <tr>
                {table.columns.map((col) => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row, rowIdx) => (
                <tr key={rowIdx}>
                  {table.columns.map((col, colIdx) => {
                    const cell = row[colIdx] ?? ''
                    return (
                      <td key={`${col}-${colIdx}`}>
                        {cell === '' || cell === 'None' ? <span className="sheet-null">—</span> : cell}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="sheet-pagination">
              <button
                type="button"
                className="sheet-page-btn"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
              >
                ← Prev
              </button>
              <span className="sheet-page-label">
                Page {page + 1} of {totalPages}
              </span>
              <button
                type="button"
                className="sheet-page-btn"
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page === totalPages - 1}
              >
                Next →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
