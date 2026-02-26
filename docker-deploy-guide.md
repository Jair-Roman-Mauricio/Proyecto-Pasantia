# Guía de Despliegue con Docker — Linea 1 Metro

Esta guía explica paso a paso cómo instalar y ejecutar el sistema en un servidor interno de la empresa usando Docker.

---

## Requisitos previos

Antes de comenzar, el servidor debe tener instalado:

- **Docker** (versión 24 o superior)
- **Docker Compose** (versión 2 o superior — viene incluido con Docker Desktop)
- Acceso a internet **solo durante la instalación** (para descargar imágenes base). Después de eso funciona completamente offline.

Para verificar que Docker está instalado correctamente:

```bash
docker --version
docker compose version
```

---

## Paso 1 — Copiar el proyecto al servidor

Llevar la carpeta del proyecto al servidor. Hay varias formas de hacerlo:

**Opción A — USB / disco externo:**
Copiar la carpeta `Linea1Mtro-CludeCodePlan` al servidor y colocarla en una ruta conveniente, por ejemplo:
```
/opt/linea1metro/
```

**Opción B — Git (si el servidor tiene acceso al repositorio):**
```bash
git clone <url-del-repositorio> /opt/linea1metro
```

El resultado debe ser una carpeta con esta estructura:
```
/opt/linea1metro/
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── .dockerignore
├── nginx/
│   └── nginx.conf
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── .env.example      ← plantilla de configuración
└── frontend/
    ├── src/
    └── package.json
```

---

## Paso 2 — Crear el archivo de configuración `.env`

Este archivo contiene las contraseñas y claves secretas del sistema. **Nunca debe subirse al repositorio.**

Crear el archivo copiando la plantilla:

```bash
cp /opt/linea1metro/backend/.env.example /opt/linea1metro/backend/.env
```

Abrir el archivo para editarlo:

```bash
nano /opt/linea1metro/backend/.env
```

El archivo se verá así (con los valores de ejemplo):

```env
POSTGRES_USER=linea1user
POSTGRES_PASSWORD=CAMBIAR_PASSWORD_FUERTE
DATABASE_URL=postgresql://linea1user:CAMBIAR_PASSWORD_FUERTE@db:5432/linea1metro
SECRET_KEY=REEMPLAZAR_CON_CLAVE_ALEATORIA_DE_64_CARACTERES
CORS_ORIGINS=["http://192.168.X.X"]
ACCESS_TOKEN_EXPIRE_MINUTES=480
STORAGE_PATH=/app/storage
MAX_IMAGE_SIZE_MB=10
```

### Qué cambiar y cómo:

---

### `POSTGRES_PASSWORD`

Elegir una contraseña fuerte para la base de datos. Ejemplo:
```
POSTGRES_PASSWORD=Metro2025#Seguro!
```

> Este mismo valor debe aparecer también dentro de `DATABASE_URL`.

---

### `DATABASE_URL`

Reemplazar `CAMBIAR_PASSWORD_FUERTE` por la misma contraseña elegida arriba.

> **Importante:** El host debe ser `db` (no `localhost`). En Docker, los servicios se comunican por nombre. Si se pone `localhost`, el backend no encontrará la base de datos.

Ejemplo completo:
```
DATABASE_URL=postgresql://linea1user:Metro2025#Seguro!@db:5432/linea1metro
```

---

### `SECRET_KEY`

Esta clave se usa para firmar los tokens de autenticación (JWT). Debe ser aleatoria y larga. Generar una ejecutando este comando en cualquier computador con Python:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Ejemplo de salida:
```
a3f8c2d1e4b5a6f7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1
```

Copiar ese valor en el `.env`:
```
SECRET_KEY=a3f8c2d1e4b5a6f7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1
```

---

### `CORS_ORIGINS`

Indicar la IP o nombre de host del servidor en la red interna de la empresa.

Para saber cuál es la IP del servidor:
```bash
ip addr show        # Linux
ipconfig            # Windows Server
```

Ejemplo:
```
CORS_ORIGINS=["http://192.168.1.50"]
```

Si el servidor tiene un nombre de dominio interno (por ejemplo `servidor-linea1.empresa.local`):
```
CORS_ORIGINS=["http://servidor-linea1.empresa.local"]
```

---

### Archivo `.env` final (ejemplo completo):

```env
POSTGRES_USER=linea1user
POSTGRES_PASSWORD=Metro2025#Seguro!
DATABASE_URL=postgresql://linea1user:Metro2025#Seguro!@db:5432/linea1metro
SECRET_KEY=a3f8c2d1e4b5a6f7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1
CORS_ORIGINS=["http://192.168.1.50"]
ACCESS_TOKEN_EXPIRE_MINUTES=480
STORAGE_PATH=/app/storage
MAX_IMAGE_SIZE_MB=10
```

Guardar y cerrar el archivo (`Ctrl+O`, `Enter`, `Ctrl+X` en nano).

---

## Paso 3 — Construir y levantar los contenedores

Ir a la carpeta del proyecto:

```bash
cd /opt/linea1metro
```

Ejecutar el siguiente comando para construir las imágenes e iniciar todo:

```bash
docker compose up -d --build
```

Este proceso tarda varios minutos la **primera vez** porque:
- Descarga las imágenes base (Python, Node, PostgreSQL, nginx)
- Instala las dependencias de Python (`pip install`)
- Compila el frontend React (`npm run build`)

