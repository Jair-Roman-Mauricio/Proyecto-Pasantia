# Plantilla SQL — Barras, Circuitos y Sub-circuitos

Plantillas para escribir el script de carga de datos por estación.
Reemplazar los valores en MAYÚSCULAS con los datos reales.

---

## 1. Barras

Cada estación tiene exactamente 3 barras (una por tipo).

```sql
INSERT INTO bars (station_id, bar_type, name, capacity_kw, capacity_a, status)
VALUES
  ((SELECT id FROM stations WHERE code = 'CODIGO_ESTACION'), 'normal',      'NOMBRE_BARRA_NORMAL',      CAPACIDAD_KW, CAPACIDAD_A, 'operative'),
  ((SELECT id FROM stations WHERE code = 'CODIGO_ESTACION'), 'emergency',   'NOMBRE_BARRA_EMERGENCIA',  CAPACIDAD_KW, CAPACIDAD_A, 'operative'),
  ((SELECT id FROM stations WHERE code = 'CODIGO_ESTACION'), 'continuity',  'NOMBRE_BARRA_CONTINUIDAD', CAPACIDAD_KW, CAPACIDAD_A, 'operative');
```

| Campo         | Descripción                                   |
|---------------|-----------------------------------------------|
| `station_id`  | ID de la estación (se obtiene por código)     |
| `bar_type`    | `normal` · `emergency` · `continuity`         |
| `name`        | Nombre descriptivo de la barra (texto libre)  |
| `capacity_kw` | Capacidad máxima en kW (ej: `100.00`)         |
| `capacity_a`  | Capacidad máxima en A (ej: `250.00`)          |
| `status`      | `operative` (valor por defecto)               |

---

## 2. Circuitos

Un circuito pertenece a una barra. Repetir el bloque por cada tipo de barra que tenga circuitos.

```sql
INSERT INTO circuits (bar_id, denomination, description, pi_kw, fd, md_kw, status)
VALUES
  (
    (SELECT id FROM bars
      WHERE station_id = (SELECT id FROM stations WHERE code = 'CODIGO_ESTACION')
        AND bar_type = 'TIPO_BARRA'),
    'DENOMINACION',   -- ej: ESC-01
    'DESCRIPCION',    -- ej: Escalera Mecanica Acceso A
    PI_KW,            -- ej: 7.50
    FD,               -- ej: 0.70  (entre 0.00 y 1.00)
    MD_KW,            -- ej: 5.25  (= PI_KW × FD)
    'STATUS'          -- ver valores válidos abajo
  ),
  (
    (SELECT id FROM bars
      WHERE station_id = (SELECT id FROM stations WHERE code = 'CODIGO_ESTACION')
        AND bar_type = 'TIPO_BARRA'),
    'DENOMINACION',
    'DESCRIPCION',
    PI_KW,
    FD,
    MD_KW,
    'STATUS'
  );
```

| Campo         | Descripción                                   |
|---------------|-----------------------------------------------|
| `bar_id`      | ID de la barra (se obtiene por estación+tipo) |
| `denomination`| Código del circuito (ej: `ESC-01`)            |
| `description` | Nombre descriptivo del circuito               |
| `pi_kw`       | Potencia instalada en kW                      |
| `fd`          | Factor de demanda (0.00 – 1.00)               |
| `md_kw`       | Máxima demanda = `pi_kw × fd`                 |
| `status`      | Ver tabla de valores válidos                  |

---

## 3. Sub-circuitos

Un sub-circuito pertenece a un circuito.

```sql
INSERT INTO sub_circuits (circuit_id, status, denomination, description, itm, mm2, pi_kw, fd, md_kw)
VALUES
  (
    (SELECT c.id FROM circuits c
       JOIN bars b ON c.bar_id = b.id
       JOIN stations s ON b.station_id = s.id
      WHERE s.code = 'CODIGO_ESTACION'
        AND c.denomination = 'DENOMINACION_CIRCUITO'),
    'STATUS',         -- ver valores válidos abajo
    'DENOMINACION',   -- ej: SC-01
    'DESCRIPCION',    -- ej: Motor Escalera Tramo A
    'ITM',            -- ej: 32A
    'MM2',            -- ej: 4
    PI_KW,            -- ej: 3.00
    FD,               -- ej: 0.70
    MD_KW             -- ej: 2.10  (= PI_KW × FD)
  ),
  (
    (SELECT c.id FROM circuits c
       JOIN bars b ON c.bar_id = b.id
       JOIN stations s ON b.station_id = s.id
      WHERE s.code = 'CODIGO_ESTACION'
        AND c.denomination = 'DENOMINACION_CIRCUITO'),
    'STATUS',
    'DENOMINACION',
    'DESCRIPCION',
    'ITM',
    'MM2',
    PI_KW,
    FD,
    MD_KW
  );
```

| Campo         | Descripción                                          |
|---------------|------------------------------------------------------|
| `circuit_id`  | ID del circuito padre (se obtiene por estación+código)|
| `status`      | Ver tabla de valores válidos                         |
| `denomination`| Código del sub-circuito (ej: `SC-01`)                |
| `description` | Nombre descriptivo                                   |
| `itm`         | Interruptor termomagnético (ej: `32A`)               |
| `mm2`         | Sección del cable en mm² (ej: `4`)                   |
| `pi_kw`       | Potencia instalada en kW                             |
| `fd`          | Factor de demanda (0.00 – 1.00)                      |
| `md_kw`       | Máxima demanda = `pi_kw × fd`                        |

---

## Valores válidos

| Campo      | Opciones                                                               |
|------------|------------------------------------------------------------------------|
| `bar_type` | `normal` · `emergency` · `continuity`                                  |
| `status`   | `operative_normal` · `reserve_r` · `reserve_equipped_re` · `inactive` |
| `fd`       | Decimal entre `0.00` y `1.00`                                          |
| `md_kw`    | Siempre `pi_kw × fd`                                                   |
| `itm`      | Texto libre: `16A`, `32A`, `63A`, …                                    |
| `mm2`      | Texto libre: `1.5`, `2.5`, `4`, `6`, `10`, …                          |
