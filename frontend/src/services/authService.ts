import { supabase } from '../config/supabaseClient';
import api from '../config/api';
import type { UserBrief } from '../types';

export const authService = {
  /**
   * Autentica al usuario contra Supabase Auth usando email interno.
   * El email se construye como `{username}@linea1metro.internal`.
   *
   * @returns El access_token de Supabase y los datos de perfil del backend.
   */
  async login(username: string, password: string): Promise<{ access_token: string; user: UserBrief }> {
    const email = `${username}@linea1metro.internal`;
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error || !data.session) {
      throw new Error(error?.message || 'Credenciales incorrectas');
    }
    const user = await authService.getMe(data.session.access_token);
    return { access_token: data.session.access_token, user };
  },

  /**
   * Cierra la sesión en Supabase Auth.
   */
  async logout(): Promise<void> {
    await supabase.auth.signOut();
  },

  /**
   * Obtiene el perfil del usuario autenticado desde el backend.
   * Si no se pasa token, el interceptor de Axios lo adjunta automáticamente.
   */
  async getMe(token?: string): Promise<UserBrief> {
    const config = token ? { headers: { Authorization: `Bearer ${token}` } } : {};
    const { data } = await api.get<UserBrief>('/auth/me', config);
    return data;
  },
};
