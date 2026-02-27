# Documentación del Frontend — Linea 1 Metro

Sistema de Gestión Energética para la Línea 1 del Metro de Lima.

---

## Stack tecnológico

| Librería | Versión | Para qué se usa |
|---|---|---|
| **React** | 19 | Librería principal para construir la interfaz de usuario con componentes reutilizables |
| **TypeScript** | 5.9 | Agrega tipado estático a JavaScript, evita errores en tiempo de desarrollo |
| **Vite** | 7 | Herramienta de build y servidor de desarrollo extremadamente rápida |
| **React Router DOM** | 7 | Manejo de rutas dentro de la SPA (Single Page Application) |
| **TanStack React Query** | 5 | Manejo de caché y sincronización de datos del servidor (no se usa extensivamente aquí pero está configurado) |
| **Axios** | 1.13 | Cliente HTTP para hacer llamadas a la API del backend |
| **Tailwind CSS** | 4 | Framework de utilidades CSS para estilizar directamente en el HTML/JSX |
| **Recharts** | 3 | Librería de gráficos para React (usada en SummaryTab para el pie chart) |
| **Lucide React** | 0.574 | Íconos SVG como componentes de React |
| **XLSX** | 0.18 | Exportar datos a archivos Excel (.xlsx) |

---

## Estructura de carpetas

```
frontend/src/
│
├── main.tsx                    ← Punto de entrada: monta React en el DOM
├── App.tsx                     ← Raíz de la app: rutas + proveedores globales
├── index.css                   ← Estilos globales y variables CSS del tema
│
├── types/
│   └── index.ts                ← Todas las interfaces TypeScript del sistema
│
├── config/
│   ├── api.ts                  ← Instancia global de Axios configurada
│   └── constants.ts            ← Datos estáticos: estaciones, colores, etiquetas
│
├── context/
│   ├── AuthContext.tsx          ← Estado global de autenticación y permisos
│   ├── ThemeContext.tsx         ← Estado global del tema (claro/oscuro)
│   └── SidebarContext.tsx       ← Estado global del sidebar (opción activa, modo vista)
│
├── services/
│   ├── authService.ts           ← Llamadas HTTP de autenticación
│   ├── stationService.ts        ← Llamadas HTTP de estaciones y barras
│   └── circuitService.ts        ← Llamadas HTTP de circuitos y sub-circuitos
│
├── components/
│   │
│   ├── ui/                      ← Componentes de interfaz genéricos y reutilizables
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   ├── Spinner.tsx
│   │   └── Table.tsx
│   │
│   ├── layout/                  ← Estructura visual fija de la app
│   │   ├── AppLayout.tsx
│   │   ├── Header.tsx
│   │   └── Sidebar.tsx
│   │
│   ├── auth/
│   │   └── ProtectedRoute.tsx   ← Guarda de rutas: redirige si no está autenticado
│   │
│   ├── notifications/
│   │   └── NotificationList.tsx ← Panel de notificaciones del sistema
│   │
│   └── station-detail/          ← Todos los componentes de detalle de una estación
│       ├── BarsCircuitsTab.tsx
│       ├── CircuitTable.tsx
│       ├── CircuitForm.tsx
│       ├── SubCircuitTable.tsx
│       ├── SubCircuitForm.tsx
│       ├── StatusChangeModal.tsx
│       ├── DeleteCircuitModal.tsx
│       ├── ObservationsModal.tsx
│       ├── PowerCards.tsx
│       ├── SummaryTab.tsx
│       └── UnifilarTab.tsx
│
└── pages/
    ├── LoginPage.tsx            ← Pantalla de inicio de sesión
    ├── DashboardPage.tsx        ← Panel principal (renderiza según opción del sidebar)
    └── StationDetailPage.tsx    ← Página de detalle de una estación específica
```

---

## 1. Punto de entrada

### `src/main.tsx`

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

**Qué hace:** Es el archivo que ejecuta el navegador primero. Busca el elemento `<div id="root">` en el `index.html` y monta toda la aplicación React dentro de él.

**Por qué `StrictMode`:** Es un componente especial de React que solo actúa en desarrollo. Detecta efectos secundarios impuros, advertencias de APIs obsoletas y problemas de renderizado doble. No afecta producción.

---

