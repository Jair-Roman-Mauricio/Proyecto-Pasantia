# Scripts SQL - Seed de Barras, Circuitos y Sub-circuitos

## Referencia rapida: Estaciones y Barras

| ID | Codigo | Estacion | Barra Normal | Barra Emergencia | Barra Continuidad |
|----|--------|----------|:------------:|:----------------:|:-----------------:|
| 1  | E01 | Villa El Salvador     | 1  | 2  | 3  |
| 2  | E02 | Parque Industrial     | 4  | 5  | 6  |
| 3  | E03 | Pumacahua             | 7  | 8  | 9  |
| 4  | E04 | Villa Maria           | 10 | 11 | 12 |
| 5  | E05 | Maria Auxiliadora     | 13 | 14 | 15 |
| 6  | E06 | San Juan              | 16 | 17 | 18 |
| 7  | E07 | Atocongo              | 19 | 20 | 21 |
| 8  | E08 | Jorge Chavez          | 22 | 23 | 24 |
| 9  | E09 | Ayacucho              | 25 | 26 | 27 |
| 10 | E10 | Cabitos               | 28 | 29 | 30 |
| 11 | E11 | Angamos               | 31 | 32 | 33 |
| 12 | E12 | San Borja Sur         | 34 | 35 | 36 |
| 13 | E13 | La Cultura            | 37 | 38 | 39 |
| 14 | E14 | Arriola               | 40 | 41 | 42 |
| 15 | E15 | Gamarra               | 43 | 44 | 45 |
| 16 | E16 | Miguel Grau           | 46 | 47 | 48 |
| 17 | E17 | El Angel              | 49 | 50 | 51 |
| 18 | E18 | Presbitero Maestro    | 52 | 53 | 54 |
| 19 | E19 | Caja de Agua          | 55 | 56 | 57 |
| 20 | E20 | Piramide del Sol      | 58 | 59 | 60 |
| 21 | E21 | Los Jardines          | 61 | 62 | 63 |
| 22 | E22 | Los Postes            | 64 | 65 | 66 |
| 23 | E23 | San Carlos            | 67 | 68 | 69 |
| 24 | E24 | San Martin            | 70 | 71 | 72 |
| 25 | E25 | Santa Rosa            | 73 | 74 | 75 |
| 26 | E26 | Bayovar               | 76 | 77 | 78 |

Formula: Barra Normal = `(station_id * 3) - 2`, Emergencia = `(station_id * 3) - 1`, Continuidad = `station_id * 3`

---

## Valores de referencia

**status de circuito:** `operative_normal`, `reserve_r`, `reserve_equipped_re`
**status de sub-circuito:** `operative_normal`, `reserve_r`, `reserve_equipped_re`
**bar_type:** `normal`, `emergency`, `continuity`
**MD se calcula como:** `pi_kw * fd`
**reserve_expires_at:** fecha hasta la cual es válida la reserva (DATE). El sistema genera una notificación automática cuando esta fecha es alcanzada.

---

## 1. Actualizar capacidad del transformador de una estacion

```sql
-- Estacion: _____ (ID: ___)
-- Capacidad real del transformador en kW
UPDATE stations
SET transformer_capacity_kw = ___,
    available_power_kw = ___ - max_demand_kw,
    updated_at = NOW()
WHERE id = ___;
```

---

## 2. Actualizar capacidad de barras de una estacion

```sql
-- Estacion: _____ (ID: ___)
-- Barra Normal (ID: ___)
UPDATE bars SET capacity_kw = ___, capacity_a = ___, updated_at = NOW() WHERE id = ___;
-- Barra Emergencia (ID: ___)
UPDATE bars SET capacity_kw = ___, capacity_a = ___, updated_at = NOW() WHERE id = ___;
-- Barra Continuidad (ID: ___)
UPDATE bars SET capacity_kw = ___, capacity_a = ___, updated_at = NOW() WHERE id = ___;
```

