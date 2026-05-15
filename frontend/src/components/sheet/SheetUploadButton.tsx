import { useRef } from 'react'

interface SheetUploadButtonProps {
  disabled?: boolean
  onSelect: (file: File) => void
}

export function SheetUploadButton({ disabled = false, onSelect }: SheetUploadButtonProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)

  function handleClick() {
    if (!disabled) inputRef.current?.click()
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
        className="composer-send sheet-upload-btn"
        onClick={handleClick}
        disabled={disabled}
        title="Upload CSV or Excel file"
      >
        Upload CSV/Excel
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={handleChange}
        style={{ display: 'none' }}
      />
    </>
  )
}
