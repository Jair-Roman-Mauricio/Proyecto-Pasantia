# Plan de Despliegue — Linea 1 Metro Sistema de Gestión Energética

> **Estado:** Pendiente de implementación
> **Propósito:** Hostear el sistema en servidores internos de la empresa
> **Versión del sistema:** V.1.1.3

---

## Arquitectura del sistema actual

| Componente   | Tecnología                       | Puerto dev |
|--------------|----------------------------------|------------|
| Frontend     | React 19 + Vite + TypeScript     | 5173       |
| Backend      | FastAPI + Uvicorn + Python 3.10  | 8000       |
| Base de datos| PostgreSQL 16                    | 5432       |
| Scheduler    | APScheduler (corre dentro del backend) | —   |

---

## Opciones de despliegue

### Opción A — Docker + docker-compose (Recomendada)
**Ideal si el servidor ya tiene Docker instalado o se puede instalar.**
Ventajas: portable, reproducible, fácil de actualizar y rollback.

### Opción B — Instalación directa (Bare metal / VM)
**Ideal si la empresa no permite Docker o si el servidor ya tiene Python/PostgreSQL instalados.**
Ventajas: sin dependencia de Docker, más transparente para el área de infraestructura.

---

## Requisitos del servidor

| Recurso      | Mínimo recomendado      |
|--------------|-------------------------|
| SO           | Linux (Ubuntu 22.04 / Rocky Linux 8+) o Windows Server 2019+ |
| CPU          | 2 vCPU                  |
| RAM          | 4 GB                    |
| Disco        | 20 GB (datos + backups) |
| Red          | Acceso interno a la intranet; no requiere salida a internet una vez instalado |

---

## Opción A — Docker + docker-compose

### Archivos a crear (no crear aún)

```
proyecto/
├── Dockerfile.backend          ← imagen Python para FastAPI
├── Dockerfile.frontend         ← imagen Node para build + Nginx para servir
├── docker-compose.yml          ← orquestación de los 3 servicios
├── nginx/
│   └── nginx.conf              ← reverse proxy + servir frontend
├── backend/
│   └── .env                    ← variables de entorno (NO commitear)
└── .dockerignore
```

### Contenido de cada archivo (a implementar)

#### `Dockerfile.backend`
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### `Dockerfile.frontend`
```dockerfile
# Etapa 1: build
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json .
RUN npm ci
COPY frontend/ .
RUN npm run build

# Etapa 2: servir con nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

#### `docker-compose.yml`
```yaml
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    restart: always
    env_file: backend/.env
    environment:
      POSTGRES_DB: linea1metro
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    restart: always
    env_file: backend/.env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - storage_data:/app/storage

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    restart: always
    ports:
      - "80:80"      # acceso HTTP en la intranet
      # - "443:443"  # descomentar si se configura HTTPS
    depends_on:
      - backend

volumes:
  postgres_data:
  storage_data:
```

#### `nginx/nginx.conf`
```nginx
events {}
http {
  include mime.types;

  server {
    listen 80;
    server_name _;            # reemplazar con IP o hostname interno
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing — todas las rutas van a index.html
    location / {
      try_files $uri $uri/ /index.html;
    }

    # Proxy al backend
    location /api/ {
      proxy_pass         http://backend:8000;
      proxy_http_version 1.1;
      proxy_set_header   Host $host;
      proxy_set_header   X-Real-IP $remote_addr;
    }

    # WebSockets (si se usan)
    location /ws/ {
      proxy_pass         http://backend:8000;
      proxy_http_version 1.1;
      proxy_set_header   Upgrade $http_upgrade;
      proxy_set_header   Connection "upgrade";
    }
  }
}
```

### Variables de entorno — `backend/.env` (a crear)
```env
# Base de datos
DATABASE_URL=postgresql://linea1user:CAMBIAR_PASSWORD@db:5432/linea1metro
POSTGRES_USER=linea1user
POSTGRES_PASSWORD=CAMBIAR_PASSWORD

# Seguridad JWT — generar con: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=REEMPLAZAR_CON_CLAVE_ALEATORIA_DE_64_CARACTERES

# CORS — reemplazar con la IP/hostname del servidor en la intranet
CORS_ORIGINS=["http://192.168.X.X", "http://nombre-servidor"]

# Tokens
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Almacenamiento de archivos (dentro del contenedor)
STORAGE_PATH=/app/storage
```

### Modificaciones necesarias en el código existente
Antes de dockerizar hay que hacer que el backend lea la config desde variables de entorno (ya está preparado con Pydantic Settings, solo necesita el `.env`). También hay que actualizar el `vite.config.ts` del frontend para producción:

```ts
// vite.config.ts — en producción el proxy no aplica (nginx lo maneja)
// Solo asegurarse que VITE_API_URL no esté hardcodeado en los servicios
```

### Comandos de despliegue (Opción A)
```bash
# Primera vez
docker compose up -d --build

# Ver logs
docker compose logs -f backend

# Actualizar a nueva versión del código
git pull
docker compose up -d --build