---

## 3. Insertar circuito normal (no UPS)

```sql
-- Estacion: _____ | Barra: _____ (bar_id: ___)
INSERT INTO circuits (bar_id, denomination, name, description, local_item, pi_kw, fd, md_kw, status, is_ups, created_at, updated_at)
VALUES (
    ___,              -- bar_id
    '___',            -- denomination (ej: 'C-01')
    '___',            -- name (ej: 'Alumbrado Pasillo')
    '___',            -- description (NULL si no hay)
    '___',            -- local_item (NULL si no hay)
    ___,              -- pi_kw (potencia instalada)
    ___,              -- fd (factor de demanda, ej: 1.0000)
    ___,              -- md_kw (= pi_kw * fd)
    'operative_normal', -- status
    false,            -- is_ups
    NOW(), NOW()
);
```

---

## 4. Insertar circuito UPS (conectado a 3 barras)

```sql
-- Estacion: _____ | Barra primaria: _____ (bar_id: ___)
-- Conexion 1: _____ (secondary_bar_id: ___) | Conexion 2: _____ (tertiary_bar_id: ___)
INSERT INTO circuits (bar_id, secondary_bar_id, tertiary_bar_id, denomination, name, description, local_item, pi_kw, fd, md_kw, status, is_ups, created_at, updated_at)
VALUES (
    ___,              -- bar_id (barra primaria)
    ___,              -- secondary_bar_id (conexion 1)
    ___,              -- tertiary_bar_id (conexion 2)
    '___',            -- denomination
    '___',            -- name
    '___',            -- description (NULL si no hay)
    '___',            -- local_item (NULL si no hay)
    ___,              -- pi_kw
    ___,              -- fd
    ___,              -- md_kw (= pi_kw * fd)
    'operative_normal',
    true,             -- is_ups = true
    NOW(), NOW()
);
```

---

## 5. Insertar circuito en reserva

```sql
-- Circuito en reserva (R) o reserva equipada (R/E)
-- reserve_since: fecha de inicio (hoy)
-- reserve_expires_at: fecha hasta la cual es válida la reserva (el sistema notificará al llegar)
INSERT INTO circuits (bar_id, denomination, name, description, local_item, pi_kw, fd, md_kw, status, is_ups, reserve_since, reserve_expires_at, created_at, updated_at)
VALUES (
    ___,              -- bar_id
    '___',            -- denomination
    '___',            -- name
    '___',            -- description
    '___',            -- local_item
    ___,              -- pi_kw
    ___,              -- fd
    ___,              -- md_kw
    'reserve_r',      -- o 'reserve_equipped_re'
    false,
    CURRENT_DATE,     -- reserve_since (inicio de la reserva)
    '____-__-__',     -- reserve_expires_at (ej: '2026-04-15', fecha de vencimiento)
    NOW(), NOW()
);
```

---

## 6. Insertar sub-circuito operativo

```sql
-- Circuito padre: _____ (circuit_id: ___)
INSERT INTO sub_circuits (circuit_id, name, description, itm, mm2, pi_kw, fd, md_kw, status, created_at, updated_at)
VALUES (
    ___,               -- circuit_id
    '___',             -- name (denominacion del sub-circuito)
    '___',             -- description (NULL si no hay)
    '___',             -- itm (ej: '3x20A', NULL si no hay)
    '___',             -- mm2 (ej: '3x4mm2', NULL si no hay)
    ___,               -- pi_kw
    ___,               -- fd
    ___,               -- md_kw (= pi_kw * fd)
    'operative_normal',-- status
    NOW(), NOW()
);
```

---

## 6b. Insertar sub-circuito en reserva

