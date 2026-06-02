import React from 'react';

interface Props {
  visible: boolean;
  message?: string;
}

export const LoadingOverlay: React.FC<Props> = ({ visible, message }) => {
  if (!visible) return null;
  return (
    <div className="absolute inset-0 z-20 flex items-center justify-center rounded-2xl bg-white/70 backdrop-blur-sm">
      <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-sky-600 border-t-transparent" />
        <span className="text-sm font-medium text-slate-700">{message || 'Working...'}</span>
      </div>
    </div>
  );
};
