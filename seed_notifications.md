# Seed: Tabla de Notificaciones (notifications)

Script SQL para poblar la tabla `notifications` con datos de prueba representativos.
Cubre los cuatro tipos de notificacion del sistema y distintos estados (leido, no leido, descartado, extendido).

---

## Tipos de notificacion

| Tipo | Descripcion |
|------|-------------|
| `reserve_no_contact` | Circuito en reserva sin contacto con el cliente |
| `negative_energy` | Estacion con demanda que supera la capacidad del transformador |
| `request_pending` | Solicitud de Opersac pendiente de revision |
| `system` | Notificacion general del sistema |

---

## Prerrequisitos

Las 26 estaciones deben existir (ids 1–26). Verificar:
```sql
SELECT COUNT(*) FROM stations; -- debe ser 26
```

Para notificaciones con `circuit_id`, debe existir al menos un circuito.
Si no hay circuitos, usar `circuit_id = NULL`.

---

## Seed completo

```sql
-- =========================================================
-- SEED: Notificaciones de prueba
-- =========================================================

INSERT INTO notifications (station_id, circuit_id, type, message, is_read, is_dismissed, extended_until, auto_delete_at, created_at)
VALUES

-- ── TIPO: reserve_no_contact (Circuito en reserva sin contacto) ──────────────

-- No leida, sin extender
(1,  NULL, 'reserve_no_contact',
 'Circuito C-03 en Barra Normal de Villa El Salvador lleva 45 dias en reserva sin contacto con el cliente.',
 false, false, NULL, NULL,
 NOW() - INTERVAL '2 days'),

-- Leida, extendida hasta el futuro
(3,  NULL, 'reserve_no_contact',
 'Circuito CE-01 en Barra Emergencia de Pumacahua supera los 30 dias en reserva equipada sin respuesta.',
 true, false, CURRENT_DATE + INTERVAL '15 days', NULL,
 NOW() - INTERVAL '5 days'),

-- Leida, sin extender
(7,  NULL, 'reserve_no_contact',
 'Circuito CC-02 en Barra Continuidad de Atocongo: 60 dias en reserva. Se recomienda liberar el espacio.',
 true, false, NULL, NULL,
 NOW() - INTERVAL '10 days'),

-- No leida
(12, NULL, 'reserve_no_contact',
 'Circuito C-05 en Barra Normal de San Borja Sur lleva 90 dias en reserva R sin actividad registrada.',
 false, false, NULL, NULL,
 NOW() - INTERVAL '1 day'),

-- Descartada
(15, NULL, 'reserve_no_contact',
 'Circuito CE-03 en Barra Emergencia de Gamarra: cliente no ha respondido en 30 dias.',
 true, true, NULL, NULL,
 NOW() - INTERVAL '20 days'),


-- ── TIPO: negative_energy (Demanda supera capacidad del transformador) ────────

-- No leida, critica
(2,  NULL, 'negative_energy',
 'ALERTA: La demanda actual de Parque Industrial (320 kW) supera la capacidad del transformador (300 kW). Revisar circuitos activos.',
 false, false, NULL, NULL,
 NOW() - INTERVAL '3 hours'),

-- No leida
(8,  NULL, 'negative_energy',
 'Estacion Jorge Chavez con disponibilidad negativa. Demanda: 410 kW, Capacidad: 400 kW. Se requiere atencion inmediata.',
 false, false, NULL, NULL,
 NOW() - INTERVAL '6 hours'),

-- Leida
(14, NULL, 'negative_energy',
 'Arriola reporta sobrecarga de transformador. Disponible: -15 kW. Verificar circuitos en reserva que puedan desactivarse.',
 true, false, NULL, NULL,
 NOW() - INTERVAL '2 days'),

-- Leida y descartada (resuelta)
(19, NULL, 'negative_energy',
 'Caja de Agua: sobrecarga resuelta tras desactivar circuito C-07. Disponibilidad actual: +25 kW.',
 true, true, NULL, NULL,
 NOW() - INTERVAL '7 days'),


-- ── TIPO: request_pending (Solicitud pendiente de revision) ──────────────────

-- No leida - mas reciente
(1,  NULL, 'request_pending',
 'Nueva solicitud de Opersac en Villa El Salvador: instalacion de circuito para local comercial (15 kW). Pendiente de aprobacion.',
 false, false, NULL, CURRENT_DATE + INTERVAL '7 days',
 NOW() - INTERVAL '30 minutes'),

-- No leida
(5,  NULL, 'request_pending',
 'Solicitud pendiente en Maria Auxiliadora: habilitacion de cafeteria (8 kW, barra normal). Sin revisar hace 2 dias.',
 false, false, NULL, CURRENT_DATE + INTERVAL '5 days',
 NOW() - INTERVAL '2 days'),

-- No leida
(9,  NULL, 'request_pending',
 'Solicitud en Ayacucho para mejora de alumbrado (4 kW). Lleva 3 dias sin revision.',
 false, false, NULL, CURRENT_DATE + INTERVAL '4 days',
 NOW() - INTERVAL '3 days'),

-- Leida (ya revisada)
(11, NULL, 'request_pending',
 'Solicitud en Angamos para nueva sala de operaciones (20 kW) fue aprobada. Notificacion archivada.',
 true, false, NULL, NULL,
 NOW() - INTERVAL '10 days'),

-- Leida y descartada
(16, NULL, 'request_pending',
 'Solicitud rechazada en Miguel Grau: carga solicitada supera el margen disponible en barra normal.',
 true, true, NULL, NULL,
 NOW() - INTERVAL '5 days'),


-- ── TIPO: system (Notificaciones generales del sistema) ──────────────────────

-- No leida - informativa
(NULL, NULL, 'system',
 'Backup automatico completado exitosamente. Datos de todas las estaciones respaldados.',
 false, false, NULL, CURRENT_DATE + INTERVAL '30 days',
 NOW() - INTERVAL '1 hour'),

-- No leida - advertencia
(NULL, NULL, 'system',
 'El sistema detecta 3 estaciones con disponibilidad menor al 20% de capacidad. Revisar en el panel principal.',
 false, false, NULL, NULL,
 NOW() - INTERVAL '4 hours'),

-- Leida - informativa
(NULL, NULL, 'system',
 'Mantenimiento programado del sistema el proximo sabado de 02:00 a 04:00 hrs. El sistema estara en modo lectura.',
 true, false, NULL, NULL,
 NOW() - INTERVAL '3 days'),

-- Leida - actualizacion
(NULL, NULL, 'system',
 'Version 1.1.3 desplegada correctamente. Nuevas funcionalidades: filtros en auditoria, eliminacion de backups.',
 true, false, NULL, NULL,
 NOW() - INTERVAL '8 days'),

-- Descartada - antigua
(NULL, NULL, 'system',
 'Recordatorio: realizar revision mensual de circuitos en reserva segun protocolo de mantenimiento.',
 true, true, NULL, NULL,
 NOW() - INTERVAL '30 days');
```