```sql
-- Sub-circuito en reserva (R) o reserva equipada (R/E)
-- reserve_expires_at: fecha de vencimiento que dispara la notificación automática
INSERT INTO sub_circuits (circuit_id, name, description, itm, mm2, pi_kw, fd, md_kw, status, reserve_since, reserve_expires_at, created_at, updated_at)
VALUES (
    ___,              -- circuit_id
    '___',            -- name
    '___',            -- description (NULL si no hay)
    '___',            -- itm (NULL si no hay)
    '___',            -- mm2 (NULL si no hay)
    ___,              -- pi_kw
    ___,              -- fd
    ___,              -- md_kw
    'reserve_r',      -- o 'reserve_equipped_re'
    CURRENT_DATE,     -- reserve_since (inicio de la reserva)
    '____-__-__',     -- reserve_expires_at (ej: '2026-04-15', fecha de vencimiento)
    NOW(), NOW()
);
```

---

## 7. Recalcular energia de una estacion (EJECUTAR DESPUES DE INSERTAR CIRCUITOS)

```sql
-- Recalcular estacion ID: ___
-- Esto suma md_kw de circuitos + sub-circuitos activos
WITH totals AS (
    SELECT COALESCE(SUM(c.md_kw), 0) + COALESCE(SUM(sc.md_kw), 0) AS total_md
    FROM bars b
    LEFT JOIN circuits c ON c.bar_id = b.id AND c.status != 'inactive'
    LEFT JOIN sub_circuits sc ON sc.circuit_id = c.id
    WHERE b.station_id = ___
)
UPDATE stations
SET max_demand_kw = t.total_md,
    available_power_kw = transformer_capacity_kw - t.total_md,
    status = CASE
        WHEN transformer_capacity_kw - t.total_md < 0 THEN 'red'
        WHEN (transformer_capacity_kw - t.total_md) / NULLIF(transformer_capacity_kw, 0) < 0.2 THEN 'yellow'
        ELSE 'green'
    END,
    updated_at = NOW()
FROM totals t
WHERE stations.id = ___;
```

---

## MIGRACION: Actualizar tablas existentes en BD

> **Importante:** `create_all()` solo crea tablas nuevas. Si la BD ya existia antes de los cambios al modelo, ejecuta este SQL una sola vez en PostgreSQL (psql o pgAdmin).

```sql
-- =====================================================
-- MIGRACION: Columnas nuevas en sub_circuits y circuits
-- Ejecutar UNA SOLA VEZ si las tablas ya existian
-- =====================================================

-- Agregar columnas nuevas a sub_circuits
ALTER TABLE sub_circuits
    ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'operative_normal',
    ADD COLUMN IF NOT EXISTS reserve_since DATE NULL,
    ADD COLUMN IF NOT EXISTS reserve_expires_at DATE NULL;

CREATE INDEX IF NOT EXISTS ix_sub_circuits_status ON sub_circuits (status);

-- Agregar columnas nuevas a circuits (si no existen)
ALTER TABLE circuits
    ADD COLUMN IF NOT EXISTS reserve_since DATE NULL,
    ADD COLUMN IF NOT EXISTS reserve_expires_at DATE NULL,
    ADD COLUMN IF NOT EXISTS client_last_contact DATE NULL;

-- Verificar que las columnas se crearon:
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name IN ('sub_circuits', 'circuits')
  AND column_name IN ('status', 'reserve_since', 'reserve_expires_at', 'client_last_contact')
ORDER BY table_name, column_name;
```
---

## 8. Recalcular TODAS las estaciones de una vez

```sql
WITH station_totals AS (
    SELECT
        b.station_id,
        COALESCE(SUM(c.md_kw), 0) + COALESCE(SUM(sc.md_kw), 0) AS total_md
    FROM bars b
    LEFT JOIN circuits c ON c.bar_id = b.id AND c.status != 'inactive'
    LEFT JOIN sub_circuits sc ON sc.circuit_id = c.id
    GROUP BY b.station_id
)
UPDATE stations s
SET max_demand_kw = st.total_md,
    available_power_kw = s.transformer_capacity_kw - st.total_md,
    status = CASE
        WHEN s.transformer_capacity_kw - st.total_md < 0 THEN 'red'
        WHEN (s.transformer_capacity_kw - st.total_md) / NULLIF(s.transformer_capacity_kw, 0) < 0.2 THEN 'yellow'
        ELSE 'green'
    END,
    updated_at = NOW()
FROM station_totals st
WHERE s.id = st.station_id;
```

