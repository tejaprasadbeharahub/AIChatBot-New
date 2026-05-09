import { useRef, useState } from 'react'

interface AttachmentUploadProps {
  onAttachmentSelect: (file: File, fileType: string) => void
  disabled?: boolean
}

export function AttachmentUploadButton({ onAttachmentSelect, disabled = false }: AttachmentUploadProps) {
  const [isOpen, setIsOpen] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const attachmentTypes = [
    { id: 'image', label: '📷 Image', accepts: 'image/*' },
    { id: 'video', label: '🎬 Video', accepts: 'video/*' },
    { id: 'code', label: '💻 Code', accepts: '.py,.js,.ts,.java,.cpp,.txt,.json,.html,.css' },
    { id: 'document', label: '📄 Document', accepts: '.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv' },
    { id: 'formula', label: '∑ Formula', accepts: '.tex,.txt,.md' },
  ]

  const handleAttachmentTypeClick = (fileType: string, accepts: string) => {
    if (fileInputRef.current) {
      fileInputRef.current.accept = accepts
      fileInputRef.current.dataset.fileType = fileType
      fileInputRef.current.click()
    }
    setIsOpen(false)
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && fileInputRef.current?.dataset.fileType) {
      onAttachmentSelect(file, fileInputRef.current.dataset.fileType)
    }
  }

  return (
    <div className="attachment-upload-wrapper">
      <div className={`attachment-menu ${isOpen ? 'open' : ''}`}>
        <div className="attachment-menu-content">
          {attachmentTypes.map((type) => (
            <button
              key={type.id}
              type="button"
              className="attachment-menu-item"
              onClick={() => handleAttachmentTypeClick(type.id, type.accepts)}
              disabled={disabled}
            >
              {type.label}
            </button>
          ))}
        </div>
      </div>

      <button
        type="button"
        className="attachment-btn"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        title="Attach files"
      >
        📎
      </button>

      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileChange}
        style={{ display: 'none' }}
        aria-hidden="true"
      />
    </div>
  )
}