### `src/App.tsx`

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, retry: 1 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
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
```

**Qué hace:** Define toda la estructura global de la app: proveedores de estado global y las rutas.

**Por qué los proveedores están anidados en ese orden:**
- `QueryClientProvider` va más afuera porque cualquier componente puede necesitar hacer queries
- `ThemeProvider` antes que `AuthProvider` para que el tema esté disponible en la pantalla de login
- `AuthProvider` antes que `BrowserRouter` para que las rutas conozcan el estado de autenticación desde el principio

**Rutas:**
- `/login` → pantalla de login, pública
- `/` → dashboard, protegida (requiere autenticación)
- `/stations/:stationId` → detalle de estación, protegida
- `*` → cualquier ruta desconocida redirige al inicio

**`staleTime: 30000`:** Los datos de React Query se consideran frescos por 30 segundos, evitando re-fetches innecesarios al cambiar de pestaña.

---

## 2. Tipos TypeScript

### `src/types/index.ts`

Define las interfaces de todos los datos que viajan entre el frontend y el backend. No tiene lógica, solo tipos.

**Interfaces principales:**

| Interface | Describe |
|---|---|
| `User` | Usuario completo (admin u opersac) con estado y fechas |
| `UserBrief` | Versión reducida del usuario que se guarda en memoria (sin datos sensibles) |
| `LoginResponse` | Lo que devuelve el endpoint de login: token + datos del usuario |
| `Station` | Estación del metro con capacidades de transformador y estado de semáforo |
| `Bar` | Barra eléctrica (normal, emergencia, continuidad) de una estación |
| `Circuit` | Circuito conectado a una barra, con sus valores de potencia y estado |
| `SubCircuit` | Sub-división de un circuito con sus propios valores eléctricos |
| `LoadRequest` | Solicitud de carga enviada por un operador Opersac |
| `Notification` | Alerta del sistema (reserva vencida, energía negativa, etc.) |
| `Observation` | Nota técnica sobre una barra, circuito o sub-circuito |
| `AuditLog` | Registro de auditoría de cada acción en el sistema |
| `Backup` | Registro de un backup generado |
| `Permission` | Permiso específico asignado a un usuario Opersac |
| `BarPowerSummary` | Resumen de potencias calculadas para una barra |

**Por qué TypeScript:** Sin tipos, acceder a `circuit.reserve_expires_at` en un componente no daría error si el campo no existe. Con TypeScript, el editor marca el error antes de ejecutar el código, reduciendo bugs de producción.

---

## 3. Configuración

### `src/config/api.ts`

```ts
const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config?.url?.includes('/auth/login')) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

**Qué hace:** Crea una sola instancia de Axios configurada para toda la app. Todos los servicios importan esta instancia en lugar de crear la propia.

**`baseURL: '/api/v1'`:** URL relativa. En desarrollo, Vite hace proxy de `/api` a `http://localhost:8000`. En producción, nginx redirige `/api/` al backend. El frontend nunca necesita saber la IP del backend.

**Interceptor de request:** Antes de cada llamada HTTP, revisa si hay un token en `localStorage` y lo agrega automáticamente como header `Authorization: Bearer <token>`. Así todos los servicios quedan autenticados sin que cada uno tenga que poner el header manualmente.

**Interceptor de response:** Si cualquier llamada devuelve error 401 (no autorizado), cierra la sesión automáticamente y redirige al login. Excepción: el propio endpoint `/auth/login` puede devolver 401 (contraseña incorrecta) sin que se redirija.

---

### `src/config/constants.ts`

```ts
export const STATIONS = [
  { code: 'E01', name: 'Villa El Salvador', orderIndex: 1 },
  // ... 26 estaciones
];

export const CIRCUIT_STATUS_COLORS = {
  operative_normal: '#22c55e',
  reserve_r: '#eab308',
  reserve_equipped_re: '#3b82f6',
  inactive: '#6b7280',
};
```

**Qué hace:** Centraliza todos los datos estáticos que no cambian. Se importan en múltiples componentes.

**Por qué no están hardcodeados en cada componente:** Si el color de "Reserva" cambia de amarillo a naranja, se cambia en un solo lugar y se actualiza en toda la app. Sin este archivo habría que buscar y cambiar en cada componente.

**Contenido:**
- `STATIONS` — lista completa de las 26 estaciones con código, nombre y orden
- `BAR_TYPES` — tipos de barra (normal, emergencia, continuidad)
- `CIRCUIT_STATUS_COLORS` — color hex para cada estado de circuito
- `CIRCUIT_STATUS_LABELS` — texto legible para cada estado
- `STATION_STATUS_COLORS` — colores para el semáforo de estaciones
- `OBSERVATION_SEVERITY_COLORS` — colores para urgente, advertencia, recomendación
- `IMAGE_JUSTIFICATION_REASONS` — razones predefinidas para cambios de imágenes

---

## 4. Contextos (estado global)

Los contextos de React permiten compartir datos entre componentes sin pasar props manualmente por cada nivel. Se usan tres contextos en esta app.

### `src/context/AuthContext.tsx`

Gestiona todo lo relacionado con la sesión del usuario: quién está logueado, si tiene permiso para hacer algo, y cómo iniciar/cerrar sesión.

**Estados internos:**
```ts
const [user, setUser] = useState<UserBrief | null>(null);
const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
const [isLoading, setIsLoading] = useState(true);
```

| Estado | Tipo | Qué controla |
|---|---|---|
| `user` | `UserBrief \| null` | Datos del usuario logueado. `null` si no hay sesión |
| `token` | `string \| null` | JWT de autenticación. Se inicializa desde `localStorage` para persistir entre recargas |
| `isLoading` | `boolean` | `true` mientras se verifica si el token guardado sigue siendo válido |

