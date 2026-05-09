import { useEffect, useState } from 'react'

import { API_BASE_URL } from '../../lib/api'
import { getStoredToken } from '../../api/auth'
import type { Attachment } from '../../types/chat'

interface AttachmentPreviewProps {
  attachment: Attachment
  onDownload?: (attachmentId: string) => void
}

export function AttachmentPreview({ attachment, onDownload }: AttachmentPreviewProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    let objectUrl: string | null = null

    async function loadPreview() {
      if (attachment.file_type !== 'image' && attachment.file_type !== 'video') {
        setPreviewUrl(null)
        return
      }

      const token = getStoredToken()
      if (!token) {
        setPreviewUrl(null)
        return
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/attachments/download/${attachment.id}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!response.ok) {
          setPreviewUrl(null)
          return
        }

        const blob = await response.blob()
        objectUrl = URL.createObjectURL(blob)
        if (active) {
          setPreviewUrl(objectUrl)
        }
      } catch {
        if (active) {
          setPreviewUrl(null)
        }
      }
    }

    void loadPreview()

    return () => {
      active = false
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [attachment.id, attachment.file_type])

  const handleDownloadClick = () => {
    onDownload?.(attachment.id)
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const getAttachmentIcon = (fileType: string): string => {
    switch (fileType) {
      case 'image':
        return '🖼️'
      case 'video':
        return '🎬'
      case 'code':
        return '💻'
      case 'formula':
        return '∑'
      case 'document':
        return '📄'
      default:
        return '📎'
    }
  }

  return (
    <div className="attachment-preview">
      <div className="attachment-preview-content">
        {attachment.file_type === 'image' && (
          previewUrl ? (
            <img
              src={previewUrl}
              alt={attachment.file_name}
              className="attachment-image"
            />
          ) : (
            <div className="attachment-file-info">
              <div className="attachment-file-icon">🖼️</div>
              <div className="attachment-file-details">
                <p className="attachment-file-name">{attachment.file_name}</p>
                <p className="attachment-file-meta">Preview unavailable. Use download.</p>
              </div>
            </div>
          )
        )}
        {attachment.file_type === 'video' && (
          previewUrl ? (
            <video
              controls
              className="attachment-video"
              src={previewUrl}
            />
          ) : (
            <div className="attachment-file-info">
              <div className="attachment-file-icon">🎬</div>
              <div className="attachment-file-details">
                <p className="attachment-file-name">{attachment.file_name}</p>
                <p className="attachment-file-meta">Preview unavailable. Use download.</p>
              </div>
            </div>
          )
        )}
        {(attachment.file_type === 'code' || attachment.file_type === 'formula' || attachment.file_type === 'document') && (
          <div className="attachment-file-info">
            <div className="attachment-file-icon">{getAttachmentIcon(attachment.file_type)}</div>
            <div className="attachment-file-details">
              <p className="attachment-file-name">{attachment.file_name}</p>
              <p className="attachment-file-meta">
                {attachment.file_type} • {formatFileSize(attachment.file_size)}
              </p>
            </div>
            <button
              type="button"
              className="attachment-download-btn"
              onClick={handleDownloadClick}
              title="Download file"
            >
              ⬇️
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
