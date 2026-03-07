# Guía de Usuario — Administrador

## ¿Qué puede hacer el Administrador?

El rol **admin** tiene acceso total al sistema. Puede gestionar usuarios, aprobar solicitudes, configurar la infraestructura eléctrica, revisar la auditoría y crear backups.

---

## 1. Gestión del Mapa de Línea 1

Al ingresar, el mapa muestra las 26 estaciones (E01–E26) con código de colores:

| Color | Significado |
|-------|-------------|
| 🟢 Verde | Capacidad suficiente |
| 🟡 Amarillo | Menos del 20% disponible |
| 🔴 Rojo | Demanda supera la capacidad |

**Clic en una estación** abre el detalle con tres pestañas:
- **Resumen:** potencia instalada, demanda y disponible
- **Unifilar:** diagrama eléctrico de la estación
- **Barras y Circuitos:** gestión de circuitos por barra

---

## 2. Gestión de Circuitos

### Crear un circuito
1. Ir al detalle de una estación → pestaña **Barras y Circuitos**
2. Seleccionar la barra (normal / emergencia / continuidad)
3. Clic en **"Nuevo Circuito"**
4. Completar los campos:
   - **Denominación** (código interno, ej: `C-001`)
   - **Nombre** (descripción del local o equipo)
   - **Potencia Instalada (PI kW)** y **Factor de Demanda (FD)**
   - **MD kW** se calcula automáticamente como PI × FD
   - **Estado:** operativo, reserva sin equipar, reserva equipada, inactivo
5. Si el circuito supera la capacidad disponible, se advertirá. Puede **forzar** la creación si es necesario.

### Cambiar estado
Clic en el estado del circuito en la tabla → seleccionar nuevo estado. Los estados de reserva requieren una fecha de vencimiento.

### Eliminar circuito
⚠ Solo cuando el circuito ya no existe físicamente. La eliminación borra también los sub-circuitos asociados.

---

## 3. Gestión de Sub-circuitos

Los sub-circuitos son ampliaciones dentro de un circuito existente.

1. En la tabla de circuitos, expandir un circuito
2. Clic en **"Agregar Sub-circuito"**
3. Completar nombre, PI kW, FD y estado

---

## 4. Aprobación de Solicitudes

Los operadores OPERSAC envían solicitudes de ampliación de carga.

### Flujo de aprobación
1. Ir a **Solicitudes** en el menú lateral
2. Ver solicitudes pendientes (badge amarillo)
3. Revisar los detalles: estación, barra, carga solicitada, justificación
4. Clic en **Aprobar** → se crea automáticamente el circuito o sub-circuito
5. O clic en **Rechazar** → ingresar motivo del rechazo

> Al aprobar una solicitud con `circuit_id`: se crea un **sub-circuito** en ese circuito.
> Al aprobar sin `circuit_id`: se crea un **nuevo circuito** en la barra.

---

## 5. Gestión de Usuarios

Ir a **Gestión de Usuarios** en el menú lateral.

### Crear usuario
1. Clic en **"Nuevo Usuario"**
2. Ingresar username, nombre completo, contraseña y rol (`admin` u `opersac`)
3. Los usuarios OPERSAC reciben todos los permisos habilitados por defecto

### Cambiar estado
Editar el usuario → cambiar estado a `active`, `inactive` o `reported`.

---

## 6. Gestión de Permisos (OPERSAC)

Ir a **Permisos** en el menú lateral.

Seleccionar un usuario OPERSAC para ver y modificar sus permisos:

| Permiso | Descripción |
|---------|-------------|
| `view_stations` | Ver mapa, estaciones y barras |
| `view_circuits` | Ver circuitos y sub-circuitos |
| `send_requests` | Enviar solicitudes de ampliación |
| `add_observations` | Agregar observaciones técnicas |
| `view_reports` | Ver y exportar reportes |

---

## 7. Notificaciones

Las notificaciones automáticas alertan sobre **reservas sin contacto**: circuitos en estado reserva cuya fecha de vencimiento se aproxima y no tienen registrado un contacto con el cliente.

El ícono de campana (🔔) muestra el número de notificaciones no leídas.

### Acciones disponibles:
- **Leer:** Marcar como leída
- **Extender:** Ampliar el plazo de la reserva
- **Resolver:** Poner el circuito en estado `inactivo` y cerrar la notificación
- **Descartar:** Cerrar la notificación sin acción sobre el circuito

---

## 8. Reportes

Ir a **Reportes** en el menú lateral.

- **Demanda eléctrica:** muestra la carga actual de cada estación
- **Solicitudes por estación:** muestra cuántas solicitudes hay por estado
- **Filtro de fechas:** filtra los datos por rango temporal
- **Exportar Excel:** descarga el reporte con gráficos incluidos

---

## 9. Auditoría

Ir a **Auditoría** en el menú lateral.

Registro de todas las acciones del sistema. Puede filtrar por:
- Tipo de entidad (circuit, user, request, backup...)
- Acción (CREATE, UPDATE, DELETE, APPROVE...)
- Usuario
- Rango de fechas
- Solo registros marcados como sospechosos

**Marcar como sospechoso:** Clic en el ícono de bandera para destacar un registro e ingresar el motivo.

**Exportar:** Descargar todos los logs en Excel.

---

## 10. Backups

Ir a **Backup** en el menú lateral.

### Crear backup
1. Clic en **"Crear Backup"**
2. Ingresar descripción (opcional)
3. Seleccionar si incluir los logs de auditoría
4. El backup queda guardado con fecha y hora

### Restaurar backup
⚠ **Advertencia:** Restaurar borra TODOS los datos actuales y los reemplaza con los del backup.
1. Seleccionar el backup de la lista
2. Clic en **"Restaurar"** → confirmar la acción
3. El sistema recalculará todas las energías tras la restauración

---

## Ver como OPERSAC

En el menú lateral inferior, el admin puede activar **"Ver como Opersac"** para revisar cómo ve el sistema un operador.
