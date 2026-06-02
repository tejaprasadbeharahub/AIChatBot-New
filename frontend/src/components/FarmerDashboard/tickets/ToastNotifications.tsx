import React, { useEffect } from 'react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error';
  text: string;
}

interface Props {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

interface ToastItemProps {
  toast: ToastMessage;
  onDismiss: (id: string) => void;
}

const TOAST_DURATION = 5000; // 5 seconds

const ToastItem: React.FC<ToastItemProps> = ({ toast, onDismiss }) => {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(toast.id), TOAST_DURATION);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  const isSuccess = toast.type === 'success';

  return (
    <div
      className={`
        min-w-96 animate-in slide-in-from-right-4 fade-in-80 rounded-2xl 
        border-2 px-5 py-4 shadow-2xl backdrop-blur-sm
        ${
          isSuccess
            ? 'border-emerald-300 bg-gradient-to-br from-emerald-50 to-emerald-100/80 text-emerald-900'
            : 'border-red-300 bg-gradient-to-br from-red-50 to-red-100/80 text-red-900'
        }
      `}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          {/* Icon */}
          <div className="mt-0.5 flex-shrink-0">
            {isSuccess ? (
              <div className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-200">
                <span className="text-lg">✓</span>
              </div>
            ) : (
              <div className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-red-200">
                <span className="text-lg">!</span>
              </div>
            )}
          </div>
          {/* Message */}
          <div className="flex-1">
            <p className="font-semibold text-sm leading-snug">{toast.text}</p>
          </div>
        </div>
        {/* Close Button */}
        <button
          type="button"
          onClick={() => onDismiss(toast.id)}
          className={`
            flex-shrink-0 p-1 rounded-lg transition-all hover:opacity-70
            ${isSuccess ? 'hover:bg-emerald-200/60' : 'hover:bg-red-200/60'}
          `}
          aria-label="Close notification"
        >
          <span className="text-xl leading-none">×</span>
        </button>
      </div>

      {/* Progress Bar */}
      <div className={`mt-3 h-1.5 rounded-full overflow-hidden ${isSuccess ? 'bg-emerald-200/40' : 'bg-red-200/40'}`}>
        <div
          className={`h-full rounded-full animate-pulse ${isSuccess ? 'bg-emerald-500' : 'bg-red-500'}`}
          style={{
            animation: `shrink ${TOAST_DURATION}ms linear forwards`,
          }}
        />
      </div>
    </div>
  );
};

export const ToastNotifications: React.FC<Props> = ({ toasts, onDismiss }) => (
  <>
    <style>{`
      @keyframes shrink {
        from {
          width: 100%;
        }
        to {
          width: 0%;
        }
      }
    `}</style>
    <div className="fixed right-4 top-4 z-50 flex flex-col gap-3 pointer-events-auto">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  </>
);
