/**
 * @file Card.tsx
 * Contenedor visual genérico con fondo, borde redondeado y padding uniformes.
 * Cuando se provee `onClick`, aplica cursor de puntero y resalta el borde al
 * pasar el cursor, indicando que la tarjeta es interactiva.
 */

import type { ReactNode } from 'react';

/**
 * Props del componente Card.
 *
 * @property children   - Contenido que se renderiza dentro de la tarjeta.
 * @property className  - Clases de Tailwind adicionales para personalización puntual.
 * @property onClick    - Manejador de clic; si se provee, la tarjeta se comporta
 *                        como elemento interactivo (cursor pointer + hover destacado).
 */
interface CardProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

/**
 * Tarjeta de contenido genérica de la aplicación.
 * Aplica estilos condicionales de interactividad únicamente cuando se define `onClick`.
 */
export default function Card({ children, className = '', onClick }: CardProps) {
  return (
    <div
      // El borde resaltado en hover solo se activa cuando la tarjeta es clickeable
      className={`bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-4 transition-colors ${onClick ? 'cursor-pointer hover:border-primary-500' : ''} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
