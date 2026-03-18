/**
 * @file AppLayout.tsx
 * Layout principal de la aplicación autenticada. Compone el Sidebar, el Header
 * y el área de contenido principal donde React Router monta las rutas hijas
 * mediante <Outlet>. Envuelve todo con SidebarProvider para que ambos componentes
 * compartan el estado del panel de navegación.
 *
 * Estructura visual:
 *   ┌─────────────┬───────────────────────────┐
 *   │   Sidebar   │  Header                   │
 *   │             ├───────────────────────────┤
 *   │             │  <Outlet /> (página activa)│
 *   └─────────────┴───────────────────────────┘
 */

import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import { SidebarProvider, useSidebar } from '../../context/SidebarContext';

/**
 * Componente interno que accede al contexto del sidebar.
 * Se separa de `AppLayout` para poder consumir `useSidebar`,
 * que requiere estar dentro del árbol de `SidebarProvider`.
 */
function AppLayoutInner() {
  const { mobileOpen, closeMobile } = useSidebar();

  return (
    <div className="flex min-h-screen">
      {/* Overlay semitransparente que cierra el sidebar al tocar fuera en móvil */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={closeMobile}
        />
      )}
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 p-4 md:p-6 overflow-auto bg-[var(--bg-secondary)]">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

/**
 * Layout raíz de la aplicación autenticada.
 * Provee el contexto del sidebar a todos los componentes del layout.
 */
export default function AppLayout() {
  return (
    <SidebarProvider>
      <AppLayoutInner />
    </SidebarProvider>
  );
}