**`useEffect` para verificar sesión al cargar:**
```ts
useEffect(() => {
  if (token) {
    authService.getMe()
      .then(loadPermissions)
      .then(setUser)
      .catch(() => { /* limpiar token inválido */ })
      .finally(() => setIsLoading(false));
  } else {
    setIsLoading(false);
  }
}, [token]);
```
Al recargar la página, si hay un token guardado, se verifica con el backend que sigue siendo válido (`/auth/me`). Si el backend rechaza el token (expirado), se limpia la sesión. El `isLoading: true` mientras ocurre esto evita que el usuario vea un flash de la pantalla de login antes de ser redirigido al dashboard.

**`useCallback` en `hasPermission` y `refreshPermissions`:**
```ts
const hasPermission = useCallback((key: string): boolean => {
  if (!user) return false;
  if (user.role === 'admin') return true;
  return user.permissions?.[key] ?? false;
}, [user]);
```
`useCallback` memoriza la función para que no se recree en cada render. Esto es importante porque `hasPermission` se pasa a muchos componentes y sin `useCallback` causaría re-renders innecesarios.

**`loadPermissions`:** Para usuarios Opersac, obtiene del backend qué funciones tienen habilitadas. Los admins siempre tienen todos los permisos sin consultar la API.

**Hook personalizado `useAuth()`:** Los componentes no importan `AuthContext` directamente sino que usan `useAuth()`. Esto encapsula la lógica de "¿estoy dentro del provider?" y lanza un error claro si se usa fuera de él.

---

### `src/context/ThemeContext.tsx`

```ts
const [theme, setTheme] = useState<Theme>(() => {
  return (localStorage.getItem('theme') as Theme) || 'light';
});

useEffect(() => {
  const root = document.documentElement;
  if (theme === 'dark') root.classList.add('dark');
  else root.classList.remove('dark');
  localStorage.setItem('theme', theme);
}, [theme]);
```

**Qué hace:** Controla el tema claro/oscuro de toda la app y lo persiste en `localStorage`.

**`useState` con función inicializadora:** El estado inicial se calcula una sola vez leyendo `localStorage`. Si se pusiera `useState(localStorage.getItem('theme'))` directamente, se ejecutaría en cada render. Con la función `() => ...`, solo se ejecuta al montar.

**`useEffect` al cambiar `theme`:** Cada vez que el tema cambia, agrega o quita la clase `dark` del elemento `<html>`. Tailwind CSS usa esta clase para activar los estilos oscuros. También guarda la preferencia en `localStorage` para que persista al recargar.

---

### `src/context/SidebarContext.tsx`

```ts
const [activeOption, setActiveOption] = useState('map');
const [viewMode, setViewMode] = useState<ViewMode>('admin');
const [isCollapsed, setIsCollapsed] = useState(false);
```

**Qué hace:** Comparte el estado de la barra lateral entre `Sidebar` (que muestra los botones) y `DashboardPage` (que renderiza el contenido según la opción activa).

**Sin este contexto:** `Sidebar` tendría que pasar la opción activa al padre `AppLayout`, que la pasaría a `DashboardPage` a través de props. El contexto elimina este "prop drilling".

| Estado | Qué controla |
|---|---|
| `activeOption` | Qué sección está seleccionada en el sidebar ('map', 'notifications', 'users', etc.) |
| `viewMode` | Si el admin está viendo la interfaz como admin o como Opersac (simulación) |
| `isCollapsed` | Si el sidebar está colapsado (preparado para implementación futura) |

---

## 5. Servicios (capa HTTP)

Los servicios son módulos que encapsulan todas las llamadas HTTP a la API. Los componentes importan los servicios en lugar de usar `axios` directamente. Esto separa la lógica de red de la lógica de interfaz.

### `src/services/authService.ts`

```ts
export const authService = {
  async login(username, password): Promise<LoginResponse> {
    const { data } = await api.post('/auth/login', { username, password });
    return data;
  },
  async getMe(): Promise<UserBrief> {
    const { data } = await api.get('/auth/me');
    return data;
  },
};
```

**Endpoints:** `POST /auth/login` y `GET /auth/me`.

---

### `src/services/stationService.ts`

```ts
export const stationService = {
  getAll()             → GET /stations
  getById(id)          → GET /stations/:id
  getPowerSummary(id)  → GET /stations/:id/power-summary
  getBars(stationId)   → GET /bars/station/:stationId
};
```

---

### `src/services/circuitService.ts`

Es el servicio más completo porque cubre circuitos, sub-circuitos y potencia de barras.

```ts
export const circuitService = {
  getByBar(barId)                   → GET /circuits/bar/:barId
  getById(id)                       → GET /circuits/:id
  create(barId, circuit)            → POST /circuits/bar/:barId
  update(id, circuit)               → PUT /circuits/:id
  updateStatus(id, status)          → PUT /circuits/:id/status
  delete(id)                        → DELETE /circuits/:id
  getSubCircuits(circuitId)         → GET /sub-circuits/circuit/:circuitId
  createSubCircuit(circuitId, sub)  → POST /sub-circuits/circuit/:circuitId
  deleteSubCircuit(id)              → DELETE /sub-circuits/:id
  updateSubCircuitStatus(id,status) → PUT /sub-circuits/:id/status
  getBarPowerSummary(barId)         → GET /bars/:barId/power-summary
};
```