# Rollback (volver a imagen anterior)
docker compose down
git checkout <commit-anterior>
docker compose up -d --build
```

---

## Opción B — Instalación directa (sin Docker)

### Prerrequisitos a instalar en el servidor
1. **PostgreSQL 16** — instalar y crear base de datos `linea1metro`
2. **Python 3.10 o 3.11** — instalar y crear virtualenv
3. **Node.js 20 LTS** — solo para el build inicial (no se necesita en producción)
4. **nginx** — para servir el frontend y hacer reverse proxy

### Paso 1 — Base de datos
```sql
-- Ejecutar en psql como superusuario
CREATE USER linea1user WITH PASSWORD 'CAMBIAR_PASSWORD';
CREATE DATABASE linea1metro OWNER linea1user;
GRANT ALL PRIVILEGES ON DATABASE linea1metro TO linea1user;
```

### Paso 2 — Backend
```bash
cd /opt/linea1metro/backend

# Crear virtualenv
python3.10 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo de entorno
cp .env.example .env   # (crear .env.example primero como plantilla)
# editar .env con los valores de producción

# Verificar que la app arranca
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Paso 3 — Configurar systemd (mantener el backend corriendo)
```ini
# /etc/systemd/system/linea1metro.service
[Unit]
Description=Linea 1 Metro Backend
After=network.target postgresql.service

[Service]
User=linea1metro
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
systemctl enable linea1metro
systemctl start linea1metro
```

### Paso 4 — Frontend (build)
```bash
cd /opt/linea1metro/frontend
npm ci
npm run build
# El resultado queda en frontend/dist/
```

### Paso 5 — nginx (Opción B)
```nginx
# /etc/nginx/sites-available/linea1metro
server {
    listen 80;
    server_name 192.168.X.X;   # IP interna del servidor

    root /opt/linea1metro/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
    }
}
```

---

## Cambios obligatorios antes de cualquier despliegue

### 1. `backend/app/config.py` — valores por defecto inseguros
```python
# ACTUAL (inseguro):
SECRET_KEY: str = "your-secret-key-change-in-production"
DATABASE_URL: str = "postgresql://postgres:12345@localhost:5432/linea1metro"

# PRODUCCIÓN: deben venir del .env, nunca hardcodeados
```

### 2. `backend/app/database.py`
Verificar que la `DATABASE_URL` se lee desde `settings` (config.py) y no está hardcodeada. Si está fija, moverla a settings.

### 3. `frontend/src/services/` — URL del API
En producción, el frontend y el backend están en el mismo origen (nginx hace el proxy), por lo que la URL base `/api/v1` funciona sin cambios. Solo hay que asegurarse de que ningún servicio tenga `http://localhost:8000` hardcodeado.

### 4. CORS
Actualizar `CORS_ORIGINS` en `.env` con la IP/hostname real del servidor interno.

---

## Seguridad interna (recomendaciones)

| Acción | Prioridad |
|--------|-----------|
| Cambiar contraseña del admin por defecto (`admin` / `admin123`) | **CRÍTICO** |
| Generar `SECRET_KEY` de 64 caracteres aleatorios | **CRÍTICO** |
| Usar usuario PostgreSQL dedicado (no `postgres`) | Alta |
| Habilitar HTTPS con certificado interno (Let's Encrypt interno o self-signed) | Alta |
| Restringir acceso a la app solo a la red interna (firewall/iptables) | Media |
| Rotación de contraseñas periódica | Media |
| No exponer el puerto 8000 directamente — solo nginx en puerto 80/443 | Alta |

---

## Estrategia de actualización del sistema

```
1. git pull   (descargar cambios)
2. Si hay cambios en backend/requirements.txt → reinstalar dependencias
3. Si hay cambios en la BD → ejecutar: alembic upgrade head
4. Rebuild del frontend si hay cambios en frontend/
5. Reiniciar el backend: systemctl restart linea1metro (Opción B)
                     o: docker compose up -d --build (Opción A)
```

---

## Backup de la base de datos

```bash
# Backup manual
pg_dump -U linea1user linea1metro > backup_$(date +%Y%m%d_%H%M).sql

# Backup automático con cron (diario a las 02:00)
0 2 * * * pg_dump -U linea1user linea1metro > /backups/linea1metro_$(date +\%Y\%m\%d).sql

# Restaurar
psql -U linea1user linea1metro < backup_20260224_0200.sql
```

---

## Resumen — Qué hay que hacer cuando llegue el momento

1. **Decidir** entre Opción A (Docker) u Opción B (directo) según lo que permita infraestructura
2. **Preparar el servidor** (instalar dependencias según la opción elegida)
3. **Crear `backend/.env`** con los valores de producción (SECRET_KEY, DATABASE_URL, CORS)
4. **Verificar** que ninguna URL esté hardcodeada a `localhost` en el código del frontend
5. **Crear los archivos Docker** o el servicio systemd según la opción
6. **Configurar nginx** como reverse proxy
7. **Primer arranque** → la app crea las tablas y el usuario admin automáticamente
8. **Cambiar contraseña del admin** de inmediato
9. **Configurar cron de backups** de PostgreSQL
10. **Distribuir la URL interna** del servidor al equipo
