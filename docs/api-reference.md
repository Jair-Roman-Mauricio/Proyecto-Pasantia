# Referencia de la API — Línea 1 Metro

**Base URL:** `http://servidor:8000/api/v1`
**Documentación interactiva:** `http://servidor:8000/docs`

## Autenticación

Todos los endpoints requieren token JWT (excepto `/auth/login`):
```
Authorization: Bearer <access_token>
```

---

## AUTH

### `POST /auth/login`
Autentica al usuario y retorna el token JWT.

**Body:**
```json
{ "username": "admin", "password": "admin123" }
```

**Respuesta 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "username": "admin", "full_name": "Administrador", "role": "admin" }
}
```

**Errores:** `401` Credenciales incorrectas

---

### `GET /auth/me`
Retorna los datos del usuario autenticado.

**Respuesta 200:** `{ "id": 1, "username": "...", "full_name": "...", "role": "admin" }`
**Errores:** `401` Token inválido o expirado

---

## USERS *(solo admin)*

### `GET /users`
Lista todos los usuarios del sistema.

### `GET /users/{user_id}`
Retorna datos de un usuario específico.

### `POST /users`
Crea un nuevo usuario.

**Body:**
```json
{
  "username": "juan.perez",
  "password": "segura123",
  "full_name": "Juan Pérez",
  "role": "opersac"
}
```
Al crear un usuario `opersac`, se le asignan todos los permisos habilitados por defecto.

**Errores:** `400` Username ya existe | Rol inválido

### `PUT /users/{user_id}`
Actualiza nombre, contraseña o estado del usuario.

**Body (campos opcionales):**
```json
{ "full_name": "...", "password": "...", "status": "active|inactive|reported" }
```

**Errores:** `400` Estado inválido | `404` Usuario no encontrado

---

## STATIONS *(requiere `view_stations`)*

### `GET /stations`
Lista las 26 estaciones ordenadas de sur a norte (E01 Villa El Salvador → E26 Bayóvar).

### `GET /stations/{station_id}`
Datos de una estación específica.

### `GET /stations/{station_id}/power-summary`
Resumen energético: capacidad, demanda máxima y disponible, estado (`green`/`yellow`/`red`).

### `PUT /stations/{station_id}` *(solo admin)*
Actualiza la capacidad del transformador en kW. Recalcula el estado automáticamente.

**Body:** `{ "transformer_capacity_kw": 600 }`

---

## BARS *(requiere `view_stations`)*

Cada estación tiene 3 barras: `normal`, `emergency`, `continuity`.

### `GET /bars/station/{station_id}`
Lista las 3 barras de la estación.

### `GET /bars/{bar_id}`
Datos de una barra específica.

### `GET /bars/{bar_id}/power-summary`
Resumen de capacidad y demanda de la barra.

---

## CIRCUITS *(requiere `view_circuits` para lectura, admin para escritura)*

Estados disponibles: `operative_normal` | `reserve_r` | `reserve_equipped_re` | `inactive`

### `GET /circuits/bar/{bar_id}`
Lista los circuitos de una barra.

### `GET /circuits/{circuit_id}`
Datos de un circuito específico.

### `POST /circuits/bar/{bar_id}` *(solo admin)*
Crea un circuito en la barra.

**Body:**
```json
{
  "denomination": "C01",
  "name": "Alumbrado Norte",
  "pi_kw": 50,
  "fd": 0.8,
  "status": "operative_normal",
  "is_ups": false
}
```

Si `md_kw` no se provee, se calcula como `pi_kw × fd`.
Si la capacidad se excede, retorna `400` con `"requires_force": true`. Reenviar con `"force": true` para confirmar.

**Circuitos UPS:** Requieren `"is_ups": true` + `secondary_bar_id` + `tertiary_bar_id` (distintas entre sí y a la primaria).

### `PUT /circuits/{circuit_id}` *(solo admin)*
Actualiza campos del circuito. Si cambia `pi_kw` o `fd`, `md_kw` se recalcula.

### `PUT /circuits/{circuit_id}/status` *(solo admin)*
Cambia el estado del circuito. Al pasar a reserva se registran fechas; al volver a `operative_normal` se borran.

**Body:** `{ "status": "reserve_r", "reserve_expires_at": "2025-12-31" }`

### `DELETE /circuits/{circuit_id}` *(solo admin)*
Elimina el circuito y sus sub-circuitos (cascade). ⚠ Irreversible.

---

## SUB-CIRCUITS *(requiere `view_circuits` para lectura, admin para escritura)*

### `GET /sub-circuits/circuit/{circuit_id}`
Lista los sub-circuitos de un circuito.

### `POST /sub-circuits/circuit/{circuit_id}` *(solo admin)*
Crea un sub-circuito.

**Body:**
```json
{
  "name": "Ampliación Taller",
  "pi_kw": 20,
  "fd": 0.7,
  "status": "operative_normal"
}
```

### `PUT /sub-circuits/{sub_circuit_id}/status` *(solo admin)*
Cambia el estado del sub-circuito.

### `DELETE /sub-circuits/{sub_circuit_id}` *(solo admin)*
Elimina el sub-circuito. ⚠ Irreversible.

---

## REQUESTS *(requiere `send_requests` para crear, admin para gestionar)*

Estados: `pending` → `approved` / `rejected`

### `GET /requests/circuit-options/{bar_id}`
Lista los circuitos disponibles para agregar un sub-circuito (para el formulario de solicitud).

### `GET /requests` *(solo admin)*
Lista todas las solicitudes del sistema.

### `GET /requests/my`
Lista las solicitudes del usuario autenticado.

### `POST /requests`
Crea una solicitud de ampliación.

**Body (nuevo circuito):**
```json
{
  "station_id": 5,
  "bar_type": "normal",
  "local_item": "Tienda 12A",
  "requested_load_kw": 30,
  "fd": 0.8,
  "justification": "Nueva tienda comercial"
}
```

**Body (sub-circuito en circuito existente):**
```json
{
  "station_id": 5,
  "bar_type": "normal",
  "circuit_id": 12,
  "requested_load_kw": 15,
  "fd": 0.7,
  "sub_circuit_name": "Punto adicional",
  "justification": "Expansión del local"
}
```

### `PUT /requests/{request_id}/approve` *(solo admin)*
Aprueba la solicitud. Crea automáticamente el circuito o sub-circuito correspondiente.

### `PUT /requests/{request_id}/reject` *(solo admin)*
Rechaza la solicitud.

**Body:** `{ "rejection_reason": "Capacidad insuficiente" }`

---

## OBSERVATIONS *(requiere `add_observations` para crear)*

Severidades: `urgent` | `warning` | `recommendation`

### `GET /observations/circuit/{circuit_id}`
Observaciones de un circuito (cualquier usuario autenticado).

### `GET /observations/bar/{bar_id}`
Observaciones de una barra.

### `POST /observations`
Crea una observación. Debe especificar al menos uno de: `circuit_id`, `sub_circuit_id`, `bar_id`.

**Body:**
```json
{
  "circuit_id": 5,
  "severity": "warning",
  "content": "Cable con desgaste visible en terminal norte"
}
```

### `DELETE /observations/{observation_id}` *(solo admin)*
Elimina la observación.

---

## NOTIFICATIONS *(solo admin)*

### `GET /notifications`
Lista notificaciones activas. Filtros: `is_read` (bool), `type` (string).

### `GET /notifications/count`
Número de notificaciones no leídas. Usado para el badge del ícono de campana.

### `PUT /notifications/{notification_id}/read`
Marca como leída.

### `PUT /notifications/{notification_id}/extend`
Extiende la fecha de vencimiento de una reserva.

**Body:** `{ "extended_until": "2025-06-30" }`

### `PUT /notifications/{notification_id}/dismiss`
Descarta permanentemente la notificación.

### `PUT /notifications/{notification_id}/resolve-reserve`
Solo para tipo `reserve_no_contact`: pone el circuito en `inactive` y descarta la notificación.

---

## PERMISSIONS

### `GET /permissions/me`
Permisos del usuario actual (cualquier usuario autenticado).

### `GET /permissions/features` *(solo admin)*
Lista de todas las features disponibles.

### `GET /permissions/users/{user_id}` *(solo admin)*
Permisos de un usuario específico.

### `PUT /permissions/users/{user_id}` *(solo admin)*
Actualiza permisos en bloque.

**Body:**
```json
{
  "permissions": [
    { "feature_key": "view_stations", "is_allowed": true },
    { "feature_key": "send_requests", "is_allowed": false }
  ]
}
```

---

## AUDIT *(solo admin)*

### `GET /audit`
Lista el historial de auditoría. Filtros: `entity_type`, `entity_id`, `user_id`, `action`, `is_flagged`, `start_date`, `end_date`, `limit`, `offset`.

### `PUT /audit/{log_id}/flag`
Marca o desmarca un log como sospechoso.

**Body:** `{ "is_flagged": true, "flag_reason": "Acceso fuera de horario" }`

### `GET /audit/export/excel`
Descarga todos los logs en formato Excel.

---

## BACKUPS *(solo admin)*

### `GET /backups`
Lista los backups disponibles.

### `POST /backups`
Crea un nuevo backup.

**Body:** `{ "description": "Backup semanal", "includes_audit": false }`

### `POST /backups/{backup_id}/restore`
⚠ **DESTRUCTIVO:** Restaura la BD al estado del backup. Borra todos los datos actuales.

### `DELETE /backups/{backup_id}`
Elimina el registro del backup.

---

## REPORTS *(requiere `view_reports`)*

### `GET /reports/demand-evolution`
Evolución de demanda por estación. Sin fechas: valores actuales. Con fechas: demanda de circuitos creados en ese rango.

**Parámetros opcionales:** `start_date` (ISO 8601), `end_date` (ISO 8601)

### `GET /reports/requests-per-station`
Conteo de solicitudes por estación y estado.

### `GET /reports/export/excel`
Descarga Excel con gráficos de demanda y solicitudes.

---

## IMAGES

### `GET /images/{entity_type}/{entity_id}`
Obtiene la imagen de una entidad. Tipos válidos: `station`, `bar`, `circuit`, `sub_circuit`.
Parámetro opcional: `sub_id`.

### `POST /images/{entity_type}/{entity_id}` *(solo admin)*
Sube o reemplaza imagen. Enviar como `multipart/form-data`:
- `file` — Archivo de imagen
- `justification` — Motivo (obligatorio)
- `sub_id` — Sub-entidad (opcional)

---

## Códigos de respuesta comunes

| Código | Significado |
|--------|-------------|
| `200` | Éxito |
| `201` | Creado |
| `204` | Sin contenido (DELETE exitoso) |
| `400` | Datos inválidos |
| `401` | No autenticado |
| `403` | Sin permisos suficientes |
| `404` | Recurso no encontrado |
| `500` | Error interno del servidor |
| `503` | Error de base de datos |
