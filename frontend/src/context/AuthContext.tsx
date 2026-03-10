import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { UserBrief, Permission } from '../types';
import { authService } from '../services/authService';
import api from '../config/api';

/**
 * Contrato del contexto de autenticación.
 *
 * @property user            - Datos del usuario autenticado actualmente, o `null` si no hay sesión.
 * @property token           - JWT almacenado en localStorage, o `null` si no existe.
 * @property isAuthenticated - `true` cuando hay un usuario cargado en memoria.
 * @property isLoading       - `true` mientras se verifica la sesión al arrancar la aplicación.
 * @property login           - Inicia sesión con usuario y contraseña; carga permisos tras autenticar.
 * @property logout          - Limpia la sesión del cliente (localStorage + estado React).
 * @property hasPermission   - Verifica si el usuario actual tiene acceso a una clave de permiso.
 * @property refreshPermissions - Vuelve a cargar los permisos del usuario desde el servidor.
 */
interface AuthContextType {
  user: UserBrief | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  hasPermission: (key: string) => boolean;
  refreshPermissions: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserBrief | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Carga los permisos del usuario desde el endpoint `/permissions/me`.
   * Si el usuario es administrador, se omite la petición porque tiene acceso total.
   * En caso de error de red, se retorna el usuario con permisos vacíos para no bloquear la sesión.
   *
   * @param userData - Datos del usuario para el cual se cargarán los permisos.
   * @returns El mismo objeto `userData` enriquecido con el mapa de permisos, o sin cambios si es admin.
   */
  const loadPermissions = async (userData: UserBrief): Promise<UserBrief> => {
    if (userData.role === 'admin') return userData;
    try {
      const { data } = await api.get<Permission[]>('/permissions/me');
      const perms: Record<string, boolean> = {};
      data.forEach((p) => { perms[p.feature_key] = p.is_allowed; });
      return { ...userData, permissions: perms };
    } catch {
      return { ...userData, permissions: {} };
    }
  };

  /**
   * Efecto de inicialización: si existe un token en localStorage al montar el proveedor,
   * se consulta `/auth/me` para obtener los datos del usuario y luego se cargan sus permisos.
   * Si la petición falla (token inválido o expirado), se limpia la sesión automáticamente.
   * El flag `isLoading` permanece en `true` hasta que el flujo completo termina.
   */
  useEffect(() => {
    if (token) {
      authService
        .getMe()
        .then((userData) => loadPermissions(userData))
        .then(setUser)
        .catch(() => {
          // Token inválido o expirado: eliminar sesión persistida
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setToken(null);
          setUser(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [token]);

  /**
   * Autentica al usuario contra el backend y persiste el token en localStorage.
   * Tras un login exitoso, carga los permisos correspondientes al rol del usuario.
   *
   * @param username - Nombre de usuario.
   * @param password - Contraseña en texto plano (el cifrado ocurre en el backend).
   */
  const login = async (username: string, password: string) => {
    const response = await authService.login(username, password);
    localStorage.setItem('token', response.access_token);
    localStorage.setItem('user', JSON.stringify(response.user));
    setToken(response.access_token);
    const userWithPerms = await loadPermissions(response.user);
    setUser(userWithPerms);
  };

  /**
   * Cierra la sesión del usuario eliminando el token y los datos del usuario
   * tanto del estado React como de localStorage.
   */
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  /**
   * Verifica si el usuario autenticado tiene acceso a una funcionalidad específica.
   *
   * - Los administradores siempre retornan `true` (acceso total sin verificar permisos).
   * - Los operadores SAC verifican la clave `key` dentro de su mapa de permisos cargados;
   *   si la clave no existe, se considera denegado (`false`).
   *
   * @param key - Clave de permiso a verificar (por ejemplo, `'view_reports'`).
   * @returns `true` si el usuario tiene el permiso; `false` en caso contrario o si no está autenticado.
   */
  const hasPermission = useCallback((key: string): boolean => {
    if (!user) return false;
    // Los administradores tienen acceso irrestricto a todas las funcionalidades
    if (user.role === 'admin') return true;
    // Los opersac consultan su mapa de permisos cargado desde el servidor
    return user.permissions?.[key] ?? false;
  }, [user]);

  /**
   * Recarga los permisos del usuario actual desde el servidor y actualiza el estado.
   * Útil para reflejar cambios de permisos sin necesidad de cerrar sesión.
   */
  const refreshPermissions = useCallback(async () => {
    if (user) {
      const updated = await loadPermissions(user);
      setUser(updated);
    }
  }, [user]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        hasPermission,
        refreshPermissions,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook para consumir el contexto de autenticación desde cualquier componente hijo de `AuthProvider`.
 *
 * @throws {Error} Si se utiliza fuera del árbol de `AuthProvider`.
 * @returns El valor completo del contexto de autenticación (`AuthContextType`).
 *
 * @example
 * const { user, hasPermission, logout } = useAuth();
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