**`force?: boolean` en `create`:** El backend puede rechazar la creación si la capacidad del transformador se excede, pero permite forzar la operación. El frontend envía `force: true` cuando el usuario confirma que quiere continuar de todas formas.

---

## 6. Componentes UI reutilizables

Estos componentes no tienen lógica de negocio. Son bloques de construcción visuales usados en toda la app. Todos están en `src/components/ui/`.

### `Button.tsx`

```tsx
const variants = {
  primary:   'bg-primary-600 text-white hover:bg-primary-700',
  secondary: 'bg-transparent text-[var(--text-primary)] border-[var(--border-color)]',
  danger:    'bg-red-600 text-white hover:bg-red-700',
  ghost:     'bg-transparent text-[var(--text-secondary)] border-transparent',
};
const sizes = { sm: 'px-3 py-1.5 text-xs', md: 'px-4 py-2 text-sm', lg: 'px-6 py-3 text-base' };
```

**Por qué este patrón:** En lugar de escribir clases de Tailwind repetidas en cada botón de la app, se define una vez aquí y se elige con `variant` y `size`. `disabled:opacity-50 disabled:cursor-not-allowed` se aplica automáticamente a todos los botones del sistema.

---

### `Input.tsx`

```tsx
const Input = forwardRef<HTMLInputElement, InputProps>(({ label, error, ...props }, ref) => (
  <div className="space-y-1">
    {label && <label className="...">{label}</label>}
    <input ref={ref} className="..." {...props} />
    {error && <p className="text-xs text-red-500">{error}</p>}
  </div>
));
```

**Por qué `forwardRef`:** Permite que el componente padre pase una `ref` al elemento `<input>` interno. Sin `forwardRef`, `<Input ref={myRef} />` no funcionaría porque la ref apuntaría al componente React, no al DOM element. Se usa cuando el padre necesita hacer `focus()` programáticamente en el input.

---

### `Modal.tsx`

```tsx
useEffect(() => {
  if (isOpen) document.body.style.overflow = 'hidden';
  else document.body.style.overflow = '';
  return () => { document.body.style.overflow = ''; };
}, [isOpen]);

// Cerrar al hacer clic fuera:
<div ref={overlayRef} onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}>
```

**`useEffect` para bloquear scroll:** Cuando el modal está abierto, bloquea el scroll del body para que el usuario no desplace el contenido detrás del modal. El `return () => {...}` es la función de cleanup: cuando el modal se desmonta, restaura el scroll.

**`useRef` para el overlay:** Se necesita distinguir entre clic en el overlay (fondo oscuro) y clic dentro del modal. `e.target === overlayRef.current` es verdadero solo si se hizo clic exactamente en el overlay, no en cualquier elemento hijo.

**`if (!isOpen) return null`:** El modal no existe en el DOM cuando está cerrado. Esto es más eficiente que usar `display: none` porque React no renderiza ni gestiona los componentes hijos cuando no están montados.

---

### `Table.tsx`

```tsx
interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => ReactNode;
}

export default function Table<T>({ columns, data, rowKey, rowClassName, onRowClick }: TableProps<T>) { ... }
```

**Por qué genérico `<T>`:** La tabla funciona con cualquier tipo de dato (Circuit, SubCircuit, AuditLog, etc.) sin duplicar código. El parámetro de tipo `T` garantiza que `render` recibe el tipo correcto de cada fila.

**`rowClassName`:** Función que recibe el ítem y devuelve clases CSS. Permite colorear filas condicionalmente según el estado del objeto (ej: filas amarillas para circuitos en reserva).

---

### `Card.tsx`

```tsx
<div
  className={`bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-4
    ${onClick ? 'cursor-pointer hover:border-primary-500' : ''}`}
  onClick={onClick}
>
```

**Por qué `onClick` opcional:** Si se pasa un `onClick`, la tarjeta se hace clicable (cambia el cursor y agrega hover). Si no, es solo un contenedor visual. Un mismo componente sirve para ambos casos.

---

### `Badge.tsx`

Muestra etiquetas de colores (verde para admin, azul para opersac, rojo para estado crítico, etc.). Define un `colorMap` con las clases de Tailwind para cada color, incluyendo variantes de modo oscuro.

---

### `Spinner.tsx`

Indicador de carga animado. Acepta `size` para ajustar el tamaño. Se usa en cualquier lugar donde haya una carga asíncrona en progreso.

---

## 7. Layout

### `src/components/layout/AppLayout.tsx`

```tsx
export default function AppLayout() {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 p-6 overflow-auto bg-[var(--bg-secondary)]">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
```

