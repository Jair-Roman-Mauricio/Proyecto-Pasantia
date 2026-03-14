# Plantilla de Carga de Datos: Circuitos y Sub-circuitos

Plantilla SQL para ingresar datos en la base de datos.
Se usa **E14 — Arriola** como estación de ejemplo. Reemplazar el código de estación
y los valores numéricos con los datos reales antes de ejecutar.

---

## 1. Circuitos

Los circuitos se agrupan por tipo de barra: `normal`, `emergency` o `continuity`.

```sql
-- E14 — Arriola · BARRA NORMAL
INSERT INTO circuits (bar_id, denomination, description, pi_kw, fd, md_kw, status)
VALUES
  ((SELECT id FROM bars WHERE station_id=(SELECT id FROM stations WHERE code='E14') AND bar_type='normal'),
   'ESC-01', 'Escalera Mecanica Acceso A', 0.00, 0.70, 0.00, 'operative_normal'),
  ((SELECT id FROM bars WHERE station_id=(SELECT id FROM stations WHERE code='E14') AND bar_type='normal'),
   'ILU-01', 'Iluminacion Anden',          0.00, 1.00, 0.00, 'operative_normal');

-- E14 — Arriola · BARRA EMERGENCIA
INSERT INTO circuits (bar_id, denomination, description, pi_kw, fd, md_kw, status)
VALUES
  ((SELECT id FROM bars WHERE station_id=(SELECT id FROM stations WHERE code='E14') AND bar_type='emergency'),
   'IEM-01', 'Iluminacion Emergencia Anden', 0.00, 1.00, 0.00, 'operative_normal');

-- E14 — Arriola · BARRA CONTINUIDAD
INSERT INTO circuits (bar_id, denomination, description, pi_kw, fd, md_kw, status)
VALUES
  ((SELECT id FROM bars WHERE station_id=(SELECT id FROM stations WHERE code='E14') AND bar_type='continuity'),
   'CTL-01', 'Sistema de Control SCADA', 0.00, 0.90, 0.00, 'operative_normal');
```

**Columnas:**

| Columna en app | Campo SQL     | Ejemplo         |
|----------------|---------------|-----------------|
| Circuito       | `denomination`| `ESC-01`        |
| Descripcion    | `description` | `Escalera Mecanica Acceso A` |
| PI(kW)         | `pi_kw`       | `7.50`          |
| F.D            | `fd`          | `0.70`          |
| MD(kW)         | `md_kw`       | `5.25` (= PI × FD) |

---

## 2. Sub-circuitos

```sql
-- Sub-circuitos del circuito ESC-01 · E14 — Arriola
INSERT INTO sub_circuits (circuit_id, status, description, itm, mm2, pi_kw, fd, md_kw)
VALUES
  ((SELECT c.id FROM circuits c JOIN bars b ON c.bar_id=b.id JOIN stations s ON b.station_id=s.id WHERE s.code='E14' AND c.denomination='ESC-01'),
   'operative_normal', 'Motor Escalera Tramo A',    '32A', '4',   0.00, 0.70, 0.00),
  ((SELECT c.id FROM circuits c JOIN bars b ON c.bar_id=b.id JOIN stations s ON b.station_id=s.id WHERE s.code='E14' AND c.denomination='ESC-01'),
   'operative_normal', 'Alumbrado Escalera Tramo A','16A', '2.5', 0.00, 1.00, 0.00);
```

**Columnas:**

| Columna en app | Campo SQL     | Ejemplo         |
|----------------|---------------|-----------------|
| Estado         | `status`      | `operative_normal` |
| Circuito       | `description` | `Motor Escalera Tramo A` |
| Descripcion    | `description` | (campo libre)   |
| ITM            | `itm`         | `32A`           |
| MM2            | `mm2`         | `4`             |
| PI(kW)         | `pi_kw`       | `3.00`          |
| F.D            | `fd`          | `0.70`          |
| MD(kW)         | `md_kw`       | `2.10` (= PI × FD) |

---

## Referencia de valores válidos

| Campo    | Valores aceptados |
|----------|-------------------|
| `bar_type` | `normal` · `emergency` · `continuity` |
| `status` | `operative_normal` · `reserve_r` · `reserve_equipped_re` · `inactive` |
| `fd`     | Decimal entre `0.00` y `1.00` |
| `md_kw`  | `pi_kw × fd` |
| `itm`    | Texto libre: `16A`, `32A`, `63A` … |
| `mm2`    | Texto libre: `2.5`, `4`, `6`, `10` … |
