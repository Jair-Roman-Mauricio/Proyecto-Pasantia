import { useState, useRef, useEffect } from 'react';
import { Sun, Moon, LogOut, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import Badge from '../ui/Badge';

export default function Header() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

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
    <header className="h-14 flex items-center justify-end gap-4 px-6 border-b border-[var(--border-color)] bg-[var(--bg-primary)]">
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
    </header>
  );
}
