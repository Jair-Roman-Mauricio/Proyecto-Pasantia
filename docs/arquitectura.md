# Arquitectura del Sistema — Línea 1 Metro

## Stack Tecnológico

| Capa | Tecnología | Versión |
|------|------------|---------|
| **Frontend** | React + TypeScript | React 19, TS 5.9 |
| **Estilos** | Tailwind CSS | 4.2 |
| **Bundler** | Vite | 7.3 |
| **Estado/datos** | TanStack React Query | 5.x |
| **Backend** | FastAPI (Python) | 0.115+ |
| **ORM** | SQLAlchemy | 2.x |
| **Base de datos** | PostgreSQL | 15 |
| **Autenticación** | Supabase Auth (JWT ES256/RS256/HS256) | — |
| **Contenedores** | Docker + Docker Compose | — |
| **Web server** | nginx (reverse proxy) | alpine |

---

## Estructura de Carpetas

```
Linea1Mtro/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints REST (14 módulos)
│   │   ├── models/          # Modelos SQLAlchemy (11 tablas)
│   │   ├── schemas/         # Schemas Pydantic (validación)
│   │   ├── services/        # Lógica de negocio
│   │   ├── utils/           # Helpers (seguridad, DB, constantes)
│   │   ├── config.py        # Variables de entorno
│   │   ├── database.py      # Conexión PostgreSQL
│   │   ├── dependencies.py  # Auth y permisos
│   │   └── main.py          # App FastAPI + startup
│   ├── migrations/          # Migraciones Alembic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Componentes React por dominio
│   │   ├── pages/           # Páginas principales
│   │   ├── context/         # React Context (auth, theme, sidebar)
│   │   ├── services/        # Clientes Axios
│   │   ├── types/           # Tipos TypeScript
│   │   └── config/          # Axios base URL, constantes
│   └── package.json
├── nginx/
│   └── nginx.conf           # Reverse proxy + HTTPS
├── docs/                    # Esta documentación
├── docker-compose.yml
├── Dockerfile.backend
└── Dockerfile.frontend
```

---

## Modelo de Datos (Tablas)

### Jerarquía principal
```
Station (26)
  └── Bar (3 por estación: normal, emergency, continuity)
        └── Circuit (n por barra)
              └── SubCircuit (n por circuito)
```

### Tablas completas

| Tabla | Descripción | Campos clave |
|-------|-------------|--------------|
| `users` | Usuarios del sistema | `username`, `role` (admin/opersac), `status` |
| `permissions` | Permisos por feature por usuario | `user_id`, `feature_key`, `is_allowed` |
| `stations` | 26 estaciones E01-E26 | `code`, `name`, `transformer_capacity_kw`, `status` |
| `bars` | 3 barras por estación | `station_id`, `bar_type`, `capacity_kw`, `capacity_a` |
| `circuits` | Circuitos eléctricos | `bar_id`, `denomination`, `pi_kw`, `fd`, `md_kw`, `status`, `is_ups` |
| `sub_circuits` | Ampliaciones de circuitos | `circuit_id`, `pi_kw`, `fd`, `md_kw`, `status` |
| `requests` | Solicitudes OPERSAC | `opersac_user_id`, `station_id`, `bar_type`, `circuit_id`, `status` |
| `observations` | Observaciones técnicas | `circuit_id`, `bar_id`, `severity`, `content` |
| `notifications` | Alertas automáticas | `circuit_id`, `type`, `is_read`, `is_dismissed` |
| `audit_logs` | Log de auditoría | `user_id`, `action`, `entity_type`, `entity_id`, `details` |
| `backups` | Respaldos JSON | `created_by`, `file_name`, `backup_data`, `size_bytes` |

### Estados de Circuito

| Estado | Descripción |
|--------|-------------|
| `operative_normal` | En operación normal |
| `reserve_r` | En reserva sin equipar |
| `reserve_equipped_re` | En reserva equipada |
| `inactive` | Fuera de servicio |

### Cálculo de energía