---

## 9. Consultas utiles

```sql
-- Ver circuitos de una barra especifica
SELECT id, denomination, name, pi_kw, fd, md_kw, status, is_ups
FROM circuits WHERE bar_id = ___ ORDER BY id;

-- Ver sub-circuitos de un circuito
SELECT id, name, itm, mm2, pi_kw, fd, md_kw, status, reserve_since, reserve_expires_at
FROM sub_circuits WHERE circuit_id = ___ ORDER BY id;

-- Resumen de potencia por estacion
SELECT s.code, s.name, s.transformer_capacity_kw, s.max_demand_kw, s.available_power_kw, s.status
FROM stations s ORDER BY s.order_index;

-- Contar circuitos por barra de una estacion
SELECT b.name, b.bar_type, COUNT(c.id) as num_circuits,
       COALESCE(SUM(c.pi_kw), 0) as total_pi, COALESCE(SUM(c.md_kw), 0) as total_md
FROM bars b
LEFT JOIN circuits c ON c.bar_id = b.id
WHERE b.station_id = ___
GROUP BY b.id, b.name, b.bar_type ORDER BY b.id;

-- Ver circuitos en reserva con su fecha de vencimiento
SELECT c.id, c.denomination, c.name, c.status, c.reserve_since, c.reserve_expires_at,
       b.name AS barra, s.name AS estacion
FROM circuits c
JOIN bars b ON c.bar_id = b.id
JOIN stations s ON b.station_id = s.id
WHERE c.status IN ('reserve_r', 'reserve_equipped_re')
ORDER BY c.reserve_expires_at ASC NULLS LAST;

-- Ver reservas que vencen hoy o ya vencieron (las que generan notificacion)
SELECT c.id, c.denomination, c.name, c.reserve_expires_at, s.name AS estacion
FROM circuits c
JOIN bars b ON c.bar_id = b.id
JOIN stations s ON b.station_id = s.id
WHERE c.status IN ('reserve_r', 'reserve_equipped_re')
  AND c.reserve_expires_at <= CURRENT_DATE;

-- Limpiar todos los circuitos de una estacion (CUIDADO)
-- DELETE FROM circuits WHERE bar_id IN (SELECT id FROM bars WHERE station_id = ___);
```

---

## EJEMPLO COMPLETO: Estacion Villa El Salvador (ID: 1)