**Qué hace:** Define la estructura visual de dos columnas: sidebar izquierdo fijo + contenido principal a la derecha con header arriba.

**`<Outlet />`:** Es de React Router. Renderiza el componente de la ruta activa dentro del layout. Cuando la URL es `/`, renderiza `DashboardPage`. Cuando es `/stations/5`, renderiza `StationDetailPage`. El layout (sidebar + header) permanece igual.

**`SidebarProvider` aquí:** El contexto del sidebar envuelve tanto `Sidebar` como el `<Outlet>` (donde está `DashboardPage`), porque ambos necesitan leer y escribir el estado de la opción activa.

---

### `src/components/layout/Header.tsx`

```tsx
const [isDropdownOpen, setIsDropdownOpen] = useState(false);
const dropdownRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  function handleClickOutside(event: MouseEvent) {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
      setIsDropdownOpen(false);
    }
  }
  document.addEventListener('mousedown', handleClickOutside);
  return () => document.removeEventListener('mousedown', handleClickOutside);
}, []);
```

**`useState` — `isDropdownOpen`:** Controla si el menú desplegable del usuario está visible.

**`useRef` + `useEffect` para cerrar al clic externo:** Es el patrón estándar para cerrar dropdowns. Se agrega un listener al `document` que detecta cualquier clic. Si el clic no está dentro del dropdown (`!contains(event.target)`), se cierra. El `return () => removeEventListener(...)` limpia el listener cuando el componente se desmonta para evitar memory leaks.

**Datos de `useAuth()` y `useTheme()`:** El header usa ambos contextos: muestra el nombre del usuario y su rol (de `AuthContext`), y el botón de tema llama `toggleTheme()` (de `ThemeContext`).

---

### `src/components/layout/Sidebar.tsx`

```tsx
const options = viewMode === 'admin' && user?.role === 'admin'
  ? adminOptions
  : opersacOptions.filter(opt => hasPermission(opt.permission));
```

**Qué hace:** Renderiza la barra lateral de navegación con las opciones disponibles según el rol del usuario.

**Dos listas de opciones:** `adminOptions` tiene 8 opciones (todas las funciones). `allOpersacOptions` tiene 3 opciones básicas filtradas por permisos individuales del usuario.

**`viewMode === 'admin'`:** Los administradores pueden activar "Ver como Opersac" para simular qué ve un operador. Esto cambia el `viewMode` en el contexto y el sidebar se re-renderiza mostrando solo las opciones del operador.

**`navigate('/')` al hacer clic:** Al seleccionar una opción del sidebar, además de actualizar `activeOption`, navega a la ruta `/` para asegurarse de que se muestre el `DashboardPage` y no la página de detalle de una estación.

---

## 8. Páginas

### `src/pages/LoginPage.tsx`

```tsx
const [username, setUsername] = useState('');
const [password, setPassword] = useState('');
const [error, setError] = useState('');
const [isLoading, setIsLoading] = useState(false);
```

**Estados:**

| Estado | Qué controla |
|---|---|
| `username` | Valor del campo de texto del usuario |
| `password` | Valor del campo de contraseña |
| `error` | Mensaje de error que se muestra bajo el formulario si el login falla |
| `isLoading` | Deshabilita el botón y cambia su texto durante la llamada al API |

**Flujo:** `handleSubmit` llama `login()` del `AuthContext`. Si tiene éxito, `navigate('/')` lleva al dashboard. Si falla, muestra el mensaje de error. El `finally` siempre quita el estado de carga.

---

### `src/pages/DashboardPage.tsx`

```tsx
export default function DashboardPage() {
  const { activeOption } = useSidebar();
  const renderContent = () => {
    switch (activeOption) {
      case 'map':           return <StationMap />;
      case 'notifications': return <NotificationList />;
      case 'requests':      return <RequestTable />;
      // ...
    }
  };
  return <>{renderContent()}</>;
}
```

**Qué hace:** Es un "enrutador visual" que muestra un componente diferente según la opción seleccionada en el sidebar. No tiene estado propio.

**Por qué no hay rutas separadas para cada sección:** Todas las secciones del dashboard viven en la misma URL `/`. Cambiar la opción del sidebar no cambia la URL. Esto es una decisión de diseño: el sistema es una SPA interna y no se necesita que cada sección tenga una URL navegable.

---

### `src/pages/StationDetailPage.tsx`

```tsx
const { stationId } = useParams<{ stationId: string }>();
const [station, setStation] = useState<Station | null>(null);
const [activeTab, setActiveTab] = useState<Tab>('unifilar');
const [isLoading, setIsLoading] = useState(true);

const refreshStation = useCallback(() => {
  if (stationId) stationService.getById(Number(stationId)).then(setStation);
}, [stationId]);

useEffect(() => {
  stationService.getById(Number(stationId))
    .then(setStation)
    .catch(() => navigate('/'))
    .finally(() => setIsLoading(false));
}, [stationId, navigate]);
```

