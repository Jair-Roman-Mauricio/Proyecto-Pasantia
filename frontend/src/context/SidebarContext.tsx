/**
 * @file SidebarContext.tsx
 * Contexto global que gestiona el estado del panel de navegación lateral.
 * Expone el ítem activo, el modo de vista (admin/opersac), el estado colapsado
 * y la visibilidad del drawer en dispositivos móviles.
 *
 * Exporta:
 *   - `SidebarProvider` — proveedor que debe envolver el layout autenticado.
 *   - `useSidebar`       — hook de acceso al contexto.
 */

import { createContext, useContext, useState, type ReactNode } from 'react';

/**
 * Modo de vista del panel lateral.
 * - `'admin'`   - Muestra las opciones de navegación propias del perfil administrador.
 * - `'opersac'` - Muestra las opciones de navegación propias del perfil operador SAC.
 */
type ViewMode = 'admin' | 'opersac';

/**
 * Contrato del contexto del panel lateral (sidebar).
 *
 * @property activeOption    - Identificador de la opción de navegación actualmente seleccionada.
 * @property setActiveOption - Actualiza la opción activa al hacer clic en un ítem del menú.
 * @property viewMode        - Controla qué conjunto de opciones se muestra: vista admin o vista opersac.
 *                             Un administrador puede alternar entre ambas para simular la experiencia del operador.
 * @property toggleViewMode  - Alterna el `viewMode` entre `'admin'` y `'opersac'`.
 * @property isCollapsed     - Indica si el sidebar está colapsado (solo iconos) o expandido (iconos + texto).
 * @property setIsCollapsed  - Permite colapsar o expandir el sidebar programáticamente.
 * @property mobileOpen      - Indica si el sidebar está visible como drawer en pantallas pequeñas.
 * @property toggleMobile    - Abre o cierra el drawer móvil.
 * @property closeMobile     - Cierra el drawer móvil (útil al navegar a una nueva sección).
 */
interface SidebarContextType {
  activeOption: string;
  setActiveOption: (option: string) => void;
  viewMode: ViewMode;
  toggleViewMode: () => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  mobileOpen: boolean;
  toggleMobile: () => void;
  closeMobile: () => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

/**
 * Proveedor del contexto del sidebar. Debe envolver el componente `AppLayout`
 * (o cualquier subárbol que necesite acceder al estado de navegación lateral).
 */
export function SidebarProvider({ children }: { children: ReactNode }) {
  const [activeOption, setActiveOption] = useState('map');
  // viewMode determina qué conjunto de ítems de navegación se renderiza en el sidebar;
  // por defecto se inicia en 'admin' ya que el usuario autenticado suele ser administrador.
  const [viewMode, setViewMode] = useState<ViewMode>('admin');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  /**
   * Alterna el modo de vista entre `'admin'` y `'opersac'`.
   * Permite que un administrador explore la interfaz desde la perspectiva de un operador SAC.
   */
  const toggleViewMode = () => {
    setViewMode((prev) => (prev === 'admin' ? 'opersac' : 'admin'));
  };

  const toggleMobile = () => setMobileOpen((prev) => !prev);
  const closeMobile = () => setMobileOpen(false);

  return (
    <SidebarContext.Provider
        value={{ activeOption, setActiveOption, viewMode, toggleViewMode, isCollapsed, setIsCollapsed, mobileOpen, toggleMobile, closeMobile }}
      >
      {children}
    </SidebarContext.Provider>
  );
}

/**
 * Hook para consumir el contexto del panel lateral desde cualquier componente hijo de `SidebarProvider`.
 *
 * @throws {Error} Si se utiliza fuera del árbol de `SidebarProvider`.
 * @returns El valor completo del contexto del sidebar (`SidebarContextType`).
 *
 * @example
 * const { activeOption, setActiveOption, viewMode } = useSidebar();
 */
export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) throw new Error('useSidebar must be used within SidebarProvider');
  return context;
}
