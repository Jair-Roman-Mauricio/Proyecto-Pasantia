# Plantilla de Carga de Datos: Barras y Circuitos

Plantilla SQL para poblar la base de datos con los datos reales de cada estación.
Se usa **E14 — Arriola** como estación de ejemplo. Reemplazar el código de estación
y los valores numéricos con los datos reales antes de ejecutar.

---

## 1. Barras (tableros)

Cada estación tiene 3 barras creadas automáticamente al hacer el seed inicial de estaciones.
Solo es necesario actualizar su capacidad nominal.

```sql
-- E14 — Arriola
-- Reemplazar 'E14' por el código de la estación y los valores 0.00 con los datos reales.

UPDATE bars
   SET capacity_kw = 0.00,
       capacity_a  = 0.00
 WHERE station_id = (SELECT id FROM stations WHERE code = 'E14')
   AND bar_type = 'normal';

UPDATE bars
   SET capacity_kw = 0.00,
       capacity_a  = 0.00
 WHERE station_id = (SELECT id FROM stations WHERE code = 'E14')
   AND bar_type = 'emergency';

UPDATE bars
   SET capacity_kw = 0.00,
       capacity_a  = 0.00
 WHERE station_id = (SELECT id FROM stations WHERE code = 'E14')
   AND bar_type = 'continuity';
```

---

## 2. Circuitos

Cada circuito pertenece a una barra. La barra se referencia mediante una subquery
que la identifica por estación y tipo.

**Campos:**

| Campo | Tipo | Descripción |
|---|---|---|
| `bar_id` | FK | ID de la barra a la que pertenece el circuito |
| `denomination` | texto | Código corto del circuito (ej: `ESC-01`) |
| `name` | texto | Nombre del tablero o carga |
| `description` | texto | Descripción adicional (opcional, puede ser `NULL`) |
| `pi_kw` | decimal | Potencia Instalada en kW |
| `fd` | decimal | Factor de Demanda (0.00 a 1.00) |
| `md_kw` | decimal | Demanda Máxima = PI × FD |
| `status` | enum | Estado del circuito (ver tabla de referencia) |
| `is_ups` | booleano | `true` si el circuito es alimentado por UPS |

```sql
-- -------------------------------------------------------
-- BARRA NORMAL — cargas en servicio regular
-- -------------------------------------------------------
INSERT INTO circuits (bar_id, denomination, name, description, pi_kw, fd, md_kw, status, is_ups)
VALUES
  (
    (SELECT id FROM bars WHERE station_id=(SELECT id FROM stations WHERE code='E14') AND bar_type='normal'),
    'ESC-01', 'Escalera Mecanica Acceso A', NULL,
    0.00, 0.70, 0.00, 'operative_normal', false
  ),
  (
    (SELECT id FROM bars WHERE station_id=(SELECT id FROM stations WHERE code='E14') AND bar_type='normal'),
    'ILU-01', 'Iluminacion Anden', NULL,
    0.00, 1.00, 0.00, 'operative_normal', false
  ),
  (
    (SELECT id FROM bars WHERE station_id=(SELECT id FROM stations WHERE code='E14') AND bar_type='normal'),
    'TOM-01', 'Tomacorrientes Generales', NULL,
    0.00, 0.50, 0.00, 'operative_normal', false
  );

-- -------------------------------------------------------
-- BARRA EMERGENCIA — cargas críticas con respaldo
-- -------------------------------------------------------
INSERT INTO circuits (bar_id, denomination, name, description, pi_kw, fd, md_kw, status, is_ups)
VALUES
  (
    (SELECT id FROM bars WHERE station_id=(SELECT id FROM stations WHERE code='E14') AND bar_type='emergency'),
    'IEM-01', 'Iluminacion Emergencia Anden', NULL,
    0.00, 1.00, 0.00, 'operative_normal', false
  ),
  (
    (SELECT id FROM bars WHERE station_id=(SELECT id FROM stations WHERE code='E14') AND bar_type='emergency'),
    'BIN-01', 'Bomba Contra Incendio Principal', NULL,
    0.00, 1.00, 0.00, 'operative_normal', false
  );

-- -------------------------------------------------------
-- BARRA CONTINUIDAD — cargas UPS (sistemas de control)
-- -------------------------------------------------------
INSERT INTO circuits (bar_id, denomination, name, description, pi_kw, fd, md_kw, status, is_ups)
VALUES
  (
    (SELECT id FROM bars WHERE station_id=(SELECT id FROM stations WHERE code='E14') AND bar_type='continuity'),
    'CTL-01', 'Sistema de Control SCADA', NULL,
    0.00, 0.90, 0.00, 'operative_normal', true
  ),
  (
    (SELECT id FROM bars WHERE station_id=(SELECT id FROM stations WHERE code='E14') AND bar_type='continuity'),
    'CCTV-01', 'Sistema de Vigilancia CCTV', NULL,
    0.00, 0.90, 0.00, 'operative_normal', true
  );
```

---

## 3. Sub-circuitos

Los sub-circuitos son cargas derivadas de un circuito principal.
Incluyen especificaciones técnicas del conductor (ITM y MM2).

**Campos:**

| Campo | Tipo | Descripción |
|---|---|---|
| `circuit_id` | FK | ID del circuito padre |
| `name` | texto | Nombre de la carga derivada |
| `description` | texto | Descripción adicional (opcional) |
| `itm` | texto | Referencia del interruptor termomagnético (ej: `32A`) |
| `mm2` | texto | Sección del conductor en mm² (ej: `4`) |
| `pi_kw` | decimal | Potencia Instalada en kW |
| `fd` | decimal | Factor de Demanda (0.00 a 1.00) |
| `md_kw` | decimal | Demanda Máxima = PI × FD |
| `status` | enum | Estado del sub-circuito (ver tabla de referencia) |

```sql
-- Sub-circuitos del circuito ESC-01 de la estación E14
-- Reemplazar el denomination y código de estación según corresponda.

INSERT INTO sub_circuits (circuit_id, name, description, itm, mm2, pi_kw, fd, md_kw, status)
VALUES
  (
    (SELECT c.id FROM circuits c
       JOIN bars b ON c.bar_id = b.id
       JOIN stations s ON b.station_id = s.id
      WHERE s.code = 'E14' AND c.denomination = 'ESC-01'),
    'Motor Escalera Tramo A', NULL,
    '32A', '4',
    0.00, 0.70, 0.00, 'operative_normal'
  ),
  (
    (SELECT c.id FROM circuits c
       JOIN bars b ON c.bar_id = b.id
       JOIN stations s ON b.station_id = s.id
      WHERE s.code = 'E14' AND c.denomination = 'ESC-01'),
    'Alumbrado Escalera Tramo A', NULL,
    '16A', '2.5',
    0.00, 1.00, 0.00, 'operative_normal'
  );
```

---

## Referencia de valores válidos

| Campo | Valores aceptados |
|---|---|
| `bar_type` | `normal` · `emergency` · `continuity` |
| `status` (circuit / sub_circuit) | `operative_normal` · `reserve_r` · `reserve_equipped_re` · `inactive` |
| `is_ups` | `true` · `false` |
| `fd` | Decimal entre `0.00` y `1.00` |
| `md_kw` | Debe calcularse como `pi_kw × fd` antes de insertar |
| `itm` | Texto libre, ej: `16A`, `32A`, `63A` |
| `mm2` | Texto libre, ej: `2.5`, `4`, `6`, `10` |
