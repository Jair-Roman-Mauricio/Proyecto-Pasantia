import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import StationDetailPage from './pages/StationDetailPage';

// QueryClient compartido para toda la app.
// staleTime=30s evita refetches innecesarios en navegación rápida entre estaciones.
// retry=1 reintenta una sola vez antes de mostrar error al usuario.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

export default function App() {
  // Árbol de providers (de afuera hacia adentro):
  // QueryClientProvider → ThemeProvider → AuthProvider → BrowserRouter
  //
  // Rutas:
  // /login           → LoginPage (pública)
  // /                → DashboardPage (protegida — renderiza vista según sidebar)
  // /stations/:id    → StationDetailPage (protegida — detalle con tabs)
  // *                → redirige a / (catch-all)
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                element={
                  // ProtectedRoute redirige a /login si no hay sesión activa
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              >
                <Route path="/" element={<DashboardPage />} />
                <Route path="/stations/:stationId" element={<StationDetailPage />} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