```sql
-- ============================================
-- ESTACION: Villa El Salvador (ID: 1, E01)
-- Barras: Normal=1, Emergencia=2, Continuidad=3
-- ============================================

-- Paso 1: Actualizar capacidad del transformador
UPDATE stations SET transformer_capacity_kw = 500, updated_at = NOW() WHERE id = 1;

-- Paso 2: Actualizar capacidades de barras
UPDATE bars SET capacity_kw = 200, capacity_a = 300, updated_at = NOW() WHERE id = 1; -- Normal
UPDATE bars SET capacity_kw = 150, capacity_a = 250, updated_at = NOW() WHERE id = 2; -- Emergencia
UPDATE bars SET capacity_kw = 100, capacity_a = 200, updated_at = NOW() WHERE id = 3; -- Continuidad

-- Paso 3: Circuitos en Barra Normal (bar_id = 1)
INSERT INTO circuits (bar_id, denomination, name, description, local_item, pi_kw, fd, md_kw, status, is_ups, created_at, updated_at) VALUES
(1, 'C-01', 'Alumbrado General', 'Iluminacion pasillos y hall', 'Local 101', 25.00, 0.8000, 20.00, 'operative_normal', false, NOW(), NOW()),
(1, 'C-02', 'Tomacorrientes', 'Tomas de corriente generales', 'Local 102', 15.00, 0.6000, 9.00, 'operative_normal', false, NOW(), NOW()),
(1, 'C-03', 'Escaleras Mecanicas', 'Escaleras 1 y 2', NULL, 50.00, 0.9000, 45.00, 'operative_normal', false, NOW(), NOW()),
(1, 'C-04', 'Reserva Futura', NULL, NULL, 30.00, 1.0000, 30.00, 'reserve_r', false, NOW(), NOW());
-- Nota: Si el circuito en reserva tiene fecha de vencimiento, usar la seccion 5 con reserve_since y reserve_expires_at

-- Paso 4: Circuitos en Barra Emergencia (bar_id = 2)
INSERT INTO circuits (bar_id, denomination, name, description, local_item, pi_kw, fd, md_kw, status, is_ups, created_at, updated_at) VALUES
(2, 'CE-01', 'Alumbrado Emergencia', 'Luces de emergencia', NULL, 10.00, 1.0000, 10.00, 'operative_normal', false, NOW(), NOW()),
(2, 'CE-02', 'Sistema Contra Incendios', 'Bombas y detectores', NULL, 20.00, 0.5000, 10.00, 'operative_normal', false, NOW(), NOW());

-- Paso 5: Circuitos en Barra Continuidad (bar_id = 3)
INSERT INTO circuits (bar_id, denomination, name, description, local_item, pi_kw, fd, md_kw, status, is_ups, created_at, updated_at) VALUES
(3, 'CC-01', 'Servidores', 'Rack de comunicaciones', 'Cuarto tecnico', 8.00, 1.0000, 8.00, 'operative_normal', false, NOW(), NOW()),
(3, 'CC-02', 'CCTV', 'Camaras de seguridad', NULL, 5.00, 0.8000, 4.00, 'operative_normal', false, NOW(), NOW());

-- Paso 6: Circuito UPS (ejemplo: nace de Normal, conecta a Emergencia y Continuidad)
INSERT INTO circuits (bar_id, secondary_bar_id, tertiary_bar_id, denomination, name, description, local_item, pi_kw, fd, md_kw, status, is_ups, created_at, updated_at) VALUES
(1, 2, 3, 'UPS-01', 'UPS Principal', 'UPS de estacion', NULL, 12.00, 1.0000, 12.00, 'operative_normal', true, NOW(), NOW());

-- Paso 7: Sub-circuitos (ejemplo: para el circuito 'Alumbrado General', necesitas el circuit_id)
-- Primero obtener el ID: SELECT id FROM circuits WHERE bar_id = 1 AND denomination = 'C-01';
-- Supongamos que el ID es 10:
INSERT INTO sub_circuits (circuit_id, name, description, itm, mm2, pi_kw, fd, md_kw, status, created_at, updated_at) VALUES
(10, 'Alumbrado Hall Norte', 'Luminarias LED hall norte', '3x20A', '3x2.5mm2', 8.00, 0.8000, 6.40, 'operative_normal', NOW(), NOW()),
(10, 'Alumbrado Hall Sur',   'Luminarias LED hall sur',  '3x20A', '3x2.5mm2', 8.00, 0.8000, 6.40, 'operative_normal', NOW(), NOW()),
(10, 'Alumbrado Pasillo',    'Luminarias pasillo principal', '3x16A', '3x2.5mm2', 9.00, 0.8000, 7.20, 'operative_normal', NOW(), NOW());

-- Paso 8: Recalcular energia de la estacion
WITH totals AS (
    SELECT COALESCE(SUM(c.md_kw), 0) + COALESCE(SUM(sc.md_kw), 0) AS total_md
    FROM bars b
    LEFT JOIN circuits c ON c.bar_id = b.id AND c.status != 'inactive'
    LEFT JOIN sub_circuits sc ON sc.circuit_id = c.id
    WHERE b.station_id = 1
)
UPDATE stations
SET max_demand_kw = t.total_md,
    available_power_kw = transformer_capacity_kw - t.total_md,
    status = CASE
        WHEN transformer_capacity_kw - t.total_md < 0 THEN 'red'
        WHEN (transformer_capacity_kw - t.total_md) / NULLIF(transformer_capacity_kw, 0) < 0.2 THEN 'yellow'
        ELSE 'green'
    END,
    updated_at = NOW()
FROM totals t
WHERE stations.id = 1;
```

