import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((message, type = 'info', duration = 3500) => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    setToasts((prev) => [...prev, { id, message, type }]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
    return id;
  }, [removeToast]);

  return (
    <ToastContext.Provider value={{ showToast, removeToast }}>
      {children}
      {/* Toast Notification Container */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none select-none">
        {toasts.map((toast) => {
          let icon = <Info className="w-4 h-4 text-sky-400 shrink-0" />;
          let borderClass = 'border-sky-500/40';

          if (toast.type === 'success') {
            icon = <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />;
            borderClass = 'border-emerald-500/40';
          } else if (toast.type === 'error') {
            icon = <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />;
            borderClass = 'border-rose-500/40';
          } else if (toast.type === 'warning') {
            icon = <AlertTriangle className="w-4 h-4 text-[#F0F0F0] shrink-0" />;
            borderClass = 'border-[#F0F0F0]/40';
          }

          return (
            <div
              key={toast.id}
              className={`pointer-events-auto flex items-center justify-between gap-3 p-3 bg-[#2A2A2A] border ${borderClass} rounded-xl shadow-2xl text-xs text-[#ECECEC] animate-slide-up transition-all`}
            >
              <div className="flex items-center gap-2.5 truncate">
                {icon}
                <span className="truncate">{toast.message}</span>
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-[#A1A1A1] hover:text-[#ECECEC] p-1 rounded-md transition"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    return {
      showToast: (msg) => console.log('Toast:', msg),
      removeToast: () => {},
    };
  }
  return ctx;
}
