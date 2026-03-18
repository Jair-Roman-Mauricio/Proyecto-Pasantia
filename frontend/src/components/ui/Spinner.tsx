/**
 * @file Spinner.tsx
 * Indicador de carga circular animado. Se centra automáticamente dentro
 * de su contenedor. Se usa para estados de carga de página, secciones o acciones.
 */

/**
 * Props del componente Spinner.
 *
 * @property size - Tamaño del indicador. Por defecto `'md'`.
 *                  - `'sm'` → 16×16 px (componentes inline)
 *                  - `'md'` → 32×32 px (secciones)
 *                  - `'lg'` → 48×48 px (pantalla completa)
 */
export default function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  // El borde superior con color de acento y el resto en el color de borde base
  // crean el efecto de arco rotatorio característico del spinner.
  const sizeClasses = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' };
  return (
    <div className="flex items-center justify-center">
      <div className={`${sizeClasses[size]} border-2 border-[var(--border-color)] border-t-primary-500 rounded-full animate-spin`} />
    </div>
  );
}
