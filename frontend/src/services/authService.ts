import api from '../config/api';
import type { LoginResponse, UserBrief } from '../types';

/**
 * Servicio de autenticación.
 * Encapsula las peticiones HTTP relacionadas con la identidad del usuario.
 */
export const authService = {
  /**
   * Autentica al usuario contra el backend enviando las credenciales al endpoint `/auth/login`.
   *
   * @param username - Nombre de usuario registrado en el sistema.
   * @param password - Contraseña en texto plano (el hash se gestiona en el servidor).
   * @returns Una promesa que resuelve con el objeto `LoginResponse`, el cual incluye
   *          el token JWT de acceso y los datos básicos del usuario autenticado.
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/auth/login', { username, password });
    return data;
  },

  /**
   * Obtiene los datos del usuario actualmente autenticado desde el endpoint `/auth/me`.
   * Requiere que el interceptor de Axios adjunte el token JWT en la cabecera `Authorization`.
   *
   * @returns Una promesa que resuelve con el objeto `UserBrief` del usuario en sesión.
   */
  async getMe(): Promise<UserBrief> {
    const { data } = await api.get<UserBrief>('/auth/me');
    return data;
  },
};