**`useParams`:** Lee el parámetro `:stationId` de la URL. Si la URL es `/stations/5`, `stationId` es `"5"`.

**`useState` — `station`:** Comienza como `null` mientras carga. Una vez recibida la respuesta del API, se llena con los datos de la estación.

**`useState` — `activeTab`:** Controla cuál de las tres pestañas está activa. El valor inicial es `'unifilar'` para mostrar el mapa eléctrico por defecto.

**`useEffect` para cargar datos:** Se ejecuta cuando el componente monta o cuando `stationId` cambia. Si el ID no es válido (la API devuelve error), redirige al inicio. Siempre termina quitando el spinner.

**`useCallback` — `refreshStation`:** Es una función que los componentes hijos pueden llamar para refrescar los datos de la estación (ej: después de subir una foto nueva). Con `useCallback`, la función mantiene la misma referencia entre renders, evitando re-renders innecesarios en los hijos que la reciben como prop.

---

## 9. Componentes de detalle de estación

### `BarsCircuitsTab.tsx`

Es el componente más grande del sistema. Gestiona la vista de árbol barras→circuitos y toda la interacción de gestión eléctrica.

**Estados:**
```tsx
const [bars, setBars] = useState<Bar[]>([]);
const [selectedBar, setSelectedBar] = useState<Bar | null>(null);
const [circuits, setCircuits] = useState<Circuit[]>([]);
const [selectedCircuit, setSelectedCircuit] = useState<Circuit | null>(null);
const [subCircuits, setSubCircuits] = useState<SubCircuit[]>([]);
const [expandedBars, setExpandedBars] = useState<Set<number>>(new Set());
const [isEditMode, setIsEditMode] = useState(false);
const [powerSummary, setPowerSummary] = useState<BarPowerSummary | null>(null);
// + estados de modales y formularios
```

| Estado | Tipo | Qué controla |
|---|---|---|
| `bars` | `Bar[]` | Lista de barras de la estación |
| `selectedBar` | `Bar \| null` | Barra actualmente seleccionada en el árbol |
| `circuits` | `Circuit[]` | Circuitos de la barra seleccionada |
| `selectedCircuit` | `Circuit \| null` | Circuito seleccionado para ver sus sub-circuitos |
| `subCircuits` | `SubCircuit[]` | Sub-circuitos del circuito seleccionado |
| `expandedBars` | `Set<number>` | IDs de barras cuyo árbol está expandido (puede haber varias expandidas a la vez) |
| `isEditMode` | `boolean` | Activa botones de eliminar y cambiar estado |
| `powerSummary` | `BarPowerSummary \| null` | Resumen de potencias para mostrar en las tarjetas superiores |

**`Set<number>` para `expandedBars`:** Un `Set` es la estructura correcta para saber si un ID está en la colección, con O(1) de búsqueda. Si se usara un array, habría que hacer `array.includes(id)` en cada render de cada barra.

**Carga en cascada:** Al seleccionar una barra, carga sus circuitos y el resumen de potencia. Al seleccionar un circuito, carga sus sub-circuitos. Cada carga tiene su propio estado de loading.

---

### `CircuitTable.tsx`

```tsx
rowClassName={(c) => {
  if (c.status === 'reserve_r') return 'bg-yellow-500/10';
  if (c.status === 'reserve_equipped_re') return 'bg-blue-500/10';
  return '';
}}
```

**Qué hace:** Tabla de circuitos con coloreado de filas según estado. Para circuitos UPS (conectados a múltiples barras), muestra un modal intermedio para elegir a cuál barra navegar.

**`useState` — `upsCircuit`:** Cuando se hace clic en "Ver" de un circuito UPS, en lugar de navegar directamente, guarda el circuito en este estado y muestra un modal. `null` significa que el modal está cerrado.

**`bg-yellow-500/10` en lugar de `bg-yellow-50`:** El sufijo `/10` es opacidad del 10%. Funciona igual en modo claro y oscuro porque usa transparencia sobre el fondo existente, en lugar de un color sólido que sería invisible en modo oscuro.

---

### `CircuitForm.tsx`

Formulario modal para crear nuevos circuitos con soporte para UPS y confirmación de forzado.

**Estados:**
```tsx
const [denomination, setDenomination] = useState('');
const [name, setName] = useState('');
const [status, setStatus] = useState('operative_normal');
const [reserveExpiresAt, setReserveExpiresAt] = useState('');
const [isUps, setIsUps] = useState(false);
const [secondaryBarId, setSecondaryBarId] = useState<number | null>(null);
const [tertiaryBarId, setTertiaryBarId] = useState<number | null>(null);
const [error, setError] = useState('');
const [isSubmitting, setIsSubmitting] = useState(false);
const [forceMessage, setForceMessage] = useState<string | null>(null);
const [pendingPayload, setPendingPayload] = useState<Record<string, unknown> | null>(null);
```

