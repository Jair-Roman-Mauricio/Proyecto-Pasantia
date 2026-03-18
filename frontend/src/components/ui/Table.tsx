/**
 * @file Table.tsx
 * Tabla de datos genérica y totalmente tipada. Acepta una definición de columnas
 * y un arreglo de elementos de cualquier tipo `T`, y renderiza cabeceras y filas
 * de forma dinámica. Soporta celdas personalizadas, filas clickeables y
 * clases condicionales por fila.
 */

import type { ReactNode } from 'react';

// ─── Tipos ────────────────────────────────────────────────────────────────────

/**
 * Definición de una columna de la tabla.
 *
 * @template T         - Tipo del elemento de datos de cada fila.
 * @property key       - Clave que identifica la columna; también se usa como fallback
 *                       para leer el valor del objeto cuando `render` no se define.
 * @property header    - Texto del encabezado de la columna.
 * @property render    - Renderizador personalizado de la celda. Si se omite, se muestra
 *                       el valor de `item[key]` convertido a string.
 * @property className - Clases de Tailwind adicionales para la celda (th y td).
 */
interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => ReactNode;
  className?: string;
}

/**
 * Props del componente Table.
 *
 * @template T             - Tipo de los elementos del arreglo de datos.
 * @property columns       - Configuración de las columnas a renderizar.
 * @property data          - Arreglo de elementos que representan las filas.
 * @property rowKey        - Función que extrae un identificador único de cada elemento
 *                           para la prop `key` de React.
 * @property rowClassName  - Función opcional que devuelve clases adicionales por fila,
 *                           útil para destacar filas según su estado.
 * @property onRowClick    - Callback invocado al hacer clic en una fila. Si se define,
 *                           la fila adopta cursor de puntero.
 * @property emptyMessage  - Mensaje a mostrar cuando `data` está vacío.
 *                           Por defecto `'No hay datos disponibles'`.
 */
interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  rowKey: (item: T) => string | number;
  rowClassName?: (item: T) => string;
  onRowClick?: (item: T) => void;
  emptyMessage?: string;
}

// ─── Componente ───────────────────────────────────────────────────────────────

/**
 * Tabla de datos genérica con scroll horizontal en viewports pequeños.
 * El casting `item as Record<string, unknown>` permite acceder al valor por clave
 * de forma segura sin requerir índices en el tipo genérico `T`.
 */
export default function Table<T>({
  columns,
  data,
  rowKey,
  rowClassName,
  onRowClick,
  emptyMessage = 'No hay datos disponibles',
}: TableProps<T>) {
  return (
    <div className="overflow-x-auto rounded-lg border border-[var(--border-color)]">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[var(--bg-secondary)]">
            {columns.map((col) => (
              <th key={col.key} className={`px-4 py-3 text-left font-medium text-[var(--text-secondary)] ${col.className || ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            // Fila vacía que ocupa todo el ancho cuando no hay datos
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-[var(--text-muted)]">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item) => (
              <tr
                key={rowKey(item)}
                className={`border-t border-[var(--border-color)] hover:bg-[var(--hover-bg)] transition-colors ${onRowClick ? 'cursor-pointer' : ''} ${rowClassName?.(item) || ''}`}
                onClick={() => onRowClick?.(item)}
              >
                {columns.map((col) => (
                  <td key={col.key} className={`px-4 py-3 ${col.className || ''}`}>
                    {/* Usa el renderizador personalizado si existe; si no, accede al valor por clave */}
                    {col.render ? col.render(item) : String((item as Record<string, unknown>)[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
