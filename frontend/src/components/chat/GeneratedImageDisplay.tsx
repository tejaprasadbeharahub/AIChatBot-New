import { useEffect, useState } from 'react'
import type { GeneratedImage } from '../../types/image_generation'
import { API_BASE_URL } from '../../lib/api'
import { getStoredToken } from '../../api/auth'

interface GeneratedImageDisplayProps {
  image: GeneratedImage
  onExpand?: () => void
  onDelete?: (imageId: string) => void
}

function getFullImageUrl(imageUrl: string | null): string | null {
  if (!imageUrl) return null
  
  // If it's already a full URL, return as-is
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    return imageUrl
  }
  
  // If it's a relative API path, prepend the API base URL
  if (imageUrl.startsWith('/api/')) {
    return `${API_BASE_URL}${imageUrl}`
  }
  
  return imageUrl
}

async function fetchImageAsDataUrl(imageUrl: string): Promise<string | null> {
  if (!imageUrl) return null
  
  const fullUrl = getFullImageUrl(imageUrl)
  if (!fullUrl) return null
  
  try {
    const token = getStoredToken()
    const response = await fetch(fullUrl, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    
    if (!response.ok) {
      console.error(`Failed to fetch image: ${response.status}`)
      return null
    }
    
    const blob = await response.blob()
    return URL.createObjectURL(blob)
  } catch (err) {
    console.error('Failed to fetch image:', err)
    return null
  }
}

export function GeneratedImageDisplay({ image, onExpand, onDelete }: GeneratedImageDisplayProps) {
  const [dataUrl, setDataUrl] = useState<string | null>(null)

  useEffect(() => {
    if (image.status === 'completed' && image.image_url && !dataUrl) {
      fetchImageAsDataUrl(image.image_url).then(setDataUrl)
    }
  }, [image.status, image.image_url, dataUrl])

  if (image.status === 'pending') {
    return (
      <div className="generated-image-container loading">
        <div className="image-loading">
          <div className="spinner" />
          <p>Generating image for: "{image.prompt}"</p>
        </div>
      </div>
    )
  }

  if (image.status === 'failed') {
    return (
      <div className="generated-image-container error">
        <div className="image-error">
          <p className="error-icon">⚠️</p>
          <p className="error-title">Image generation failed</p>
          <p className="error-prompt">Prompt: "{image.prompt}"</p>
          {image.error_message && <p className="error-message">{image.error_message}</p>}
          {onDelete && (
            <button
              className="delete-button"
              onClick={() => onDelete(image.id)}
              title="Delete this failed attempt"
            >
              Remove
            </button>
          )}
        </div>
      </div>
    )
  }

  if (image.status === 'completed' && image.image_url) {
    return (
      <div className="generated-image-container">
        <div className="image-wrapper">
          {dataUrl ? (
            <img
              src={dataUrl}
              alt={image.prompt}
              className="generated-image"
              onClick={onExpand}
              title="Click to expand"
            />
          ) : (
            <div className="image-loading">
              <div className="spinner" />
              <p>Loading image...</p>
            </div>
          )}
          <div className="image-actions">
            {onExpand && (
              <button className="action-button expand" onClick={onExpand} title="Expand image">
                ↗
              </button>
            )}
            {onDelete && (
              <button
                className="action-button delete"
                onClick={() => onDelete(image.id)}
                title="Delete image"
              >
                🗑
              </button>
            )}
          </div>
        </div>
        <p className="image-prompt">
          <span className="label">Prompt:</span> {image.prompt}
        </p>
      </div>
    )
  }

  return null
}