---

## Verificacion

```sql
-- Resumen por tipo
SELECT type, COUNT(*) AS total,
       SUM(CASE WHEN is_read = false AND is_dismissed = false THEN 1 ELSE 0 END) AS no_leidas,
       SUM(CASE WHEN is_dismissed = true THEN 1 ELSE 0 END) AS descartadas
FROM notifications
GROUP BY type
ORDER BY type;

-- Ver notificaciones no leidas (las que aparecen en el panel)
SELECT id, type, LEFT(message, 60) AS mensaje, is_read, is_dismissed, created_at::date
FROM notifications
WHERE is_read = false AND is_dismissed = false
ORDER BY created_at DESC;

-- Conteo total de no leidas (lo que muestra el badge del campana)
SELECT COUNT(*) AS unread_count
FROM notifications
WHERE is_read = false AND is_dismissed = false;
```

---

## Referencia de campos

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `station_id` | int / NULL | Estacion relacionada (nullable) |
| `circuit_id` | int / NULL | Circuito relacionado (nullable) |
| `type` | string | `reserve_no_contact`, `negative_energy`, `request_pending`, `system` |
| `message` | text | Mensaje descriptivo mostrado en el panel |
| `is_read` | bool | `false` = aparece como nueva en el panel |
| `is_dismissed` | bool | `true` = descartada, no se muestra |
| `extended_until` | date / NULL | Fecha hasta la cual se extiende (para `reserve_no_contact`) |
| `auto_delete_at` | date / NULL | Fecha de eliminacion automatica |
