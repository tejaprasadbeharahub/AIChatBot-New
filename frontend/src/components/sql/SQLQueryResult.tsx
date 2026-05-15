import { useState } from 'react'
import type { SQLQueryExecution } from '../../types/nl_sql'

type Props = {
  execution: SQLQueryExecution
}

const PAGE_SIZE = 25

export function SQLQueryResult({ execution }: Props) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [page, setPage] = useState(0)

  const { generated_sql, sql_explanation, execution_status, error_message, returned_columns, result_rows, row_count, execution_duration_ms } = execution

  const totalPages = Math.ceil((result_rows?.length ?? 0) / PAGE_SIZE)
  const pageRows = (result_rows ?? []).slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  const statusBadge =
    execution_status === 'succeeded'
      ? 'sql-badge sql-badge--success'
      : execution_status === 'failed'
        ? 'sql-badge sql-badge--error'
        : 'sql-badge sql-badge--pending'

  const statusLabel =
    execution_status === 'succeeded' ? 'Success' : execution_status === 'failed' ? 'Failed' : 'Pending'

  return (
    <div className="sql-result-card">
      <div className="sql-result-header">
        <span className={statusBadge}>{statusLabel}</span>
        {execution_duration_ms !== null && execution_duration_ms !== undefined && (
          <span className="sql-meta">{execution_duration_ms} ms</span>
        )}
        {row_count !== null && row_count !== undefined && (
          <span className="sql-meta">{row_count} row{row_count !== 1 ? 's' : ''}</span>
        )}
      </div>

      <div className="sql-query-block">
        <button
          type="button"
          className="sql-expand-toggle"
          onClick={() => setIsExpanded((v) => !v)}
          aria-expanded={isExpanded}
        >
          {isExpanded ? '▾' : '▸'} Generated SQL
        </button>
        {isExpanded && (
          <pre className="sql-code-block">{generated_sql}</pre>
        )}
        {sql_explanation && (
          <p className="sql-explanation">{sql_explanation}</p>
        )}
      </div>

      {execution_status === 'failed' && error_message && (
        <div className="sql-error-block">
          <span className="sql-error-label">Error:</span> {error_message}
        </div>
      )}

      {execution_status === 'succeeded' && returned_columns.length > 0 && (
        <div className="sql-table-wrapper">
          <table className="sql-result-table">
            <thead>
              <tr>
                {returned_columns.map((col) => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row, rowIdx) => (
                <tr key={rowIdx}>
                  {returned_columns.map((col) => (
                    <td key={col}>
                      {row[col] === null || row[col] === undefined
                        ? <span className="sql-null">NULL</span>
                        : String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="sql-pagination">
              <button
                type="button"
                className="sql-page-btn"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
              >
                ← Prev
              </button>
              <span className="sql-page-label">
                Page {page + 1} of {totalPages}
              </span>
              <button
                type="button"
                className="sql-page-btn"
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page === totalPages - 1}
              >
                Next →
              </button>
            </div>
          )}
        </div>
      )}

      {execution_status === 'succeeded' && returned_columns.length === 0 && (
        <p className="sql-empty-state">Query executed with no results.</p>
      )}
    </div>
  )
}
