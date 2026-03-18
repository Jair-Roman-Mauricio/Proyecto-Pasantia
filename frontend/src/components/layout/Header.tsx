/**
 * @file Header.tsx
 * Barra de navegación superior de la aplicación autenticada.
 * Contiene:
 *   - Botón hamburguesa para abrir el sidebar en dispositivos móviles.
 *   - Selector de tema claro/oscuro.
 *   - Menú desplegable de usuario con avatar, nombre, rol y opción de cierre de sesión.
 *
 * El dropdown se cierra automáticamente al hacer clic fuera del componente
 * mediante un listener de `mousedown` a nivel de documento.
 */

import { useState, useRef, useEffect } from 'react';
import { Sun, Moon, LogOut, ChevronDown, Menu } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useSidebar } from '../../context/SidebarContext';
import Badge from '../ui/Badge';

/**
 * Header de la aplicación autenticada.
 * Gestiona el estado local del dropdown de usuario y registra un listener
 * global para cerrarlo al detectar clics fuera del área del componente.
 */
export default function Header() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { toggleMobile } = useSidebar();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  // Referencia al contenedor del dropdown para detectar clics exteriores
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Cierra el dropdown al hacer clic en cualquier parte fuera de él
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-14 flex items-center justify-between gap-4 px-4 md:px-6 border-b border-[var(--border-color)] bg-[var(--bg-primary)]">
      {/* Hamburger (mobile only) */}
      <button
        onClick={toggleMobile}
        className="md:hidden p-2 rounded-lg hover:bg-[var(--hover-bg)] text-[var(--text-secondary)] transition-colors cursor-pointer"
        aria-label="Abrir menú"
      >
        <Menu size={20} />
      </button>

      <div className="flex items-center gap-4 ml-auto">
      {/* Theme toggle */}
      <button
        onClick={toggleTheme}
        className="p-2 rounded-lg hover:bg-[var(--hover-bg)] text-[var(--text-secondary)] transition-colors cursor-pointer"
        title={theme === 'light' ? 'Modo oscuro' : 'Modo claro'}
      >
        {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
      </button>

      {/* User dropdown */}
      <div ref={dropdownRef} className="relative">
        <button
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-[var(--hover-bg)] transition-colors cursor-pointer"
        >
          {/* Avatar con inicial del nombre; fallback a 'U' si full_name no está disponible */}
          <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-[var(--text-primary)]">{user?.full_name}</p>
            <Badge color={user?.role === 'admin' ? 'green' : 'blue'}>
              {user?.role === 'admin' ? 'Admin' : 'Opersac'}
            </Badge>
          </div>
          <ChevronDown size={14} className="text-[var(--text-muted)]" />
        </button>

        {isDropdownOpen && (
          <div className="absolute right-0 mt-2 w-48 bg-[var(--card-bg)] border border-[var(--border-color)] rounded-lg shadow-lg z-50">
            <button
              onClick={() => { logout(); setIsDropdownOpen(false); }}
              className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-500 hover:bg-[var(--hover-bg)] rounded-lg transition-colors cursor-pointer"
            >
              <LogOut size={16} />
              Cerrar Sesion
            </button>
          </div>
        )}
      </div>
      </div>
    </header>
  );
}
