/**
 * @file authService.ts
 * Servicio de autenticación que integra Supabase Auth con el backend propio.
 * El flujo de login obtiene primero el token JWT de Supabase y luego lo usa
 * para consultar el perfil enriquecido del usuario desde la API interna.
 *
 * Estrategia de email interno:
 *   Los usernames se transforman a `{username}@linea1metro.internal` para
 *   usar la autenticación por email de Supabase sin exponer emails reales.
 */

import { supabase } from '../config/supabaseClient';
import api from '../config/api';
import type { UserBrief } from '../types';

/**
 * Servicio de autenticación de la aplicación.
 * Combina Supabase Auth (emisión de JWT) con el endpoint `/auth/me`
 * del backend (perfil de usuario con rol y permisos).
 */
export const authService = {
  /**
   * Autentica al usuario contra Supabase Auth usando email interno.
   * El email se construye como `{username}@linea1metro.internal`.
   *
   * @returns El access_token de Supabase y los datos de perfil del backend.
   */
  async login(username: string, password: string): Promise<{ access_token: string; user: UserBrief }> {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    const { data } = await api.post<{ access_token: string; token_type: string }>(
      '/auth/login',
      form,
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
    const user = await authService.getMe(data.access_token);
    return { access_token: data.access_token, user };
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
    // Si se pasa token explícitamente (p. ej. justo tras el login antes de guardarlo
    // en contexto), se incluye en la cabecera; de lo contrario el interceptor de Axios
    // lo adjunta automáticamente desde el estado de sesión de Supabase.
    const config = token ? { headers: { Authorization: `Bearer ${token}` } } : {};
    const { data } = await api.get<UserBrief>('/auth/me', config);
    return data;
  },
};
