/**
 * @file LoginToast.tsx
 * Sistema de notificaciones tipo toast que se presenta al iniciar sesión.
 * Cada toast muestra información relevante según el rol del usuario (alertas de
 * solicitudes pendientes para admins, actualizaciones de solicitudes para opersac).
 * Los toasts se auto-descartan a los 6 segundos y también pueden cerrarse manualmente
 * o al hacer clic en ellos para navegar a la sección correspondiente.
 */

import { useEffect } from 'react';
import { X, Bell, FileText, AlertTriangle } from 'lucide-react';

// ─── Tipos ────────────────────────────────────────────────────────────────────

/**
 * Estructura de un ítem de notificación toast.
 *
 * @property id         - Identificador único para gestión del ciclo de vida del toast.
 * @property message    - Texto descriptivo que se muestra al usuario.
 * @property type       - Nivel de severidad; determina el color del borde e ícono.
 * @property role       - Rol del usuario destinatario; influye en el ícono mostrado.
 * @property navigateTo - Identificador de sección a la que navega al hacer clic en el toast.
 */
export interface ToastItem {
  id: string;
  message: string;
  type: 'info' | 'warning' | 'error';
  role: 'admin' | 'opersac';
  navigateTo: string;
}

/**
 * Props del componente LoginToast (contenedor de múltiples toasts).
 *
 * @property toasts       - Lista de toasts activos a renderizar.
 * @property onClose      - Callback para eliminar un toast por su `id`.
 * @property onClickToast - Callback invocado al hacer clic en un toast;
 *                          recibe el item completo para permitir navegación.
 */
interface LoginToastProps {
  toasts: ToastItem[];
  onClose: (id: string) => void;
  onClickToast: (toast: ToastItem) => void;
}

// ─── Componente interno ───────────────────────────────────────────────────────

/**
 * Renderiza un único toast con auto-descarte temporizador.
 * El timer se reinicia si cambia `onClose` (estabilizar la referencia con useCallback
 * en el padre evita reinicios innecesarios).
 */
function SingleToast({
  toast,
  onClose,
  onClick,
}: {
  toast: ToastItem;
  onClose: () => void;
  onClick: () => void;
}) {
  // Auto-descarta el toast luego de 6 segundos; limpia el timeout al desmontar
  useEffect(() => {
    const t = setTimeout(onClose, 6000);
    return () => clearTimeout(t);
  }, [onClose]);

  // Color del borde izquierdo según severidad del toast
  const borderColor =
    toast.type === 'error'
      ? 'border-red-500'
      : toast.type === 'warning'
      ? 'border-yellow-500'
      : 'border-primary-500';

  // Ícono: error → triángulo de alerta; admin → campana; opersac → documento
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
      {/* stopPropagation evita que el clic en X también dispare onClick del toast */}
      <button
        onClick={(e) => { e.stopPropagation(); onClose(); }}
        className="shrink-0 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
      >
        <X size={14} />
      </button>
    </div>
  );
}

// ─── Componente público ───────────────────────────────────────────────────────

/**
 * Contenedor de toasts de login. Se posiciona en la esquina inferior derecha
 * de la pantalla y apila verticalmente los toasts activos.
 * No renderiza nada cuando la lista de toasts está vacía.
 */
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
