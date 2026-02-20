import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { UserBrief, Permission } from '../types';
import { authService } from '../services/authService';
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
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
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

  useEffect(() => {
    if (token) {
      authService
        .getMe()
        .then((userData) => loadPermissions(userData))
        .then(setUser)
        .catch(() => {
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

  const login = async (username: string, password: string) => {
    const response = await authService.login(username, password);
    localStorage.setItem('token', response.access_token);
    localStorage.setItem('user', JSON.stringify(response.user));
    setToken(response.access_token);
    const userWithPerms = await loadPermissions(response.user);
    setUser(userWithPerms);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
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
