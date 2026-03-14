import axios from 'axios';
import { supabase } from './supabaseClient';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

/**
 * Interceptor de solicitudes.
 * Obtiene el token de sesión actual de Supabase y lo adjunta al header Authorization.
 * Supabase refresca automáticamente el token cuando está próximo a expirar.
 */
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

/**
 * Interceptor de respuestas.
 * Error 401: cierra la sesión de Supabase y redirige al login.
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await supabase.auth.signOut();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
