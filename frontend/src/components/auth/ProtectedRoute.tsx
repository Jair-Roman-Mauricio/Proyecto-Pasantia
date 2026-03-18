/**
 * @file ProtectedRoute.tsx
 * Componente de ruta protegida que verifica autenticación y autorización por rol
 * antes de renderizar el contenido solicitado.
 *
 * Flujo de decisión:
 *   1. Si la sesión aún se está resolviendo → muestra un spinner de pantalla completa.
 *   2. Si el usuario no está autenticado    → redirige a `/login`.
 *   3. Si `allowedRoles` está definido y el rol del usuario no está incluido
 *      → redirige a `/` (home).
 *   4. En cualquier otro caso               → renderiza los hijos normalmente.
 */

import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Spinner from '../ui/Spinner';

/**
 * Props del componente ProtectedRoute.
 *
 * @property children      - Ruta o componente a renderizar si se cumplen las condiciones.
 * @property allowedRoles  - Lista de roles con acceso permitido. Si se omite, cualquier
 *                           usuario autenticado puede acceder sin restricción de rol.
 */
interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
}

/**
 * Guarda de ruta que combina verificación de sesión y autorización basada en rol.
 * Usa `replace` en los redirects para que el usuario no pueda volver a la ruta
 * bloqueada con el botón "Atrás" del navegador.
 */
export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  // Mientras se resuelve la sesión de Supabase, se evita un flash de redirección
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Si se especifican roles permitidos, verifica que el usuario tenga uno de ellos
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
