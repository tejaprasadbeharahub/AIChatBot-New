import { useState } from 'react'
import type { FormEvent } from 'react'

interface ImageGenerationPromptProps {
  onGenerateImage: (prompt: string) => void
  isLoading?: boolean
  disabled?: boolean
}

export function ImageGenerationPrompt({
  onGenerateImage,
  isLoading = false,
  disabled = false,
}: ImageGenerationPromptProps) {
  const [prompt, setPrompt] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (prompt.trim() && !isLoading && !disabled) {
      onGenerateImage(prompt.trim())
      setPrompt('')
      setIsExpanded(false)
    }
  }

  if (!isExpanded) {
    return (
      <button
        type="button"
        className="image-gen-toggle"
        onClick={() => setIsExpanded(true)}
        disabled={disabled || isLoading}
        title="Generate an AI image"
      >
        🖼️ Generate Image
      </button>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="image-generation-form">
      <div className="image-gen-input-wrapper">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the image you want to generate (e.g., 'A sunset over mountains, oil painting style')"
          className="image-gen-input"
          rows={3}
          disabled={isLoading || disabled}
          maxLength={2000}
        />
        <div className="char-count">
          {prompt.length}/2000
        </div>
      </div>

      <div className="image-gen-buttons">
        <button
          type="submit"
          className="generate-button"
          disabled={prompt.trim().length < 2 || isLoading || disabled}
        >
          {isLoading ? 'Generating...' : 'Generate Image'}
        </button>
        <button
          type="button"
          className="cancel-button"
          onClick={() => {
            setPrompt('')
            setIsExpanded(false)
          }}
          disabled={isLoading}
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
