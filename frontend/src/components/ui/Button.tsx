/**
 * @file Button.tsx
 * Componente de botón reutilizable con soporte para múltiples variantes visuales
 * y tamaños. Extiende todos los atributos nativos del elemento <button> de HTML,
 * por lo que acepta `onClick`, `disabled`, `type`, etc.
 */

import type { ButtonHTMLAttributes, ReactNode } from 'react';

// ─── Tipos ───────────────────────────────────────────────────────────────────

/**
 * Props del componente Button.
 *
 * @property variant  - Estilo visual del botón. Por defecto `'primary'`.
 * @property size     - Tamaño del botón que ajusta padding y fuente. Por defecto `'md'`.
 * @property children - Contenido interior del botón (texto, iconos, etc.).
 */
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: ReactNode;
}

// ─── Mapas de estilos ─────────────────────────────────────────────────────────

/** Clases de Tailwind para cada variante visual del botón. */
const variants = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 border-transparent',
  secondary: 'bg-transparent text-[var(--text-primary)] border-[var(--border-color)] hover:bg-[var(--hover-bg)]',
  danger: 'bg-red-600 text-white hover:bg-red-700 border-transparent',
  ghost: 'bg-transparent text-[var(--text-secondary)] border-transparent hover:bg-[var(--hover-bg)]',
};

/** Clases de Tailwind para cada tamaño del botón. */
const sizes = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

// ─── Componente ───────────────────────────────────────────────────────────────

/**
 * Botón genérico de la aplicación.
 * Combina las clases base con la variante y el tamaño seleccionados,
 * y deshabilita la interacción visualmente cuando `disabled` es `true`.
 */
export default function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center font-medium rounded-lg border transition-colors duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
