import axios from 'axios';

/**
 * Instancia de Axios configurada para consumir la API del backend.
 * Todas las solicitudes se envían a la ruta base `/api/v1` con Content-Type JSON.
 */
const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

/**
 * Interceptor de solicitudes (request).
 * Adjunta el token JWT almacenado en localStorage al header `Authorization`
 * de cada petición saliente, siguiendo el esquema Bearer.
 * Si no existe token (sesión no iniciada), la solicitud se envía sin header de auth.
 */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Interceptor de respuestas (response).
 * - Respuestas exitosas: las deja pasar sin modificación.
 * - Error 401 (no autorizado): limpia la sesión del localStorage y redirige al login,
 *   excepto cuando el error proviene del propio endpoint de login (evita bucle).
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      !error.config?.url?.includes('/auth/login')
    ) {
      // Sesión expirada o token inválido: se elimina la sesión local
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Solo redirige si el usuario no está ya en la página de login
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
