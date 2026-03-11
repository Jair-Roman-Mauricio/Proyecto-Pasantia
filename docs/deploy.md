# Guía de Despliegue — Sistema de Gestión Energética · Línea 1 Metro

> **Versión del sistema:** 1.1.8
> **Mantenedor:** Área de TI / Infraestructura

---

## Tabla de contenidos

1. [Arquitectura del sistema](#1-arquitectura-del-sistema)
2. [Requisitos del servidor](#2-requisitos-del-servidor)
3. [Configuración de la base de datos](#3-configuración-de-la-base-de-datos)
   - [Opción A — Supabase Cloud (recomendada)](#opción-a--supabase-cloud-recomendada)
   - [Opción B — Supabase Self-Hosted](#opción-b--supabase-self-hosted)
   - [Opción C — PostgreSQL local en Docker](#opción-c--postgresql-local-en-docker)
4. [Variables de entorno](#4-variables-de-entorno)
5. [Despliegue con Docker (recomendado)](#5-despliegue-con-docker-recomendado)
6. [Despliegue bare metal / VM](#6-despliegue-bare-metal--vm)
7. [Operaciones del día a día](#7-operaciones-del-día-a-día)
8. [Actualizar el sistema](#8-actualizar-el-sistema)
9. [Backup y restauración](#9-backup-y-restauración)
10. [Seguridad](#10-seguridad)
11. [Solución de problemas](#11-solución-de-problemas)

---

## 1. Arquitectura del sistema

| Componente | Tecnología | Puerto (desarrollo) |
|------------|-----------|---------------------|
| Frontend | React 19 + Vite + TypeScript → compilado y servido por nginx | 5173 |
| Backend | FastAPI + Uvicorn + Python 3.10 | 8000 |
| Base de datos | PostgreSQL 15+ (Supabase o local) | 5432 |
| Scheduler | APScheduler (embebido en el backend, sin puerto propio) | — |
| Almacenamiento | Sistema de archivos local (imágenes de estaciones) | — |

```
Usuario → nginx (80/443) ─┬─► /         → React SPA (frontend/dist/)
                           └─► /api/     → FastAPI (backend:8000)
                                              │
                                              ▼
                                    Base de datos (Supabase / PostgreSQL)
```

---

## 2. Requisitos del servidor

### Para despliegue Docker

| Recurso | Mínimo recomendado |
|---------|-------------------|
| SO | Linux Ubuntu 22.04+ / Debian 12 / Rocky Linux 9+ |
| CPU | 2 vCPU |
| RAM | 4 GB |
| Disco | 20 GB (código + imágenes almacenadas) |
| Software | Docker 24+ y Docker Compose 2+ |
| Red | Acceso a la intranet; internet solo en instalación inicial |

Para instalar Docker en Linux:
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # permite usar docker sin sudo
newgrp docker
```

### Para despliegue bare metal

| Recurso | Requerido |
|---------|-----------|
| Python | 3.10 o 3.11 |
| Node.js | 20 LTS (solo para compilar el frontend, no en producción) |
| nginx | Cualquier versión reciente |
| PostgreSQL | 15+ (o usar Supabase como BD externa) |

---

## 3. Configuración de la base de datos

El sistema soporta tres modos de base de datos. La selección se hace exclusivamente a través de la variable `DATABASE_URL` en el archivo `backend/.env`. **El backend crea las tablas automáticamente al iniciar** — no se requieren migraciones manuales.

---

### Opción A — Supabase Cloud (recomendada)

Supabase es una plataforma PostgreSQL gestionada en la nube. No requiere administrar ningún servidor de base de datos.

#### Paso 1 — Crear el proyecto en Supabase

1. Ir a [supabase.com](https://supabase.com) y crear una cuenta gratuita
2. Crear un nuevo proyecto:
   - **Name:** `linea1metro` (o el nombre que prefiera)
   - **Database Password:** elegir una contraseña fuerte — **guardarla**, no se puede recuperar
   - **Region:** elegir la más cercana geográficamente (ej: `South America (São Paulo)`)
3. Esperar ~2 minutos a que el proyecto se aprovisione

#### Paso 2 — Obtener la cadena de conexión

1. En el dashboard de Supabase, ir a **Settings → Database**
2. En la sección **Connection string**, seleccionar la pestaña **URI**
3. Elegir el modo de conexión:

| Modo | Puerto | Cuándo usarlo |
|------|--------|---------------|
| **Session mode** (Direct) | `5432` | Recomendado para este sistema — conexiones persistentes con SQLAlchemy |
| Transaction mode (Pooler) | `6543` | Solo si se necesita escalar a muchos usuarios concurrentes |

4. Copiar la URI. Tiene el formato:
```
postgresql://postgres.XXXX:[TU-PASSWORD]@aws-0-REGION.pooler.supabase.com:5432/postgres
```

#### Paso 3 — Configurar `DATABASE_URL`

Agregar la URI al archivo `backend/.env` con `?sslmode=require`:

```env
DATABASE_URL=postgresql://postgres.XXXX:TU-PASSWORD@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require
```

> **`?sslmode=require`** es obligatorio para conectar a Supabase Cloud. Sin él la conexión se rechaza.

#### Notas importantes de Supabase Cloud

- El plan gratuito permite hasta **500 MB** de almacenamiento y **2 proyectos activos**
- El proyecto se **pausa automáticamente** tras 7 días de inactividad en el plan gratuito — para evitarlo, usar el plan Pro o configurar una tarea cron para hacer ping a la DB cada día
- Los backups automáticos están incluidos en todos los planes
- El endpoint `/backups/pgdump/download` funciona con Supabase siempre que el contenedor Docker tenga `postgresql-client` instalado (ya está incluido en `Dockerfile.backend`)

---

### Opción B — Supabase Self-Hosted

Instalar Supabase en los propios servidores de la empresa para mantener los datos en la intranet.

#### Requisitos
- Docker instalado en el servidor de base de datos
- Mínimo 4 GB RAM, 2 vCPU dedicados para Supabase

#### Instalación

```bash
# Clonar el repositorio oficial de Supabase
git clone --depth 1 https://github.com/supabase/supabase
cd supabase/docker

# Copiar la configuración
cp .env.example .env
nano .env   # cambiar POSTGRES_PASSWORD, JWT_SECRET, ANON_KEY, SERVICE_ROLE_KEY

# Levantar Supabase
docker compose up -d
```

#### Cadena de conexión (Self-Hosted)

```env
DATABASE_URL=postgresql://postgres:TU-PASSWORD@IP-SERVIDOR-SUPABASE:5432/postgres
```

No requiere `?sslmode=require` a menos que se configure SSL explícitamente en la instalación self-hosted.

---

### Opción C — PostgreSQL local en Docker

Para entornos donde no se puede usar Supabase y se prefiere todo en el mismo servidor.

Al usar `docker compose --profile local`, se levanta un contenedor PostgreSQL gestionado por Docker Compose.

```env
# backend/.env para PostgreSQL local en Docker
DATABASE_URL=postgresql://postgres:TU-PASSWORD@db:5432/linea1metro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=TU-PASSWORD
```

> **Importante:** El host debe ser `db` (nombre del servicio en docker-compose.yml), **no** `localhost`.

Ver [Sección 5](#5-despliegue-con-docker-recomendado) para los comandos de arranque con este perfil.

---

## 4. Variables de entorno

Crear el archivo `backend/.env` copiando la plantilla:

```bash
cp backend/.env.example backend/.env
```

Contenido completo de `backend/.env` para producción:

```env
# ── BASE DE DATOS ──────────────────────────────────────────────────
# Elegir una de las tres opciones de la Sección 3 de esta guía:

# Supabase Cloud (Session mode, puerto 5432):
DATABASE_URL=postgresql://postgres.XXXX:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?sslmode=require

# Supabase Self-Hosted:
# DATABASE_URL=postgresql://postgres:PASSWORD@IP-SUPABASE:5432/postgres

# PostgreSQL local en Docker (perfil local):
# DATABASE_URL=postgresql://postgres:PASSWORD@db:5432/linea1metro

# ── JWT ────────────────────────────────────────────────────────────
# Generar con: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=REEMPLAZAR_CON_CLAVE_ALEATORIA_DE_64_CARACTERES
ACCESS_TOKEN_EXPIRE_MINUTES=480

# ── CORS ───────────────────────────────────────────────────────────
# IP o nombre de host del servidor donde corre el frontend en producción
CORS_ORIGINS=["http://192.168.1.50"]
# Con HTTPS: CORS_ORIGINS=["https://servidor-linea1.empresa.local"]

# ── Almacenamiento de imágenes ──────────────────────────────────────
STORAGE_PATH=/app/storage
MAX_IMAGE_SIZE_MB=10

# ── Solo para PostgreSQL local (--profile local) ───────────────────
POSTGRES_USER=postgres
POSTGRES_PASSWORD=TU-PASSWORD-POSTGRES
```

### Generar `SECRET_KEY`

```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Ejemplo de salida:
# a3f8c2d1e4b5a6f7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1
```

---

## 5. Despliegue con Docker (recomendado)

### Estructura de archivos Docker

```
proyecto/
├── Dockerfile.backend          ← imagen Python 3.10 + FastAPI
├── Dockerfile.frontend         ← build React + nginx alpine
├── docker-compose.yml          ← orquestación de servicios
├── .dockerignore               ← excluye node_modules, .env, tests, etc.
├── nginx/
│   └── nginx.conf              ← reverse proxy + SPA routing + HTTPS opcional
└── backend/
    ├── .env                    ← variables de producción (NO commitear)
    └── .env.example            ← plantilla de referencia
```

### Modos de arranque

#### Modo Supabase (default) — solo backend + frontend

```bash
# Requiere DATABASE_URL en backend/.env apuntando a Supabase
docker compose up -d --build
```

Levanta 2 servicios: `backend` + `frontend`. La BD es externa (Supabase).

#### Modo PostgreSQL local

```bash
# Requiere POSTGRES_USER, POSTGRES_PASSWORD y DATABASE_URL con host=db en backend/.env
docker compose --profile local up -d --build
```

Levanta 3 servicios: `db` (PostgreSQL) + `backend` + `frontend`.

---

### Primer arranque — paso a paso

**1. Copiar el proyecto al servidor**

```bash
# Opción A: desde USB / disco externo
cp -r /media/usb/Linea1Mtro-CludeCodePlan /opt/linea1metro

# Opción B: desde git
git clone <url-del-repositorio> /opt/linea1metro
```

**2. Crear el archivo `.env`**

```bash
cd /opt/linea1metro
cp backend/.env.example backend/.env
nano backend/.env   # editar con los valores reales
```

**3. Construir y levantar**

```bash
# Con Supabase:
docker compose up -d --build

# Con PostgreSQL local:
docker compose --profile local up -d --build
```

La primera vez descarga imágenes base (~500 MB) e instala dependencias. Puede tardar 5–10 minutos según la velocidad de internet.

**4. Verificar el arranque**

```bash
docker compose ps
```

Salida esperada (modo Supabase):
```
NAME                     STATUS          PORTS
linea1metro-backend-1    running
linea1metro-frontend-1   running         0.0.0.0:80->80/tcp
```

```bash
docker compose logs backend
# Debe aparecer al final:
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**5. Acceder al sistema**

Abrir en cualquier navegador de la red interna:
```
http://192.168.1.50
```
(reemplazar con la IP real del servidor)

**Credenciales iniciales:** `admin` / `admin123`
> Cambiar la contraseña del admin **inmediatamente** después del primer login.

---

## 6. Despliegue bare metal / VM

Para servidores donde no se puede instalar Docker.

### Prerrequisitos

```bash
# Python 3.10
sudo apt install python3.10 python3.10-venv python3-pip

# Node.js 20 (solo para compilar el frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs

# nginx
sudo apt install nginx

# postgresql-client (solo para el endpoint pg_dump/download)
sudo apt install postgresql-client
```

### Backend

```bash
cd /opt/linea1metro/backend

python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env   # editar con valores de producción

# Verificar arranque
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Servicio systemd (mantener el backend corriendo)

```ini
# /etc/systemd/system/linea1metro.service
[Unit]
Description=Linea 1 Metro - Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/linea1metro/backend
EnvironmentFile=/opt/linea1metro/backend/.env
ExecStart=/opt/linea1metro/backend/venv/bin/uvicorn app.main:app \
          --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable linea1metro
sudo systemctl start linea1metro
```

### Frontend (compilar)

```bash
cd /opt/linea1metro/frontend
npm ci
npm run build
# Resultado en frontend/dist/
```

### nginx

```nginx
# /etc/nginx/sites-available/linea1metro
server {
    listen 80;
    server_name 192.168.1.50;   # IP o hostname interno

    root /opt/linea1metro/frontend/dist;
    index index.html;

    gzip on;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy al backend
    location /api/ {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/linea1metro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 7. Operaciones del día a día

### Docker

```bash
cd /opt/linea1metro

# Iniciar (si se reinició el servidor y los contenedores no arrancaron solos)
docker compose up -d

# Detener
docker compose down

# Ver logs en tiempo real
docker compose logs -f backend

# Reiniciar un servicio específico
docker compose restart backend
docker compose restart frontend

# Ver uso de CPU/memoria
docker stats
```

### Bare metal

```bash
# Estado del servicio
sudo systemctl status linea1metro

# Reiniciar
sudo systemctl restart linea1metro

# Logs en tiempo real
sudo journalctl -u linea1metro -f
```

---

## 8. Actualizar el sistema

Cuando haya una nueva versión del código:

### Docker

```bash
cd /opt/linea1metro

# Obtener cambios
git pull   # o copiar los archivos nuevos manualmente

# Reconstruir y reiniciar
docker compose up -d --build
# (o con perfil local: docker compose --profile local up -d --build)
```

Docker solo reconstruye las capas que cambiaron. Los datos y archivos almacenados se conservan.

### Bare metal

```bash
cd /opt/linea1metro

# Obtener cambios
git pull

# Reinstalar dependencias si requirements.txt cambió
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Recompilar frontend si hay cambios en frontend/
cd ../frontend
npm ci && npm run build

# Reiniciar el backend
sudo systemctl restart linea1metro
```

---

## 9. Backup y restauración

El sistema incluye un módulo de backup integrado accesible desde el panel de administración (Sección Backups). Adicionalmente, se puede hacer backup directo a la base de datos:

### Backup manual con Docker

```bash
# Backup del volumen PostgreSQL (solo modo --profile local)
docker compose exec db pg_dump -U postgres linea1metro > backup_$(date +%Y%m%d_%H%M).sql

# Backup vía el endpoint de la API (genera JSON con todos los datos)
# Disponible en el panel admin → Backups → Crear Backup
```

### Backup de Supabase

Supabase Cloud realiza backups automáticos diarios. Para exportar manualmente:

1. Dashboard Supabase → **Database** → **Backups** → descargar
2. O usar el endpoint `GET /api/v1/backups/pgdump/download` desde el panel admin — genera un `.sql` completo usando `pg_dump` contra la BD de Supabase

### Restaurar un backup JSON (desde el panel admin)

1. Panel admin → **Backups** → seleccionar backup → **Restaurar**
2. Confirmar la acción (es destructiva e irreversible)

### Restaurar un backup SQL

```bash
# Con Docker (modo local)
cat backup_20260311.sql | docker compose exec -T db psql -U postgres linea1metro

# Sin Docker
psql -U postgres linea1metro < backup_20260311.sql
```

### Backup automático con cron (bare metal o servidor host)

```bash
crontab -e

# Backup diario a las 02:00
0 2 * * * cd /opt/linea1metro && docker compose exec -T db pg_dump -U postgres linea1metro > /var/backups/linea1metro_$(date +\%Y\%m\%d).sql
```

---

## 10. Seguridad

| Acción | Prioridad |
|--------|-----------|
| Cambiar contraseña del admin (`admin` / `admin123`) inmediatamente tras el primer login | **CRÍTICO** |
| Generar `SECRET_KEY` de 64 caracteres aleatorios y único por entorno | **CRÍTICO** |
| Nunca commitear `backend/.env` al repositorio | **CRÍTICO** |
| Usar HTTPS (certificado interno de la empresa o Let's Encrypt) | Alta |
| Restringir el acceso al puerto 80/443 solo a la red interna (firewall) | Alta |
| No exponer el puerto 8000 del backend directamente — solo a través de nginx | Alta |
| En Supabase: activar Row Level Security (RLS) si se habilita el acceso directo desde el frontend | Media |
| Rotación periódica de contraseñas | Media |

### Configurar HTTPS

Descomentar el bloque HTTPS en `nginx/nginx.conf` y ajustar las rutas de los certificados:

```nginx
server {
  listen 443 ssl;
  ssl_certificate     /etc/ssl/certs/linea1metro.crt;
  ssl_certificate_key /etc/ssl/private/linea1metro.key;
  # ... (ver nginx/nginx.conf para el bloque completo)
}
```

Actualizar `CORS_ORIGINS` en `.env`:
```env
CORS_ORIGINS=["https://servidor-linea1.empresa.local"]
```

---

## 11. Solución de problemas

### El sistema no carga en el navegador

```bash
# 1. Verificar contenedores
docker compose ps

# 2. Verificar que el puerto 80 no está bloqueado
sudo ufw allow 80/tcp       # Ubuntu
sudo firewall-cmd --add-port=80/tcp --permanent && sudo firewall-cmd --reload  # Rocky/RHEL
```

### Error de conexión a la base de datos

```bash
docker compose logs backend
# Buscar: "could not connect to server" o "FATAL: password authentication failed"
```

Causas frecuentes:
- `DATABASE_URL` con host incorrecto (`localhost` en vez de `db` para modo Docker local)
- Falta `?sslmode=require` en la URL de Supabase Cloud
- Contraseña incorrecta en la URL
- Proyecto Supabase pausado (plan gratuito tras 7 días de inactividad)

### El backend arranca pero las tablas no existen

Al primer arranque, el backend crea las tablas automáticamente. Si no lo hace:
```bash
docker compose logs backend | grep "error\|ERROR\|Exception"
```

Verificar que la `DATABASE_URL` es accesible desde dentro del contenedor.

### Error 502 Bad Gateway en `/api/`

El frontend cargó pero nginx no puede llegar al backend:
```bash
docker compose restart backend
docker compose logs backend
```

### Error al construir el frontend (`npm run build` falla)

```bash
docker compose logs frontend
# Si falla por falta de memoria durante el build:
# Agregar al docker-compose.yml en el servicio frontend:
#   build:
#     args:
#       NODE_OPTIONS: "--max-old-space-size=2048"
```

### Reiniciar todo desde cero (sin perder datos)

```bash
docker compose down
docker compose up -d --build   # o con --profile local
```

### Reiniciar todo incluyendo la base de datos (⚠ BORRA TODOS LOS DATOS)

```bash
docker compose down -v   # -v elimina los volúmenes Docker
docker compose --profile local up -d --build
```

---

## Evaluación del estado de los archivos Docker (v1.1.8)

Los archivos Docker actuales están **al día** y no requieren modificaciones para la versión 1.1.8. A continuación el razonamiento:

| Archivo | Estado | Observación |
|---------|--------|-------------|
| `Dockerfile.backend` | ✅ Sin cambios | Instala `postgresql-client` (necesario para el endpoint `pg_dump/download` del módulo de Backups) |
| `Dockerfile.frontend` | ✅ Sin cambios | Build React + nginx; no depende de librerías del SO |
| `docker-compose.yml` | ✅ Sin cambios | Arquitectura con perfiles ya implementada (Supabase default / PostgreSQL local con `--profile local`) |
| `nginx/nginx.conf` | ✅ Sin cambios | Gzip habilitado, SPA routing correcto, bloque HTTPS comentado listo para activar |
| `.dockerignore` | ✅ Sin cambios | Excluye correctamente `tests/`, `node_modules/`, `.env` y `*.md` |
| `backend/requirements.txt` | ✅ Sin cambios | Todas las dependencias nuevas (openpyxl, reportlab, apscheduler, Pillow) ya estaban declaradas |

Las adiciones de código en esta versión (módulo de backups con `pg_dump`, notificaciones, reportes, imágenes) no requieren nuevas dependencias de sistema ni cambios en la infraestructura Docker.