En arranques posteriores, si el código no cambió, es casi instantáneo.

### Qué hace este comando paso a paso:

| Etapa | Qué ocurre |
|---|---|
| `--build` | Reconstruye las imágenes si hay cambios en el código |
| `-d` | Corre los contenedores en segundo plano (detached mode) |
| Servicio `db` | Levanta PostgreSQL y espera a que esté listo |
| Servicio `backend` | Espera a que `db` esté sano, luego inicia FastAPI. En el primer arranque crea todas las tablas y carga los datos iniciales (26 estaciones, usuario admin) |
| Servicio `frontend` | Construye React y lo sirve con nginx en el puerto 80. nginx también hace de proxy hacia el backend |

---

## Paso 4 — Verificar que todo funciona

### Ver el estado de los contenedores:

```bash
docker compose ps
```

La salida debe mostrar los 3 servicios como `running`:

```
NAME                    STATUS          PORTS
linea1metro-db-1        running (healthy)
linea1metro-backend-1   running
linea1metro-frontend-1  running         0.0.0.0:80->80/tcp
```

### Ver los logs del backend (útil para detectar errores):

```bash
docker compose logs backend
```

Si la app arrancó bien, al final de los logs debe aparecer algo como:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Ver logs en tiempo real:

```bash
docker compose logs -f backend
```

Presionar `Ctrl+C` para salir.

---

## Paso 5 — Acceder al sistema

Abrir un navegador en cualquier computador de la red interna y entrar a:

```
http://192.168.1.50
```

(Reemplazar con la IP real del servidor.)

La página de login del sistema debe aparecer.

### Primera sesión — cambiar contraseña del admin

Ingresar con las credenciales por defecto:
- **Usuario:** `admin`
- **Contraseña:** `admin123`

> **Importante:** Cambiar la contraseña del admin inmediatamente después del primer login. Esta contraseña por defecto es pública y conocida.

---

## Comandos útiles del día a día

### Iniciar los servicios (si el servidor se reinició):
```bash
cd /opt/linea1metro
docker compose up -d
```

Los contenedores están configurados con `restart: always`, por lo que se reinician automáticamente si el servidor se reinicia. Este comando solo es necesario la primera vez o si se detuvieron manualmente.

### Detener los servicios:
```bash
docker compose down
```

> Los datos en la base de datos y los archivos subidos **no se pierden** al detener los servicios. Están guardados en volúmenes Docker persistentes.

### Ver logs de un servicio específico:
```bash
docker compose logs backend    # API FastAPI
docker compose logs frontend   # nginx
docker compose logs db         # PostgreSQL
```

### Ver uso de recursos:
```bash
docker stats
```

---

## Actualizar el sistema con una nueva versión

Cuando haya cambios en el código (nuevo feature, corrección de bug, etc.):

```bash
cd /opt/linea1metro

# 1. Obtener los cambios nuevos
git pull        # si se usa git
# o copiar los archivos nuevos manualmente

# 2. Reconstruir e reiniciar
docker compose up -d --build
```

Docker solo reconstruye lo que cambió, por lo que el proceso es más rápido que la primera vez.

> Los datos de la base de datos y los archivos almacenados **se conservan** durante las actualizaciones.

---

## Backup de la base de datos

### Hacer un backup manual:
```bash
docker compose exec db pg_dump -U linea1user linea1metro > backup_$(date +%Y%m%d_%H%M).sql
```

Esto crea un archivo `.sql` con todos los datos en la carpeta actual.

### Restaurar un backup:
```bash
cat backup_20260225_1430.sql | docker compose exec -T db psql -U linea1user linea1metro
```

### Programar backups automáticos (cron en el servidor host):
```bash
# Abrir el cron del servidor
crontab -e

# Agregar esta línea para backup diario a las 02:00
0 2 * * * cd /opt/linea1metro && docker compose exec -T db pg_dump -U linea1user linea1metro > /backups/linea1metro_$(date +\%Y\%m\%d).sql
```

---

## Solución de problemas comunes

### El sistema no carga en el navegador

1. Verificar que los contenedores están corriendo: `docker compose ps`
2. Revisar si el puerto 80 está bloqueado por el firewall del servidor:
   ```bash
   # Linux
   sudo ufw allow 80/tcp
   # o
   sudo firewall-cmd --add-port=80/tcp --permanent && sudo firewall-cmd --reload
   ```

### El backend no conecta con la base de datos

Verificar que en el `.env` el host de `DATABASE_URL` es `db` y no `localhost`:
```env
DATABASE_URL=postgresql://linea1user:PASSWORD@db:5432/linea1metro
#                                              ^^
#                                         nombre del servicio Docker
```

### Error al construir el frontend

Si `npm run build` falla, ver el log completo:
```bash
docker compose logs frontend
```

### Reiniciar un servicio específico:
```bash
docker compose restart backend
docker compose restart frontend
```

### Reconstruir todo desde cero (sin perder datos):
```bash
docker compose down
docker compose up -d --build
```

---

## Resumen rápido

```bash
# Preparación (solo una vez)
cp backend/.env.example backend/.env
nano backend/.env          # editar contraseñas y IP

# Arrancar
docker compose up -d --build

# Verificar
docker compose ps
# Abrir http://IP-SERVIDOR en el navegador

# Actualizar
git pull && docker compose up -d --build

# Backup
docker compose exec db pg_dump -U linea1user linea1metro > backup.sql
```