- **MD kW** = `pi_kw × fd` (demanda máxima de un circuito)
- **Demanda estación** = suma de `md_kw` de todos los circuitos activos en sus barras
- **Disponible** = `transformer_capacity_kw - max_demand_kw`
- **Estado:**
  - `green` si disponible > 20% de la capacidad
  - `yellow` si disponible ≤ 20%
  - `red` si disponible ≤ 0

---

## Flujos Principales

### Flujo: Solicitud de ampliación

```
OPERSAC                   Backend                   Admin
  │                          │                         │
  ├─ POST /requests ─────────►                         │
  │  (status: pending)        │                         │
  │                          │── notifica admin ──────►│
  │                          │                         │
  │                          │◄── PUT /approve ────────┤
  │                          │                         │
  │            (si circuit_id) crea SubCircuit         │
  │            (si no)        crea Circuit             │
  │                          │                         │
  │                     recalcula energía              │
  │                          │                         │
  │◄─ status: approved ──────┤                         │
```

### Flujo: Reserva sin contacto

```
Scheduler (08:00 AM diario)
  │
  ├── consulta circuitos en reserve_r / reserve_equipped_re
  ├── verifica si reserve_expires_at está vencida
  ├── verifica si client_last_contact fue hace más de X días
  │
  └── si no hay contacto: crea Notification (type: reserve_no_contact)

Admin
  ├── ve badge en campana
  ├── abre notificación
  └── elige: Extender | Resolver (→ circuit.status = inactive) | Descartar
```

### Flujo: Autenticación

```
1. LoginPage llama a supabase.auth.signInWithPassword({ email, password })
   └── Supabase valida credenciales y devuelve { session: { access_token, ... } }

2. authService.getMe(access_token) → GET /api/v1/auth/me
   └── Backend decodifica el JWT (ES256/RS256 via JWKS o HS256 local)
   └── Busca el usuario en la BD por sub (UUID de Supabase)
   └── Devuelve { id, username, role, status, ... }

3. Si rol = opersac: GET /api/v1/permissions/me → carga permisos por feature
   └── Permisos se almacenan en AuthContext.user.permissions

4. Axios interceptor lee token de AuthContext y añade "Authorization: Bearer <token>"

5. Supabase renueva el token automáticamente (onAuthStateChange → TOKEN_REFRESHED)

6. Sidebar filtra opciones según rol y permisos (hasPermission())
```

---

## Variables de Entorno

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql://linea1user:linea1pass@db:5432/linea1metro
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...   # Admin API — mantener secreta
SUPABASE_JWT_SECRET=super-secret-jwt    # Solo para HS256 local; en producción usa JWKS
STORAGE_PATH=storage
CORS_ORIGINS=["http://localhost", "https://tu-dominio.duckdns.org"]
PROJECT_NAME=Linea1Metro-API
API_V1_PREFIX=/api/v1
```

### Base de datos (`docker-compose.yml` / `.env` raíz)

```env
POSTGRES_USER=linea1user
POSTGRES_PASSWORD=linea1pass
POSTGRES_DB=linea1metro
```

---

## Despliegue con Docker

```bash
# Construir y levantar todos los servicios
docker compose up -d --build

# Ver estado de los contenedores
docker compose ps

# Ver logs en tiempo real
docker compose logs -f

# Reiniciar un servicio
docker compose restart backend
```

**Servicios:**
- `db` — PostgreSQL 15 (puerto 5432, interno)
- `backend` — FastAPI en uvicorn (puerto 8000, interno)
- `frontend` — React + nginx (puertos 80 / 443, externo)

---

## Datos Iniciales (Seed)

Al iniciar el backend por primera vez, se crean automáticamente:

- **1 usuario admin** en Supabase Auth + en la BD local (si no existe ningún admin)
- **26 estaciones** (E01 Villa El Salvador → E26 Bayóvar)
- **78 barras** (3 por estación: normal, emergency, continuity)
- Capacidad inicial del transformador: **500 kW** por estación

---

## Documentación interactiva

Con el sistema corriendo, acceder a:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/api/v1/openapi.json`
