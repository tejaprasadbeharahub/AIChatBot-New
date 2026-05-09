import { useRef } from 'react'

interface PdfUploadButtonProps {
  disabled?: boolean
  onSelect: (file: File) => void
}

export function PdfUploadButton({ disabled = false, onSelect }: PdfUploadButtonProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)

  function handleClick() {
    if (!disabled) {
      inputRef.current?.click()
    }
  }

  function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (file) {
      onSelect(file)
      event.target.value = ''
    }
  }

  return (
    <>
      <button
        type="button"
        className="composer-send pdf-upload-btn"
        onClick={handleClick}
        disabled={disabled}
      >
        Upload PDF
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        onChange={handleChange}
        style={{ display: 'none' }}
      />
    </>
  )
}
