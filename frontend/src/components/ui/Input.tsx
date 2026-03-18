/**
 * @file Input.tsx
 * Campo de texto controlado y reutilizable con soporte para etiqueta visible,
 * estado de error con mensaje descriptivo y reenvío de ref al elemento nativo.
 * Extiende todos los atributos estándar de <input> de HTML.
 */

import { forwardRef, type InputHTMLAttributes } from 'react';

/**
 * Props del componente Input.
 *
 * @property label - Etiqueta visible que se renderiza sobre el campo de texto.
 * @property error - Mensaje de error a mostrar bajo el campo; también activa
 *                   el borde rojo para indicar estado inválido.
 */
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

/**
 * Input con etiqueta y manejo de errores de validación.
 * Usa `forwardRef` para permitir que el padre acceda al elemento <input> nativo
 * (p. ej. para gestión de foco con `react-hook-form` o autofoco programático).
 */
const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div className="space-y-1">
        {label && (
          <label className="block text-sm font-medium text-[var(--text-secondary)]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors ${error ? 'border-red-500' : ''} ${className}`}
          {...props}
        />
        {error && <p className="text-xs text-red-500">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
export default Input;
