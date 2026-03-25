-- ============================================================
-- Seed: 26 estaciones + 3 barras por estación en schema Subest
-- Ejecutar en Supabase Studio → SQL Editor
-- ============================================================

-- Insertar estaciones
INSERT INTO "Subest".stations (code, name, order_index, transformer_capacity_kw, max_demand_kw, available_power_kw, status)
VALUES
  ('E01', 'Villa El Salvador',     1,  500, 0, 500, 'green'),
  ('E02', 'Parque Industrial',     2,  500, 0, 500, 'green'),
  ('E03', 'Pumacahua',             3,  500, 0, 500, 'green'),
  ('E04', 'Villa Maria',           4,  500, 0, 500, 'green'),
  ('E05', 'Maria Auxiliadora',     5,  500, 0, 500, 'green'),
  ('E06', 'San Juan',              6,  500, 0, 500, 'green'),
  ('E07', 'Atocongo',              7,  500, 0, 500, 'green'),
  ('E08', 'Jorge Chavez',          8,  500, 0, 500, 'green'),
  ('E09', 'Ayacucho',              9,  500, 0, 500, 'green'),
  ('E10', 'Cabitos',               10, 500, 0, 500, 'green'),
  ('E11', 'Angamos',               11, 500, 0, 500, 'green'),
  ('E12', 'San Borja Sur',         12, 500, 0, 500, 'green'),
  ('E13', 'La Cultura',            13, 500, 0, 500, 'green'),
  ('E14', 'Arriola',               14, 500, 0, 500, 'green'),
  ('E15', 'Gamarra',               15, 500, 0, 500, 'green'),
  ('E16', 'Miguel Grau',           16, 500, 0, 500, 'green'),
  ('E17', 'El Angel',              17, 500, 0, 500, 'green'),
  ('E18', 'Presbitero Maestro',    18, 500, 0, 500, 'green'),
  ('E19', 'Caja de Agua',          19, 500, 0, 500, 'green'),
  ('E20', 'Piramide del Sol',      20, 500, 0, 500, 'green'),
  ('E21', 'Los Jardines',          21, 500, 0, 500, 'green'),
  ('E22', 'Los Postes',            22, 500, 0, 500, 'green'),
  ('E23', 'San Carlos',            23, 500, 0, 500, 'green'),
  ('E24', 'San Martin',            24, 500, 0, 500, 'green'),
  ('E25', 'Santa Rosa',            25, 500, 0, 500, 'green'),
  ('E26', 'Bayovar',               26, 500, 0, 500, 'green')
ON CONFLICT (code) DO NOTHING;

-- Insertar 3 barras por cada estación
INSERT INTO "Subest".bars (station_id, name, bar_type, status, capacity_kw, capacity_a)
SELECT s.id, 'Barra Normal',      'normal',      'operative', 200, 300 FROM "Subest".stations s
UNION ALL
SELECT s.id, 'Barra Emergencia',  'emergency',   'operative', 200, 300 FROM "Subest".stations s
UNION ALL
SELECT s.id, 'Barra Continuidad', 'continuity',  'operative', 200, 300 FROM "Subest".stations s
ON CONFLICT DO NOTHING;
