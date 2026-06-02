import React from 'react';

interface Props {
  disabled?: boolean;
  isLoading?: boolean;
  onClick: () => void;
}

export const StartProcessingButton: React.FC<Props> = ({ disabled, isLoading, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled || isLoading}
    className="inline-flex items-center justify-center gap-2 rounded-lg bg-sky-600 px-3 py-2 text-xs font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-sky-700 hover:shadow disabled:cursor-not-allowed disabled:opacity-60"
  >
    {isLoading ? <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" /> : <span>▶</span>}
    Start Processing
  </button>
);
