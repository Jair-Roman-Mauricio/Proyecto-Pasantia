# Guía de despliegue en Amazon EC2

> **Objetivo:** Levantar la aplicación Línea 1 Metro en una instancia EC2 de AWS para simular el entorno del servidor interno de la empresa. El proceso es idéntico al despliegue real — solo cambia que la IP es pública en lugar de privada de intranet.

---

## Prerrequisitos

- Cuenta en [aws.amazon.com](https://aws.amazon.com) (la capa gratuita es suficiente para la simulación)
- El proyecto con todos los archivos Docker presentes (`Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`, `nginx/nginx.conf`, `backend/.env.example`)
- Tu PC con acceso a internet

---

## Paso 1 — Crear la instancia EC2

1. Inicia sesión en la consola AWS: [console.aws.amazon.com](https://console.aws.amazon.com)
2. Ve a **EC2 → Launch Instance**
3. Completa los campos:

| Campo | Valor recomendado |
|---|---|
| **Nombre** | `linea1metro-server` |
| **AMI** | Ubuntu Server 22.04 LTS (64-bit x86) |
| **Tipo de instancia** | `t3.micro` o superior (mínimo 1GB RAM) |
| **Par de claves** | Crear nuevo → descargar `mi-clave.pem` y guardarlo en lugar seguro |
| **Almacenamiento** | 20 GB (gp3) |

> **Sobre el tipo de instancia:** El build del frontend (Vite + TypeScript) consume ~900 MB de RAM. Con `t2.micro` (1 GB) el proceso puede agotarse. Se recomienda `t3.micro` o agregar swap después (ver Paso 4).

4. En **Network settings → Edit**, configura el grupo de seguridad con estas reglas **antes de lanzar**:

| Tipo | Puerto | Origen | Motivo |
|---|---|---|---|
| SSH | 22 | Mi IP ("My IP") | Acceso seguro solo desde tu PC |
| HTTP | 80 | 0.0.0.0/0 | Acceso a la aplicación web |
| HTTPS | 443 | 0.0.0.0/0 | Opcional, para SSL futuro |

> **Importante:** No abrir el puerto 5432 (PostgreSQL). La base de datos solo es accesible dentro de la red Docker interna, nunca desde fuera.

5. Clic en **Launch Instance** y espera 1-2 minutos.

---

## Paso 2 — Asignar una IP Elástica (Elastic IP)

Por defecto, EC2 cambia la IP pública cada vez que apagas y enciendes la instancia. Para evitarlo:

1. En el menú izquierdo de EC2 → **Elastic IPs**
2. Clic en **Allocate Elastic IP address** → **Allocate**
3. Selecciona la IP recién creada → **Actions → Associate Elastic IP address**
4. Selecciona tu instancia → **Associate**

Ahora tienes una IP fija (ej. `44.203.29.225`) que no cambia entre reinicios.

---

## Paso 3 — Conectarse a la instancia

### Opción A — Desde el navegador (más fácil, sin problemas de claves)

1. En la consola AWS, selecciona la instancia
2. Clic en **"Conectar"** (botón naranja arriba)
3. Elige la pestaña **"EC2 Instance Connect"**
4. Usuario: `ubuntu` → Clic en **"Conectar"**

Se abre una terminal directamente en el navegador. No requiere archivo `.pem`.

### Opción B — SSH desde tu PC (macOS/Linux)

```bash
chmod 400 ~/Descargas/mi-clave.pem
ssh -i ~/Descargas/mi-clave.pem ubuntu@IP-PUBLICA
```

### Opción C — SSH desde Windows (PowerShell)

En Windows el cliente SSH rechaza el `.pem` si tiene permisos abiertos. Antes de conectarte, ejecuta en PowerShell:

```powershell
# Corregir permisos del archivo de clave (solo una vez)
$key = "C:\Users\TuUsuario\Downloads\mi-clave.pem"
icacls $key /inheritance:r
icacls $key /grant:r "$($env:USERNAME):(R)"

# Conectarse
ssh -i "C:\Users\TuUsuario\Downloads\mi-clave.pem" ubuntu@IP-PUBLICA
```

> Si sigues viendo `Permission denied (publickey)` después de corregir los permisos, usa la **Opción A** (EC2 Instance Connect desde el navegador) — es más simple y no requiere el `.pem`.

> Cuando aparezca `Are you sure you want to continue connecting?`, escribe `yes` y presiona Enter.

---

## Paso 4 — Instalar Docker y agregar swap

### 4.1 — Instalar Docker

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker ubuntu
newgrp docker
```

Verificar:
```bash
docker --version        # Docker version 26.x.x
docker compose version  # Docker Compose version v2.x.x
```

### 4.2 — Agregar swap (evita fallos de memoria durante el build)

El build de Vite con 2500+ módulos puede agotar la RAM en instancias de 1 GB. Agrega 2 GB de swap antes de construir:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

Verificar que está activo:
```bash
free -h   # Debe mostrar 2G en la fila Swap
```

---

## Paso 5 — Clonar el proyecto

```bash
sudo apt-get install -y git
git clone https://github.com/tu-usuario/tu-repositorio.git
```

> **Atención:** la carpeta se crea con el nombre del repositorio en GitHub, no con el nombre de tu carpeta local. Si tu repo se llama `Proyecto-Pasantia`, entra con `cd Proyecto-Pasantia` — no uses el nombre de carpeta local.

```bash
# Verificar la carpeta creada
ls
cd nombre-del-repositorio
```

Confirma que ves los archivos del proyecto:
```bash
ls
# Debes ver: backend/  frontend/  docker-compose.yml  Dockerfile.backend  Dockerfile.frontend  nginx/
```

---

## Paso 6 — Crear los archivos de configuración

Se necesitan **dos archivos `.env`**: uno para el backend (credenciales de DB, JWT, CORS) y uno en la raíz (para que Docker Compose pueda interpolar variables en el `docker-compose.yml`).

### 6.1 — Crear `backend/.env`

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

Rellena estos valores:

```env
POSTGRES_USER=linea1user
POSTGRES_PASSWORD=CambiaEstoPorAlgoSeguro123!
DATABASE_URL=postgresql://linea1user:CambiaEstoPorAlgoSeguro123!@db:5432/linea1metro
SECRET_KEY=pega-aqui-el-resultado-del-comando-de-abajo
CORS_ORIGINS=["http://TU-IP-ELASTICA"]
ACCESS_TOKEN_EXPIRE_MINUTES=480
STORAGE_PATH=/app/storage
MAX_IMAGE_SIZE_MB=10
```

Para generar la `SECRET_KEY`:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Copia el resultado y pégalo en `SECRET_KEY=`.

Guardar en nano: `Ctrl+O` → Enter → `Ctrl+X`

> **Regla importante:** La contraseña en `POSTGRES_PASSWORD` y la contraseña dentro de la URL en `DATABASE_URL` deben ser **exactamente iguales**. El host en la URL siempre es `db` (nombre del servicio Docker), nunca `localhost`.

### 6.2 — Crear `.env` en la raíz del proyecto

Docker Compose usa este archivo para resolver variables como `${POSTGRES_USER}` dentro del `docker-compose.yml`. Sin este archivo, el healthcheck de la base de datos falla.

```bash
echo "POSTGRES_USER=linea1user" > .env
```

> Este archivo solo necesita `POSTGRES_USER`. Las demás variables las lee directamente de `backend/.env` en tiempo de ejecución de los contenedores.

---

## Paso 7 — Construir y levantar la aplicación

```bash
docker compose up -d --build
```

La primera vez tarda **5-10 minutos** porque:
- Descarga imágenes base (postgres:16-alpine, nginx:alpine, python:3.10-slim, node:20-alpine)
- Instala dependencias Python (`pip install`)
- Instala dependencias Node (`npm ci`) y compila el frontend (`tsc + vite build`)

**Lo que verás durante el build (todo normal):**
- `WARN: the attribute 'version' is obsolete` → advertencia cosmética, no afecta nada
- `✓ 2510 modules transformed.` → TypeScript y Vite compilaron sin errores
- Tiempo en silencio después del "transforming..." → Vite está generando los bundles finales; espera, no canceles

Al terminar deberías ver:
```
✔ Container proyecto-pasantia-db-1        Healthy
✔ Container proyecto-pasantia-backend-1   Started
✔ Container proyecto-pasantia-frontend-1  Started
```

---

## Paso 8 — Verificar el estado

```bash
docker compose ps
```

Los tres servicios deben estar en estado `Up`:
```
NAME                           STATUS
proyecto-...-db-1              Up (healthy)
proyecto-...-backend-1         Up
proyecto-...-frontend-1        Up     0.0.0.0:80->80/tcp
```

Revisar logs del backend:
```bash
docker compose logs backend --tail=20
```
Debe mostrar: `Application startup complete.`

---

## Paso 9 — Acceder a la aplicación

Abre tu navegador y entra a:

```
http://TU-IP-ELASTICA
```

> **Usa `http://` explícitamente, no `https://`.** Muchos navegadores redirigen automáticamente a HTTPS. Si ves "No se puede acceder al sitio", verifica que la URL empiece con `http://` y no `https://`.

Credenciales iniciales:
- Usuario: `admin`
- Contraseña: `admin123`

**Cambia la contraseña inmediatamente** después del primer inicio de sesión.

API docs (Swagger): `http://TU-IP-ELASTICA/api/docs`

---

## Paso 10 — Solución a problemas comunes

### Los contenedores no arrancan / DB "unhealthy"

```bash
# Ver logs de la base de datos
docker compose logs db --tail=20
```

Si el error menciona variables no definidas, verifica que existe el `.env` raíz:
```bash
cat .env   # Debe mostrar: POSTGRES_USER=linea1user
```

Si no existe, créalo:
```bash
echo "POSTGRES_USER=linea1user" > .env
docker compose up -d
```

### El build del frontend falla por memoria (exit code 137)

```bash
# Agregar swap si no lo hiciste en el Paso 4
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Volver a construir
docker compose up -d --build
```

### ERR_CONNECTION_REFUSED en el navegador

Verifica en orden:
1. Los contenedores están corriendo: `docker compose ps`
2. Estás usando `http://` (no `https://`) en la URL
3. El Security Group tiene la regla de puerto 80 abierta a `0.0.0.0/0` (verificar en la consola AWS → instancia → pestaña Seguridad)

### El git pull falla porque hay un `.env` local

```bash
# Si git pull dice "untracked files would be overwritten":
rm backend/.env   # El pull lo restaurará desde el repo
git pull
```

---

## Paso 11 — Actualizar el código (ciclo de trabajo)

Cuando hagas cambios en tu PC local:

```bash
# En tu PC: commit y push
git add .
git commit -m "descripcion del cambio"
git push
```

```bash
# En EC2: pull y rebuild
cd ~/nombre-del-repositorio
git pull
docker compose up -d --build
```

> Si git pull falla porque hay un `.env` local que el repo quiere sobreescribir: `rm backend/.env && git pull`

---

## Paso 12 — Operaciones diarias

```bash
# Ver logs en tiempo real
docker compose logs -f backend
docker compose logs -f frontend

# Reiniciar un servicio sin perder datos
docker compose restart backend

# Parar todos los contenedores (datos se conservan en volúmenes)
docker compose down

# Volver a levantar sin rebuild
docker compose up -d
```

---

## Paso 13 — Backup de la base de datos

```bash
# En EC2 — crear backup con fecha
docker compose exec db pg_dump -U linea1user linea1metro > backup_$(date +%Y%m%d_%H%M).sql

# Verificar tamaño
ls -lh backup_*.sql
```

Descargar a tu PC:
```bash
# Ejecutar desde tu PC (macOS/Linux)
scp -i mi-clave.pem ubuntu@IP-PUBLICA:~/nombre-repo/backup_*.sql ./

# Windows
scp -i "C:\Users\...\mi-clave.pem" ubuntu@IP-PUBLICA:~/nombre-repo/backup_*.sql .
```

---

## Paso 14 — Apagar la instancia para ahorrar costos

Cuando termines de probar:

```bash
# Parar los contenedores (datos persisten)
docker compose down
```

Luego en la consola AWS: **EC2 → Instances → seleccionar → Instance State → Stop**

> La IP Elástica sigue asociada. Al encender de nuevo, la IP es la misma y los datos de PostgreSQL siguen en el volumen EBS.

---

## Paso 15 — Agregar HTTPS con Let's Encrypt (para pasar filtros corporativos)

Los firewalls corporativos bloquean HTTP puro a IPs sin categorizar. Con HTTPS y un dominio real el acceso es permitido.

### 15.1 — Obtener un dominio gratuito (DuckDNS)

1. Ir a **duckdns.org** → login con Google o GitHub
2. Crear un subdominio: ej. `linea1metro` → queda `linea1metro.duckdns.org`
3. En el campo "current ip" poner la **IP Elástica del EC2** → clic en **Update IP**
4. Verificar desde EC2: `nslookup linea1metro.duckdns.org` → debe devolver la IP de EC2

### 15.2 — Reemplazar el dominio placeholder en nginx.conf

El archivo `nginx/nginx.conf` tiene `TU-DOMINIO.duckdns.org` como placeholder. En EC2, edítalo con tu dominio real:

```bash
# En EC2, dentro del repo
sed -i 's/TU-DOMINIO.duckdns.org/linea1metro.duckdns.org/g' nginx/nginx.conf
```

O editar manualmente con nano y reemplazar los 4 lugares donde aparece `TU-DOMINIO.duckdns.org`.

### 15.3 — Instalar Certbot y obtener el certificado

```bash
# Instalar certbot en el host
sudo apt-get install -y certbot

# Parar el frontend para liberar el puerto 80
docker compose stop frontend

# Obtener el certificado (reemplaza con tu dominio real)
sudo certbot certonly --standalone -d linea1metro.duckdns.org

# Dar permisos de lectura para que nginx (dentro del contenedor) pueda leer los certs
sudo chmod -R 755 /etc/letsencrypt/live/
sudo chmod -R 755 /etc/letsencrypt/archive/
```

### 15.4 — Levantar con HTTPS

```bash
# El docker-compose.yml ya tiene puerto 443 y el volumen montado
docker compose up -d

# Verificar
docker compose ps
docker compose logs frontend --tail=10
```

### 15.5 — Actualizar CORS en backend/.env

```bash
nano backend/.env
# Cambiar:
# CORS_ORIGINS=["http://44.203.29.225"]
# Por:
# CORS_ORIGINS=["https://linea1metro.duckdns.org"]

docker compose restart backend
```

### 15.6 — Renovación automática del certificado (expira en 90 días)

```bash
sudo nano /etc/cron.d/certbot-renew
```

Pegar este contenido (reemplaza `Proyecto-Pasantia` con el nombre de tu carpeta):
```
0 3 * * 1 root certbot renew --pre-hook "cd /home/ubuntu/Proyecto-Pasantia && docker compose stop frontend" --post-hook "cd /home/ubuntu/Proyecto-Pasantia && docker compose start frontend" --quiet
```

### Verificación

- `https://linea1metro.duckdns.org` → carga con candado verde
- `http://linea1metro.duckdns.org` → redirige automáticamente a HTTPS
- Probar desde la red corporativa → ya no debe bloquear

---

## Paso 17 — Diferencias entre EC2 y el servidor real de la empresa

| Aspecto | EC2 (simulación) | Servidor de la empresa |
|---|---|---|
| **Acceso** | Por internet (IP pública) | Por intranet (IP privada) |
| **IP** | IP Elástica pública | IP fija de la red interna |
| **CORS_ORIGINS** | `["http://44.x.x.x"]` | `["http://192.168.x.x"]` |
| **SSH** | Con `.pem` desde internet | Con usuario/contraseña desde la intranet |
| **Docker y proceso** | Igual | Igual |

El único cambio real es editar `CORS_ORIGINS` en `backend/.env` con la IP interna. Todo el proceso Docker es idéntico.

---

## Resumen de costos en AWS

| Recurso | Free Tier (12 meses) | Después del free tier |
|---|---|---|
| `t2.micro` (750 h/mes) | Gratis | ~$0.012/hora |
| `t3.micro` | No incluido | ~$0.010/hora (~$7/mes 24/7) |
| `t3.small` | No incluido | ~$0.023/hora (~$17/mes 24/7) |
| Almacenamiento EBS 20 GB | 30 GB incluidos | ~$1.60/mes |
| IP Elástica (asociada a instancia activa) | Gratis | Gratis |
| IP Elástica (sin instancia asociada) | $0.005/hora | $0.005/hora |

> Apaga la instancia cuando no la uses para evitar cobros.
