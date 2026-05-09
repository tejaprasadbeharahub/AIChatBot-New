import type { PdfDocument } from '../../types/pdf_rag'

interface PdfDocumentStatusListProps {
  items: PdfDocument[]
  isUploading?: boolean
}

function statusLabel(status: PdfDocument['status']): string {
  if (status === 'completed') return 'Indexed'
  if (status === 'processing') return 'Processing'
  if (status === 'failed') return 'Failed'
  return 'Pending'
}

function statusClass(status: PdfDocument['status']): string {
  if (status === 'completed') return 'pdf-doc-status completed'
  if (status === 'processing') return 'pdf-doc-status processing'
  if (status === 'failed') return 'pdf-doc-status failed'
  return 'pdf-doc-status pending'
}

export function PdfDocumentStatusList({ items, isUploading = false }: PdfDocumentStatusListProps) {
  if (items.length === 0 && !isUploading) {
    return null
  }

  return (
    <section className="pdf-doc-list" aria-live="polite">
      <div className="pdf-doc-list-header">
        <p className="pdf-doc-title">PDF Knowledge Base</p>
        {isUploading ? <span className="pdf-doc-uploading">Uploading...</span> : null}
      </div>
      <div className="pdf-doc-items">
        {items.map((item) => (
          <article key={item.id} className="pdf-doc-card">
            <div className="pdf-doc-main">
              <p className="pdf-doc-name">{item.file_name}</p>
              <p className="pdf-doc-meta">
                {item.chunk_count ? `${item.chunk_count} chunks` : 'Not indexed yet'}
              </p>
              {item.error_message ? <p className="pdf-doc-error">{item.error_message}</p> : null}
            </div>
            <div className={statusClass(item.status)}>{statusLabel(item.status)}</div>
          </article>
        ))}
      </div>
    </section>
  )
}