**`forceMessage` + `pendingPayload`:** Implementan el flujo de confirmación. Cuando el API responde con `requires_force: true`, el formulario no hace `confirm()` del navegador sino que guarda el payload y el mensaje. Se abre un segundo modal con el mensaje. Si el usuario acepta, se reenvía con `force: true`. Si cancela, ambos estados vuelven a `null`.

**`isReserve` calculado, no estado:**
```tsx
const isReserve = status === 'reserve_r' || status === 'reserve_equipped_re';
```
No es un `useState` porque se puede derivar del estado `status`. Si fuera un estado separado, habría que mantenerlos sincronizados, lo que causa bugs.

**Cálculo automático de MD:**
```tsx
const mdKw = (parseFloat(piKw) || 0) * (parseFloat(fd) || 1);
```
MD = PI × F.D. Se recalcula en cada render en lugar de almacenarlo en estado. El resultado siempre es consistente con los valores actuales de PI y F.D.

---

### `SubCircuitForm.tsx`

Similar a `CircuitForm` pero para sub-circuitos. Incluye campos adicionales: ITM, MM2 (especificaciones del cable) y override manual del MD.

**`mdManual` + `mdOverride`:**
```tsx
const [mdManual, setMdManual] = useState('');
const [mdOverride, setMdOverride] = useState(false);
```
Por defecto el MD se calcula automáticamente. Si el usuario activa el override, puede ingresar un MD personalizado. Cuando `mdOverride` es `false`, el campo MD se muestra como solo lectura con el valor calculado.

---

### `SubCircuitTable.tsx`

```tsx
const handleDelete = async (sub: SubCircuit) => {
  if (!confirm(`Eliminar sub-circuito "${sub.name}"?`)) return;
  // ...
};
```

Tabla con las columnas: estado (dot de color), nombre, descripción, ITM, MM2, PI, F.D, MD. En modo edición aparece el botón de eliminar.

> Nota: Este componente todavía usa `confirm()` del navegador para la eliminación. A diferencia de `CircuitForm`, aquí no se reemplazó por modal personalizado aún.

---

### `StatusChangeModal.tsx`

```tsx
const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
const [targetStatus, setTargetStatus] = useState('operative_normal');
const [isSaving, setIsSaving] = useState(false);
```

**Qué hace:** Permite cambiar el estado de varios circuitos o sub-circuitos a la vez. Muestra la lista con checkboxes para selección múltiple.

**`Set<number>` para `selectedIds`:** Igual que `expandedBars`, un Set es la estructura correcta para selección múltiple. Agregar y quitar IDs es O(1).

**`type` prop:** El modal funciona tanto para circuitos como para sub-circuitos. Según `type === 'circuits'` o `type === 'subCircuits'`, llama al endpoint correcto y muestra la lista correcta.

---

### `DeleteCircuitModal.tsx`

```tsx
const [subCircuits, setSubCircuits] = useState<SubCircuit[]>([]);
const [isLoading, setIsLoading] = useState(false);
const [isDeleting, setIsDeleting] = useState(false);
```

**Qué hace:** Antes de eliminar un circuito, muestra los sub-circuitos que serán eliminados en cascada. Ofrece descargar un reporte Excel de los datos antes de eliminar.

**`useEffect` para cargar sub-circuitos:**
```tsx
useEffect(() => {
  if (circuit) {
    setIsLoading(true);
    circuitService.getSubCircuits(circuit.id)
      .then(setSubCircuits)
      .finally(() => setIsLoading(false));
  }
}, [circuit]);
```
Cuando `circuit` cambia (se abre el modal con un circuito diferente), recarga los sub-circuitos. El array de dependencias `[circuit]` es clave: sin él, solo cargaría al montar el componente, no cuando cambia el circuito.

---

### `ObservationsModal.tsx`

```tsx
const [observations, setObservations] = useState<Observation[]>([]);
const [content, setContent] = useState('');
const [severity, setSeverity] = useState<'recommendation' | 'warning' | 'urgent'>('recommendation');
const [isAdding, setIsAdding] = useState(false);
```

**Qué hace:** Muestra y permite agregar observaciones técnicas a barras, circuitos o sub-circuitos. Las observaciones tienen tres niveles de severidad con colores diferentes.

**Dos modos de `entity`:** El modal recibe un `entityType` ('bar', 'circuit', 'subCircuit') y el ID correspondiente. Según el tipo, llama al endpoint correcto para guardar la observación.

---

### `PowerCards.tsx`

```tsx
interface PowerCardsProps {
  summary: BarPowerSummary;
}
```

Componente puramente presentacional. No tiene estados ni efectos. Recibe un objeto `summary` y renderiza 4 tarjetas con los valores de potencia. La tarjeta de "Potencia Disponible" se pinta de verde si es positiva y de rojo si es negativa.

---

### `SummaryTab.tsx`

```tsx
const [imageKey, setImageKey] = useState(0);
const [showUploadModal, setShowUploadModal] = useState(false);
```

