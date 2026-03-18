/**
 * @file Badge.tsx
 * Etiqueta de estado de tipo pill (pastilla redondeada) para indicar categorías,
 * roles, estados o cualquier información de clasificación breve.
 * Compatible con modo oscuro mediante variantes Tailwind `dark:`.
 */

import type { ReactNode } from 'react';

/**
 * Props del componente Badge.
 *
 * @property color     - Nombre del color semántico del badge. Debe coincidir con
 *                       una clave de `colorMap`; si no coincide, se usa `'gray'`.
 *                       Por defecto `'gray'`.
 * @property children  - Texto o contenido interno del badge.
 * @property className - Clases de Tailwind adicionales para ajustes puntuales.
 */
interface BadgeProps {
  color?: string;
  children: ReactNode;
  className?: string;
}

// ─── Paleta de colores ────────────────────────────────────────────────────────

/**
 * Mapa de colores semánticos a clases de Tailwind, con soporte para modo oscuro.
 * Si se pasa un `color` que no existe en este mapa, el badge fallback a `gray`.
 */
const colorMap: Record<string, string> = {
  green: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  red: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  yellow: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  gray: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
};

// ─── Componente ───────────────────────────────────────────────────────────────

/**
 * Badge de estado pill.
 * Usa `colorMap[color] || colorMap.gray` como fallback seguro para colores no definidos.
 */
export default function Badge({ color = 'gray', children, className = '' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorMap[color] || colorMap.gray} ${className}`}>
      {children}
    </span>
  );
}
