/**
 * @file Sidebar.tsx
 * Panel de navegación lateral de la aplicación. Muestra un menú diferente según
 * el rol del usuario autenticado y el modo de vista activo (admin / opersac).
 *
 * Comportamiento responsive:
 *   - En desktop (md+): posición estática, siempre visible.
 *   - En móvil: drawer deslizable controlado por `mobileOpen` del SidebarContext.
 *
 * Los administradores pueden cambiar al "modo opersac" para ver la interfaz
 * tal como la vería un operador SAC, sin abandonar su sesión.
 */

import {
  Map,
  Bell,
  FileText,
  BarChart3,
  Shield,
  Users,
  Database,
  ClipboardList,
  Eye,
  X,
  BookOpen,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useSidebar } from '../../context/SidebarContext';
import { useEffect } from 'react';

/**
 * Opciones del menú para usuarios con rol 'admin'.
 * Incluye todas las secciones del sistema sin restricciones de permiso.
 */
const adminOptions = [
  { id: 'map', label: 'Mapa de Linea 1', icon: Map },
  { id: 'notifications', label: 'Notificaciones', icon: Bell },
  { id: 'requests', label: 'Solicitudes', icon: FileText },
  { id: 'reports', label: 'Reportes', icon: BarChart3 },
  { id: 'permissions', label: 'Permisos', icon: Shield },
  { id: 'users', label: 'Gestion de Usuarios', icon: Users },
  { id: 'backup', label: 'Backup', icon: Database },
  { id: 'audit', label: 'Auditoria', icon: ClipboardList },
  { id: 'guide', label: 'Guia de Uso', icon: BookOpen },
];

/**
 * Opciones del menú para usuarios con rol 'opersac'.
 * Cada opción con `permission` solo se muestra si el usuario tiene ese permiso habilitado.
 * Se filtra en tiempo de ejecución mediante `hasPermission` del contexto de autenticación.
 */
const allOpersacOptions = [
  { id: 'map', label: 'Mapa de Linea 1', icon: Map, permission: 'view_stations' },
  { id: 'requests', label: 'Mis Solicitudes', icon: FileText, permission: 'send_requests' },
  { id: 'reports', label: 'Reportes', icon: BarChart3, permission: 'view_reports' },
  { id: 'guide', label: 'Guia de Uso', icon: BookOpen },
];

/**
 * Barra lateral de navegación principal de la aplicación.
 * En mobile se muestra/oculta con una transición lateral; en desktop es estática.
 * El contenido del menú varía según el rol del usuario y el modo de vista activo
 * (los admins pueden alternar entre vista admin y vista opersac).
 */
export default function Sidebar() {
  const { user, hasPermission } = useAuth();
  const { activeOption, setActiveOption, viewMode, toggleViewMode, mobileOpen, closeMobile } = useSidebar();
  const navigate = useNavigate();

  // Filtra las opciones de opersac según los permisos asignados al usuario actual
  const opersacOptions = allOpersacOptions.filter((opt) => !opt.permission || hasPermission(opt.permission));
  // Selecciona el conjunto de opciones a mostrar según el rol y el modo de vista
  const options = viewMode === 'admin' && user?.role === 'admin' ? adminOptions : opersacOptions;

  // Cierra el sidebar al cambiar de vista (solo móvil)
  useEffect(() => { closeMobile(); }, [activeOption]);

  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-40 w-64 flex flex-col overflow-y-auto transition-transform duration-300
        md:static md:translate-x-0 md:shrink-0 md:h-screen md:sticky md:top-0
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
      `}
      style={{ backgroundColor: 'var(--sidebar-bg)', color: 'var(--sidebar-text)' }}
    >
      {/* Logo */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center text-white font-bold text-lg shrink-0">
            L1
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-bold truncate">Linea 1 del Metro</h1>
            <p className="text-xs text-gray-400">Gestion Energetica</p>
          </div>
          {/* Close button (mobile only) */}
          <button
            onClick={closeMobile}
            className="md:hidden p-1 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 transition-colors cursor-pointer"
            aria-label="Cerrar menú"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        {options.map((option) => {
          const Icon = option.icon;
          const isActive = activeOption === option.id;
          return (
            <button
              key={option.id}
              onClick={() => { setActiveOption(option.id); navigate('/'); }}
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors cursor-pointer ${
                isActive
                  ? 'bg-primary-600/20 text-primary-400 border-l-3 border-primary-500'
                  : 'text-gray-300 hover:bg-gray-800 border-l-3 border-transparent'
              }`}
            >
              <Icon size={18} />
              <span>{option.label}</span>
            </button>
          );
        })}
      </nav>

      {/* View as Opersac toggle (admin only) */}
      {user?.role === 'admin' && (
        <div className="p-4 border-t border-gray-700">
          <button
            onClick={toggleViewMode}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors cursor-pointer hover:bg-gray-800 text-gray-300"
          >
            <Eye size={18} />
            <span>{viewMode === 'admin' ? 'Ver como Opersac' : 'Volver a Admin'}</span>
          </button>
          {viewMode === 'opersac' && (
            <div className="mt-2 px-3 py-1.5 bg-yellow-500/20 text-yellow-300 text-xs rounded-lg text-center">
              Modo Opersac activo
            </div>
          )}
        </div>
      )}
    </aside>
  );
}