**`imageKey`:** Truco para forzar que el navegador recargue una imagen. El navegador cachea imágenes por URL. Cuando se sube una imagen nueva (misma URL, contenido diferente), el navegador no la recarga. Incrementar `imageKey` cambia el `key` del elemento `<img>`, forzando a React a desmontar y remontar el componente, lo que hace que el navegador descargue la imagen nuevamente.

**Gráfico de dona con Recharts:**
```tsx
<PieChart>
  <Pie data={[
    { name: 'Consumido', value: summary.max_demand_kw },
    { name: 'Disponible', value: Math.max(0, summary.available_power_kw) },
  ]} />
</PieChart>
```

---

### `UnifilarTab.tsx`

Similar a `SummaryTab` pero para el diagrama unifilar. Muestra la imagen del diagrama eléctrico de la estación y permite actualizarla. Usa el mismo truco de `imageKey` para forzar recarga.

---

## 10. Componente de notificaciones

### `src/components/notifications/NotificationList.tsx`

```tsx
const [notifications, setNotifications] = useState<Notification[]>([]);
const [filter, setFilter] = useState<'all' | 'unread' | 'reserve' | 'energy'>('all');
const [extendTarget, setExtendTarget] = useState<Notification | null>(null);
const [extendDate, setExtendDate] = useState('');
const [extendLoading, setExtendLoading] = useState(false);
const [resolving, setResolving] = useState<number | null>(null);
```

**Filtrado en el frontend:**
```tsx
const filtered = notifications.filter((n) => {
  if (filter === 'unread') return !n.is_read;
  if (filter === 'reserve') return n.type === 'reserve_no_contact';
  if (filter === 'energy') return n.type === 'negative_energy';
  return true;
});
```
El filtrado se hace sobre los datos ya cargados, sin volver a llamar al API. Esto es más rápido y evita llamadas innecesarias.

**Para notificaciones de tipo `reserve_no_contact`:** Aparecen dos botones adicionales:
- **Extender:** Abre un modal para elegir nueva fecha. Al confirmar, llama `PUT /notifications/:id/extend`
- **Eliminar reserva:** Llama `PUT /notifications/:id/resolve-reserve`, que cambia el circuito a inactivo y descarta la notificación

**`resolving: number | null`:** Guarda el ID de la notificación que se está procesando (eliminar reserva). Permite deshabilitar ese botón específico durante la operación, sin afectar los botones de otras notificaciones.

---

## 11. Componente de autenticación

### `src/components/auth/ProtectedRoute.tsx`

```tsx
export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) return <div className="flex ..."><Spinner size="lg" /></div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (allowedRoles && user && !allowedRoles.includes(user.role)) return <Navigate to="/" replace />;

  return <>{children}</>;
}
```

**Qué hace:** Envuelve rutas que requieren autenticación. Si el usuario no está logueado, redirige al login. Si no tiene el rol requerido, redirige al inicio.

**Por qué verificar `isLoading`:** Al recargar la página, `AuthContext` está verificando el token con el backend. Durante ese tiempo, `isAuthenticated` es `false` (aún no se sabe si está autenticado). Sin el check de `isLoading`, el usuario autenticado sería redirigido al login por error durante esa verificación.

**`replace` en `Navigate`:** Reemplaza la entrada actual en el historial del navegador en lugar de agregar una nueva. Así, al hacer "Atrás" desde el login no vuelve a la página protegida.

---

## 12. CSS Global y sistema de temas

### `src/index.css`

```css
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  --text-primary: #111827;
  --text-secondary: #6b7280;
  --border-color: #e5e7eb;
  --card-bg: #ffffff;
  --sidebar-bg: #111827;
  --sidebar-text: #f9fafb;
  --hover-bg: #f3f4f6;
}

.dark {
  --bg-primary: #1f2937;
  --bg-secondary: #111827;
  --text-primary: #f9fafb;
  --text-secondary: #9ca3af;
  --border-color: #374151;
  --card-bg: #1f2937;
  --hover-bg: #374151;
}
```

**Por qué CSS variables en lugar de solo Tailwind `dark:`:**
El sistema de temas usa variables CSS (`var(--bg-primary)`) en lugar del prefijo `dark:` de Tailwind. Esto se debe a que las variables CSS se pueden leer desde JavaScript y son más predecibles con componentes que definen estilos inline.

**Cómo funciona el cambio de tema:** `ThemeContext` agrega o quita la clase `dark` en el `<html>`. CSS aplica el segundo bloque de variables cuando existe esa clase. Todos los componentes que usan `var(--bg-primary)` automáticamente cambian de color.

**`@keyframes` y `animate-spin`:** El spinner usa la animación de rotación de Tailwind. Los modales usan `animate-in fade-in` para aparecer con transición suave.

**Scrollbar personalizado:**
```css
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background-color: var(--border-color); border-radius: 3px; }
```
Unifica el estilo del scrollbar en Chrome/Edge para que combine con el tema.

**Transición global:**
```css
* { transition: background-color 0.2s ease, border-color 0.2s ease, color 0.1s ease; }
```
Hace que el cambio de tema sea suave en toda la app sin configurarlo componente por componente.
