import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { UserBrief, Permission } from '../types';
import { authService } from '../services/authService';
import { supabase } from '../config/supabaseClient';
import api from '../config/api';

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
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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
   * Al montar: recupera la sesión activa de Supabase (si existe) y carga el perfil.
   * Se suscribe a cambios de sesión para manejar refresh de tokens automáticamente.
   */
  useEffect(() => {
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (session?.access_token) {
        setToken(session.access_token);
        try {
          const userData = await authService.getMe(session.access_token);
          const userWithPerms = await loadPermissions(userData);
          setUser(userWithPerms);
        } catch {
          await supabase.auth.signOut();
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'TOKEN_REFRESHED' && session?.access_token) {
        setToken(session.access_token);
      } else if (event === 'SIGNED_OUT') {
        setToken(null);
        setUser(null);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const login = async (username: string, password: string) => {
    const { access_token, user: userData } = await authService.login(username, password);
    setToken(access_token);
    const userWithPerms = await loadPermissions(userData);
    setUser(userWithPerms);
  };

  const logout = async () => {
    await authService.logout();
    setToken(null);
    setUser(null);
  };

  const hasPermission = useCallback((key: string): boolean => {
    if (!user) return false;
    if (user.role === 'admin') return true;
    return user.permissions?.[key] ?? false;
  }, [user]);

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

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
