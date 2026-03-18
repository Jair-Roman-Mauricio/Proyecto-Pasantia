# Backend — Sistema de Gestión Energética · Línea 1 Metro de Lima

API REST construida con **FastAPI** para administrar la infraestructura eléctrica de las 26 estaciones de la Línea 1 del Metro de Lima.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Framework web | FastAPI 0.115 |
| Base de datos | PostgreSQL (producción) · SQLite en memoria (tests) |
| ORM | SQLAlchemy 2.0 |
| Autenticación | Supabase Auth (JWT ES256/RS256/HS256) |
| Validación | Pydantic v2 |
| Programador de tareas | APScheduler 3.10 |
| Testing | pytest + pytest-asyncio + httpx |

---

## Jerarquía de datos

```
Estación (26 en total: E01 Villa El Salvador → E26 Bayóvar)
└── Barra (3 por estación: normal · emergency · continuity)
    └── Circuito
        └── Sub-circuito
```

La demanda máxima (MD = PI × FD) de cada circuito y sub-circuito se suma para calcular el estado energético de la estación: **green** (≥20% disponible) · **yellow** (<20%) · **red** (demanda > capacidad).

---

## Roles de usuario

| Rol | Descripción |
|---|---|
| `admin` | Acceso total: gestión de circuitos, aprobación de solicitudes, backups, auditoría |
| `opersac` | Acceso limitado por permisos: ver estaciones, enviar solicitudes, ver reportes |

Los permisos de los usuarios `opersac` se controlan por feature: `view_stations`, `view_circuits`, `send_requests`, `add_observations`, `view_reports`.

---

## Requisitos previos

- Python 3.11+
- PostgreSQL 14+
- Proyecto en [Supabase](https://supabase.com) (Auth habilitado)

---

## Instalación

```bash
# 1. Clonar y entrar al directorio
cd backend

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con los valores reales (ver sección Variables de entorno)
```

---

## Variables de entorno

Copiar `.env.example` a `.env` y completar:

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Cadena de conexión PostgreSQL · ej: `postgresql://user:pass@host:5432/db` |
| `SUPABASE_URL` | URL del proyecto Supabase · ej: `https://xxxx.supabase.co` |
| `SUPABASE_ANON_KEY` | Clave anónima pública de Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Clave de servicio (Admin API) — mantener secreta |
| `SUPABASE_JWT_SECRET` | Solo para HS256 local; en producción se usa JWKS automáticamente |
| `STORAGE_PATH` | Ruta local para guardar imágenes y backups · defecto: `storage` |
| `CORS_ORIGINS` | Lista de orígenes permitidos · ej: `["http://localhost:5173"]` |

---

## Comandos de desarrollo

```bash
# Servidor de desarrollo (recarga automática)
uvicorn app.main:app --reload --port 8000

# Documentación interactiva (Swagger UI)
# http://localhost:8000/docs

# Documentación alternativa (ReDoc)
# http://localhost:8000/redoc
```

---

## Testing

Los tests usan **SQLite en memoria** y **mocks de Supabase Auth** — no requieren conexión a PostgreSQL ni a Supabase.

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Solo un módulo
python -m pytest tests/test_energy_flows.py -v

# Salida compacta sin warnings
python -m pytest tests/ -q --no-header -p no:warnings
```

### Cobertura de tests (76 tests)

| Módulo | Tests |
|---|---|
| Autenticación (`test_auth.py`) | Token válido, sin token, expirado, inactivo |
| Usuarios (`test_users.py`) | CRUD, duplicados, roles |
| Estaciones (`test_stations.py`) | Listar, permisos, actualizar capacidad |
| Barras (`test_bars.py`) | Listar, resumen de potencia, actualizar capacidad |
| Circuitos (`test_circuits.py`) | CRUD, cascade delete, recalculo MD |
| Sub-circuitos (`test_sub_circuits.py`) | CRUD, cambio de estado, fechas de reserva |
| Solicitudes (`test_requests.py`) | Crear, aprobar, rechazar, flujos de estado |
| Permisos (`test_permissions.py`) | Leer/escribir permisos por usuario |
| Flujos energéticos (`test_energy_flows.py`) | green/yellow/red, inactivos, sub-circuitos |
| Integración (`test_integration.py`) | Flujos end-to-end completos |

---

## Estructura de carpetas

```
backend/
├── app/
│   ├── main.py                 # Punto de entrada FastAPI, startup, CORS
│   ├── config.py               # Settings desde variables de entorno
│   ├── database.py             # Engine SQLAlchemy, sesión, Base
│   ├── dependencies.py         # get_current_user, require_admin, check_permission
│   ├── api/
│   │   └── v1/                 # Endpoints REST (auth, users, stations, bars, circuits…)
│   ├── models/                 # Modelos SQLAlchemy (tablas de la BD)
│   ├── schemas/                # Schemas Pydantic (validación request/response)
│   ├── services/
│   │   ├── energy_calculator.py    # Recalculo de demanda y estado por estación
│   │   ├── audit_service.py        # Registro de acciones en el log de auditoría
│   │   ├── notification_service.py # Notificaciones automáticas de reservas
│   │   └── image_service.py        # Gestión de imágenes (redimensionado, storage)
│   └── utils/
│       ├── security.py         # Decodificación de tokens JWT de Supabase
│       ├── supabase_admin.py   # Llamadas a la Admin API de Supabase
│       ├── db_helpers.py       # safe_commit (manejo de errores de BD)
│       ├── constants.py        # Estaciones, tipos de barra, features de permisos
│       └── enums.py            # Enums de estados y tipos
├── tests/                      # Suite de tests (pytest)
├── docs/                       # Documentación adicional
├── conftest.py                 # Configuración de pytest (env vars, patches)
├── pyproject.toml              # Configuración de pytest
├── requirements.txt            # Dependencias Python
└── .env.example                # Plantilla de variables de entorno
```

---

## Proceso de deployment (Docker)

```bash
# Construir imagen
docker build -t linea1metro-backend .

# Ejecutar con variables de entorno
docker run -p 8000:8000 --env-file .env linea1metro-backend
```

Las tablas se crean automáticamente al iniciar (`Base.metadata.create_all`). El usuario admin por defecto se crea en Supabase Auth si no existe ningún admin en la BD.
