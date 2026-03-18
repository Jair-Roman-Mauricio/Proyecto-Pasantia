/**
 * @file Modal.tsx
 * Diálogo modal accesible y configurable en tamaño. Bloquea el scroll del body
 * mientras está abierto y se cierra al hacer clic en el overlay semitransparente
 * o en el botón "X" del encabezado.
 */

import { useEffect, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';

// ─── Tipos ────────────────────────────────────────────────────────────────────

/**
 * Props del componente Modal.
 *
 * @property isOpen   - Controla la visibilidad del modal; cuando es `false` no se renderiza nada.
 * @property onClose  - Callback invocado al cerrar el modal (clic en overlay o en botón X).
 * @property title    - Título opcional que aparece en la cabecera del panel. Si se omite,
 *                      la cabecera no se renderiza.
 * @property children - Contenido del cuerpo del modal.
 * @property size     - Anchura máxima del panel. Por defecto `'md'`.
 */
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// ─── Mapas de estilos ─────────────────────────────────────────────────────────

/** Clases de Tailwind para la anchura máxima según tamaño seleccionado. */
const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

// ─── Componente ───────────────────────────────────────────────────────────────

/**
 * Modal genérico de la aplicación.
 * Usa un ref sobre el overlay para diferenciar clics en el fondo vs. en el panel,
 * evitando que el cierre se dispare al interactuar con el contenido interno.
 */
export default function Modal({ isOpen, onClose, title, children, size = 'md' }: ModalProps) {
  // Referencia al div de overlay para detectar clics directamente sobre él
  const overlayRef = useRef<HTMLDivElement>(null);

  // Bloquea el scroll del documento mientras el modal está abierto
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    // Cleanup: restaura el scroll si el componente se desmonta con el modal abierto
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      // Solo cierra si el clic fue sobre el overlay, no sobre el panel del modal
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div className={`${sizeClasses[size]} w-full mx-4 bg-[var(--card-bg)] rounded-xl shadow-2xl border border-[var(--border-color)] animate-in fade-in`}>
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-color)]">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">{title}</h2>
            <button onClick={onClose} className="p-1 rounded-lg hover:bg-[var(--hover-bg)] text-[var(--text-muted)] cursor-pointer">
              <X size={20} />
            </button>
          </div>
        )}
        <div className="px-6 py-4">{children}</div>
      </div>
    </div>
  );
}