---

## PLANTILLA VACIA PARA COPIAR Y LLENAR

```sql
-- ============================================
-- ESTACION: __________ (ID: ___, E___)
-- Barras: Normal=___, Emergencia=___, Continuidad=___
-- ============================================

-- Capacidad del transformador
UPDATE stations SET transformer_capacity_kw = ___, updated_at = NOW() WHERE id = ___;

-- Capacidades de barras
UPDATE bars SET capacity_kw = ___, capacity_a = ___, updated_at = NOW() WHERE id = ___; -- Normal
UPDATE bars SET capacity_kw = ___, capacity_a = ___, updated_at = NOW() WHERE id = ___; -- Emergencia
UPDATE bars SET capacity_kw = ___, capacity_a = ___, updated_at = NOW() WHERE id = ___; -- Continuidad

-- Circuitos Barra Normal (bar_id = ___)
INSERT INTO circuits (bar_id, denomination, name, description, local_item, pi_kw, fd, md_kw, status, is_ups, created_at, updated_at) VALUES
(___, '___', '___', '___', '___', ___, ___, ___, 'operative_normal', false, NOW(), NOW());

-- Circuitos Barra Emergencia (bar_id = ___)
INSERT INTO circuits (bar_id, denomination, name, description, local_item, pi_kw, fd, md_kw, status, is_ups, created_at, updated_at) VALUES
(___, '___', '___', '___', '___', ___, ___, ___, 'operative_normal', false, NOW(), NOW());

-- Circuitos Barra Continuidad (bar_id = ___)
INSERT INTO circuits (bar_id, denomination, name, description, local_item, pi_kw, fd, md_kw, status, is_ups, created_at, updated_at) VALUES
(___, '___', '___', '___', '___', ___, ___, ___, 'operative_normal', false, NOW(), NOW());

-- Sub-circuitos (circuit_id = ___)
-- Primero obtener el ID: SELECT id FROM circuits WHERE bar_id = ___ AND denomination = '___';
INSERT INTO sub_circuits (circuit_id, name, description, itm, mm2, pi_kw, fd, md_kw, status, created_at, updated_at) VALUES
(___, '___', '___', '___', '___', ___, ___, ___, 'operative_normal', NOW(), NOW());

-- Recalcular energia
WITH totals AS (
    SELECT COALESCE(SUM(c.md_kw), 0) + COALESCE(SUM(sc.md_kw), 0) AS total_md
    FROM bars b
    LEFT JOIN circuits c ON c.bar_id = b.id AND c.status != 'inactive'
    LEFT JOIN sub_circuits sc ON sc.circuit_id = c.id
    WHERE b.station_id = ___
)
UPDATE stations
SET max_demand_kw = t.total_md,
    available_power_kw = transformer_capacity_kw - t.total_md,
    status = CASE
        WHEN transformer_capacity_kw - t.total_md < 0 THEN 'red'
        WHEN (transformer_capacity_kw - t.total_md) / NULLIF(transformer_capacity_kw, 0) < 0.2 THEN 'yellow'
        ELSE 'green'
    END,
    updated_at = NOW()
FROM totals t
WHERE stations.id = ___;
```
