import { useEffect } from 'react';
import { X, Bell, FileText, AlertTriangle } from 'lucide-react';

export interface ToastItem {
  id: string;
  message: string;
  type: 'info' | 'warning' | 'error';
  role: 'admin' | 'opersac';
  navigateTo: string;
}

interface LoginToastProps {
  toasts: ToastItem[];
  onClose: (id: string) => void;
  onClickToast: (toast: ToastItem) => void;
}

function SingleToast({
  toast,
  onClose,
  onClick,
}: {
  toast: ToastItem;
  onClose: () => void;
  onClick: () => void;
}) {
  useEffect(() => {
    const t = setTimeout(onClose, 6000);
    return () => clearTimeout(t);
  }, [onClose]);

  const borderColor =
    toast.type === 'error'
      ? 'border-red-500'
      : toast.type === 'warning'
      ? 'border-yellow-500'
      : 'border-primary-500';

  const Icon = toast.type === 'error' ? AlertTriangle : toast.role === 'admin' ? Bell : FileText;
  const iconColor =
    toast.type === 'error'
      ? 'text-red-400'
      : toast.type === 'warning'
      ? 'text-yellow-400'
      : 'text-primary-400';

  return (
    <div
      className={`flex items-start gap-3 w-80 rounded-xl border-l-4 ${borderColor} bg-[var(--card-bg)] shadow-xl px-4 py-3 cursor-pointer animate-slide-in`}
      onClick={onClick}
      role="button"
    >
      <Icon size={18} className={`shrink-0 mt-0.5 ${iconColor}`} />
      <p className="flex-1 text-sm text-[var(--text-primary)] leading-snug">{toast.message}</p>
      <button
        onClick={(e) => { e.stopPropagation(); onClose(); }}
        className="shrink-0 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export default function LoginToast({ toasts, onClose, onClickToast }: LoginToastProps) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3">
      {toasts.map((toast) => (
        <SingleToast
          key={toast.id}
          toast={toast}
          onClose={() => onClose(toast.id)}
          onClick={() => { onClickToast(toast); onClose(toast.id); }}
        />
      ))}
    </div>
  );
}
