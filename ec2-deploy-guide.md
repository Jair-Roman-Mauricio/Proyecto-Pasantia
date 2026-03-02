# Guía de despliegue en Amazon EC2

> **Objetivo:** Levantar la aplicación Línea 1 Metro en una instancia EC2 de AWS para simular el entorno del servidor interno de la empresa. El proceso es idéntico al despliegue real — solo cambia que aquí la IP es pública en lugar de privada de intranet.

---

## Prerrequisitos

- Cuenta en [aws.amazon.com](https://aws.amazon.com) (la capa gratuita es suficiente para la simulación)
- El proyecto con todos los archivos Docker ya presentes (`Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`, `nginx/nginx.conf`, `backend/.env.example`)
- Tu PC con acceso a internet

---

## Paso 1 — Crear la instancia EC2

1. Inicia sesión en la consola AWS: [console.aws.amazon.com](https://console.aws.amazon.com)
2. Ve a **EC2 → Launch Instance**
3. Completa los campos:

| Campo | Valor |
|---|---|
| **Nombre** | `linea1metro-server` |
| **AMI** | Ubuntu Server 22.04 LTS (64-bit x86) |
| **Tipo de instancia** | `t2.micro` (gratis 12 meses) o `t3.small` (más RAM, ~$0.02/h) |
| **Par de claves** | Crear nuevo → descargar `mi-clave.pem` y guardarlo en lugar seguro |
| **Almacenamiento** | 20 GB (gp3, suficiente para la base de datos + imágenes) |

4. En **Network settings → Edit**, configura el grupo de seguridad con estas reglas:

| Tipo | Puerto | Origen | Motivo |
|---|---|---|---|
| SSH | 22 | Mi IP (seleccionar "My IP") | Acceso seguro desde tu PC |
| HTTP | 80 | 0.0.0.0/0 | Acceso a la aplicación web |
| HTTPS | 443 | 0.0.0.0/0 | Opcional, para SSL futuro |

> **Importante:** No abrir el puerto 5432 (PostgreSQL). La base de datos solo es accesible dentro de la red Docker interna.

5. Clic en **Launch Instance** y espera 1-2 minutos.

---

## Paso 2 — Asignar una IP Elástica (Elastic IP)

Por defecto, EC2 cambia la IP pública cada vez que apagas y enciendes la instancia. Para evitarlo:

1. En el menú izquierdo de EC2 → **Elastic IPs**
2. Clic en **Allocate Elastic IP address** → **Allocate**
3. Selecciona la IP recién creada → **Actions → Associate Elastic IP address**
4. Selecciona tu instancia `linea1metro-server` → **Associate**

Ahora tienes una IP fija (ej. `54.123.45.67`) que no cambia.

---

## Paso 3 — Conectarse por SSH

### En macOS / Linux:
```bash
# Dar permisos correctos al archivo de clave
chmod 400 ~/Descargas/mi-clave.pem

# Conectarse (reemplaza IP-PUBLICA con tu IP Elástica)
ssh -i ~/Descargas/mi-clave.pem ubuntu@IP-PUBLICA
```

### En Windows (usando PowerShell):
```powershell
ssh -i C:\Users\TuUsuario\Descargas\mi-clave.pem ubuntu@IP-PUBLICA
```

> Si aparece el mensaje `Are you sure you want to continue connecting?`, escribe `yes` y presiona Enter.

---

## Paso 4 — Instalar Docker en la instancia

Una vez conectado por SSH, ejecuta estos comandos uno por uno:

```bash
# Actualizar paquetes del sistema
sudo apt-get update

# Instalar dependencias necesarias
sudo apt-get install -y ca-certificates curl

# Agregar clave GPG oficial de Docker
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Agregar repositorio de Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Actualizar e instalar Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Agregar el usuario ubuntu al grupo docker (para no tener que usar sudo siempre)
sudo usermod -aG docker ubuntu

# Aplicar el cambio de grupo en la sesión actual
newgrp docker
```

Verificar que funciona:
```bash
docker --version
docker compose version
```

Deberías ver algo como:
```
Docker version 26.x.x
Docker Compose version v2.x.x
```

---

## Paso 5 — Subir el proyecto a la instancia

Tienes dos opciones. Elige la que aplique a tu caso:

### Opción A — SCP (copiar desde tu PC directamente)

Ejecuta esto **desde tu PC local** (no desde la sesión SSH):

```bash
# macOS/Linux:
scp -i ~/Descargas/mi-clave.pem -r ./Linea1Mtro-CludeCodePlan ubuntu@IP-PUBLICA:~/

# Windows (PowerShell):
scp -i C:\Users\TuUsuario\Descargas\mi-clave.pem -r .\Linea1Mtro-CludeCodePlan ubuntu@IP-PUBLICA:~/
```

Esto copia toda la carpeta del proyecto a la instancia. Tarda unos minutos según el tamaño.

### Opción B — Git clone (si el proyecto está en GitHub o GitLab)

En la sesión SSH de la instancia:

```bash
# Instalar git si no está disponible
sudo apt-get install -y git

# Clonar el repositorio
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio
```

---

## Paso 6 — Crear el archivo .env

En la sesión SSH, dentro de la carpeta del proyecto:

```bash
cd ~/Linea1Mtro-CludeCodePlan

# Copiar la plantilla
cp backend/.env.example backend/.env

# Editar con nano
nano backend/.env
```

Rellena estos valores (los demás puedes dejarlos como están):

```env
# Elige un nombre de usuario para la base de datos
POSTGRES_USER=linea1user

# Contraseña fuerte (mínimo 16 caracteres, mezcla letras/números/símbolos)
POSTGRES_PASSWORD=MiContraseñaSegura2024!

# La URL debe usar el mismo usuario y contraseña que arriba
# IMPORTANTE: el host siempre es "db", no localhost
DATABASE_URL=postgresql://linea1user:MiContraseñaSegura2024!@db:5432/linea1metro

# Generar clave secreta aleatoria con este comando:
# python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=pega-aqui-la-clave-generada

# Reemplaza con tu IP Elástica de EC2
CORS_ORIGINS=["http://54.123.45.67"]

ACCESS_TOKEN_EXPIRE_MINUTES=480
STORAGE_PATH=/app/storage
MAX_IMAGE_SIZE_MB=10
```

Para generar la SECRET_KEY en la misma terminal:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Copia el resultado y pégalo en el archivo `.env`.

Guardar en nano: `Ctrl+O` → Enter → `Ctrl+X`

---

## Paso 7 — Construir y levantar la aplicación

```bash
# Asegurarte de estar en la carpeta del proyecto
cd ~/Linea1Mtro-CludeCodePlan

# Construir imágenes y levantar todos los servicios en segundo plano
docker compose up -d --build
```

La primera vez tarda entre 3 y 8 minutos porque:
- Descarga las imágenes base (postgres, nginx, python, node)
- Compila el frontend con Node.js
- Instala las dependencias Python

Puedes ver el progreso en tiempo real con:
```bash
docker compose logs -f
```

Presiona `Ctrl+C` para salir del seguimiento de logs (los contenedores siguen corriendo).

---

## Paso 8 — Verificar que todo funciona

```bash
# Ver el estado de los 3 contenedores
docker compose ps
```

Deberías ver los tres servicios con estado `running`:
```
NAME                STATUS
linea1metro-db      running (healthy)
linea1metro-backend running
linea1metro-frontend running
```

Revisar los logs del backend para confirmar que no hay errores:
```bash
docker compose logs backend --tail=30
```

Deberías ver: `Application startup complete.`

---

## Paso 9 — Acceder a la aplicación

Abre tu navegador y entra a:

- **Aplicación web:** `http://IP-PUBLICA-EC2`
- **API (Swagger docs):** `http://IP-PUBLICA-EC2/api/docs`

Credenciales iniciales:
- Usuario: `admin`
- Contraseña: `admin123`

> **Cambia la contraseña inmediatamente** después del primer inicio de sesión.

---

## Paso 10 — Operaciones diarias

### Ver logs en tiempo real
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### Reiniciar un servicio sin perder datos
```bash
docker compose restart backend
docker compose restart frontend
```

### Parar toda la aplicación (los datos persisten en los volúmenes)
```bash
docker compose down
```

### Volver a levantar después de parar
```bash
docker compose up -d
```

### Actualizar el código (cuando hagas cambios)
```bash
git pull   # si usaste git clone
docker compose up -d --build
```

Solo reconstruye lo que cambió — el frontend puede tardar 1-2 minutos, el backend unos segundos.

---

## Paso 11 — Hacer backup de la base de datos

Desde la instancia EC2:

```bash
# Crear backup con fecha en el nombre
docker compose exec db pg_dump -U linea1user linea1metro > backup_$(date +%Y%m%d_%H%M).sql

# Ver que se creó correctamente
ls -lh backup_*.sql
```

Para descargar el backup a tu PC (ejecutar desde tu PC):
```bash
scp -i mi-clave.pem ubuntu@IP-PUBLICA:~/Linea1Mtro-CludeCodePlan/backup_*.sql ./
```

---

## Paso 12 — Apagar la instancia para ahorrar costos

Cuando termines de probar, **apaga la instancia** desde la consola AWS o:

```bash
# Parar los contenedores Docker (los datos en volúmenes se conservan)
docker compose down
```

Luego en la consola AWS: **EC2 → Instances → seleccionar instancia → Instance State → Stop**

> La IP Elástica sigue asociada. Cuando enciendas de nuevo la instancia, la IP es la misma y los datos de PostgreSQL siguen ahí (en el volumen EBS).

---

## Paso 13 — Diferencias entre EC2 y el servidor real de la empresa

| Aspecto | EC2 (simulación) | Servidor de la empresa |
|---|---|---|
| **Acceso** | Por internet (IP pública) | Por intranet (IP privada) |
| **IP** | IP Elástica pública | IP fija de la red interna |
| **CORS_ORIGINS** | `["http://54.x.x.x"]` | `["http://192.168.x.x"]` |
| **SSH** | Con `.pem` desde internet | Con usuario/contraseña desde la intranet |
| **Docker** | Igual | Igual |
| **docker-compose.yml** | Sin cambios | Sin cambios |
| **Proceso de despliegue** | Igual | Igual |

El único cambio real cuando vayas al servidor de la empresa es editar `CORS_ORIGINS` en el `.env` con la IP interna. Todo lo demás es idéntico.

---

## Resumen de costos en AWS (referencia)

| Recurso | Free Tier (12 meses) | Después del free tier |
|---|---|---|
| `t2.micro` (750 h/mes) | Gratis | ~$0.012/hora |
| `t3.small` | No incluido | ~$0.023/hora (~$17/mes 24/7) |
| Almacenamiento EBS 20 GB | 30 GB incluidos | ~$1.60/mes |
| IP Elástica (asociada) | Gratis | Gratis |
| IP Elástica (no asociada) | $0.005/hora | $0.005/hora |

> **Recomendación:** usa `t2.micro` para la simulación. Es suficiente para probar y está dentro del free tier. Apaga la instancia cuando no la uses.
