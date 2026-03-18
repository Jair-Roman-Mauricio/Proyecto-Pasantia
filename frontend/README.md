# Frontend — Sistema de Gestión Energética · Línea 1 Metro de Lima

Interfaz web construida con **React + TypeScript + Vite** para visualizar y administrar la infraestructura eléctrica de las 26 estaciones de la Línea 1 del Metro de Lima.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Framework UI | React 19 + TypeScript 5 |
| Bundler | Vite 7 |
| Estilos | Tailwind CSS 4 |
| Estado/datos | TanStack React Query 5 |
| Autenticación | Supabase JS (Auth) |
| Gráficos | Recharts |
| Iconos | Lucide React |
| HTTP client | Axios |

---

## Roles y vistas

| Rol | Acceso |
|---|---|
| `admin` | Todas las vistas: mapa, notificaciones, solicitudes, reportes, permisos, usuarios, backups, auditoría, guía |
| `opersac` | Vistas habilitadas por permiso: mapa de estaciones, solicitudes propias, reportes, guía |

Los permisos (`view_stations`, `view_circuits`, `send_requests`, `add_observations`, `view_reports`) se cargan al iniciar sesión y filtran las opciones visibles en el sidebar.

---

## Requisitos previos

- Node.js 18+
- Proyecto en [Supabase](https://supabase.com) (Auth habilitado)
- Backend corriendo en `http://localhost:8000`

---

## Instalación

```bash
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con los valores reales
```

---

## Variables de entorno

| Variable | Descripción |
|---|---|
| `VITE_API_BASE_URL` | URL base del backend · ej: `http://localhost:8000/api/v1` |
| `VITE_SUPABASE_URL` | URL del proyecto Supabase · ej: `https://xxxx.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Clave anónima pública de Supabase |

---

## Comandos de desarrollo

```bash
# Servidor de desarrollo con HMR
npm run dev          # http://localhost:5173

# Verificación de tipos TypeScript
npm run build        # compila + genera dist/

# Lint
npm run lint
```

---

## Estructura de carpetas

```
frontend/src/
├── components/         # Componentes React organizados por dominio
│   ├── audit/          # Tabla de logs de auditoría
│   ├── backup/         # Historial de backups
│   ├── guide/          # Vista de guía de usuario
│   ├── layout/         # AppLayout, Sidebar, Header
│   ├── notifications/  # Lista de notificaciones
│   ├── permissions/    # Gestor de permisos por usuario
│   ├── reports/        # Vista de reportes energéticos
│   ├── requests/       # Tabla de solicitudes OPERSAC
│   ├── station-detail/ # Tabs de detalle de estación (resumen, unifilar, barras)
│   ├── station-map/    # Mapa de las 26 estaciones con estado energético
│   ├── ui/             # Componentes base reutilizables (Button, Modal, Table, etc.)
│   └── users/          # Gestión de usuarios (solo admin)
├── config/
│   ├── api.ts          # Instancia Axios con interceptor de Authorization
│   └── supabaseClient.ts  # Cliente Supabase para Auth
├── context/
│   ├── AuthContext.tsx     # Sesión Supabase, perfil de usuario, permisos
│   ├── SidebarContext.tsx  # Opción activa del sidebar
│   └── ThemeContext.tsx    # Tema claro/oscuro
├── hooks/              # Hooks personalizados (useLoginNotifications, etc.)
├── pages/
│   ├── DashboardPage.tsx      # Dashboard principal con renderContent()
│   ├── LoginPage.tsx          # Formulario de login (Supabase Auth)
│   └── StationDetailPage.tsx  # Detalle de estación con sistema de tabs
├── services/           # Funciones de acceso a la API REST
├── types/
│   └── index.ts        # Tipos TypeScript de todas las entidades del sistema
└── App.tsx             # Raíz: providers, QueryClient, rutas React Router
```

---

## Flujo de autenticación

1. El usuario ingresa `username` y `password` en `LoginPage`.
2. `authService.login()` llama a `POST /api/v1/auth/login` que delega en Supabase.
3. Se obtiene un `access_token` JWT que se almacena en `AuthContext`.
4. Axios interceptor inyecta el token en cada request (`Authorization: Bearer ...`).
5. Supabase renueva el token automáticamente (`onAuthStateChange`).

---

## Build para producción

```bash
npm run build
# Genera dist/ — servir con nginx o cualquier servidor estático
```

El `Dockerfile.frontend` construye la imagen con nginx incluido como reverse proxy.
