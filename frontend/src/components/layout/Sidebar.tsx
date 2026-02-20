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
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useSidebar } from '../../context/SidebarContext';

const adminOptions = [
  { id: 'map', label: 'Mapa de Linea 1', icon: Map },
  { id: 'notifications', label: 'Notificaciones', icon: Bell },
  { id: 'requests', label: 'Solicitudes', icon: FileText },
  { id: 'reports', label: 'Reportes', icon: BarChart3 },
  { id: 'permissions', label: 'Permisos', icon: Shield },
  { id: 'users', label: 'Gestion de Usuarios', icon: Users },
  { id: 'backup', label: 'Backup', icon: Database },
  { id: 'audit', label: 'Auditoria', icon: ClipboardList },
];

const allOpersacOptions = [
  { id: 'map', label: 'Mapa de Linea 1', icon: Map, permission: 'view_stations' },
  { id: 'requests', label: 'Mis Solicitudes', icon: FileText, permission: 'send_requests' },
  { id: 'reports', label: 'Reportes', icon: BarChart3, permission: 'view_reports' },
];

export default function Sidebar() {
  const { user, hasPermission } = useAuth();
  const { activeOption, setActiveOption, viewMode, toggleViewMode } = useSidebar();
  const navigate = useNavigate();

  const opersacOptions = allOpersacOptions.filter((opt) => hasPermission(opt.permission));
  const options = viewMode === 'admin' && user?.role === 'admin' ? adminOptions : opersacOptions;

  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 flex flex-col overflow-y-auto" style={{ backgroundColor: 'var(--sidebar-bg)', color: 'var(--sidebar-text)' }}>
      {/* Logo */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center text-white font-bold text-lg">
            L1
          </div>
          <div>
            <h1 className="text-sm font-bold">Linea 1 del Metro</h1>
            <p className="text-xs text-gray-400">Gestion Energetica</p>
          </div>
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
