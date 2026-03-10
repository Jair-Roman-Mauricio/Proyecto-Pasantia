// ---------------------------------------------------------------------------
// Catálogo de estaciones de la Línea 1 del Metro de Lima
// orderIndex sigue la numeración oficial: 1 = Villa El Salvador, 26 = Bayovar
// ---------------------------------------------------------------------------
export const STATIONS = [
  { code: 'E01', name: 'Villa El Salvador', orderIndex: 1 },
  { code: 'E02', name: 'Parque Industrial', orderIndex: 2 },
  { code: 'E03', name: 'Pumacahua', orderIndex: 3 },
  { code: 'E04', name: 'Villa Maria', orderIndex: 4 },
  { code: 'E05', name: 'Maria Auxiliadora', orderIndex: 5 },
  { code: 'E06', name: 'San Juan', orderIndex: 6 },
  { code: 'E07', name: 'Atocongo', orderIndex: 7 },
  { code: 'E08', name: 'Jorge Chavez', orderIndex: 8 },
  { code: 'E09', name: 'Ayacucho', orderIndex: 9 },
  { code: 'E10', name: 'Cabitos', orderIndex: 10 },
  { code: 'E11', name: 'Angamos', orderIndex: 11 },
  { code: 'E12', name: 'San Borja Sur', orderIndex: 12 },
  { code: 'E13', name: 'La Cultura', orderIndex: 13 },
  { code: 'E14', name: 'Arriola', orderIndex: 14 },
  { code: 'E15', name: 'Gamarra', orderIndex: 15 },
  { code: 'E16', name: 'Miguel Grau', orderIndex: 16 },
  { code: 'E17', name: 'El Angel', orderIndex: 17 },
  { code: 'E18', name: 'Presbitero Maestro', orderIndex: 18 },
  { code: 'E19', name: 'Caja de Agua', orderIndex: 19 },
  { code: 'E20', name: 'Piramide del Sol', orderIndex: 20 },
  { code: 'E21', name: 'Los Jardines', orderIndex: 21 },
  { code: 'E22', name: 'Los Postes', orderIndex: 22 },
  { code: 'E23', name: 'San Carlos', orderIndex: 23 },
  { code: 'E24', name: 'San Martin', orderIndex: 24 },
  { code: 'E25', name: 'Santa Rosa', orderIndex: 25 },
  { code: 'E26', name: 'Bayovar', orderIndex: 26 },
];

// ---------------------------------------------------------------------------
// Tipos de barra eléctrica disponibles en cada estación
// ---------------------------------------------------------------------------
export const BAR_TYPES = [
  { name: 'Barra Normal', type: 'normal' },
  { name: 'Barra Emergencia', type: 'emergency' },
  { name: 'Barra Continuidad', type: 'continuity' },
];

// ---------------------------------------------------------------------------
// Colores de estado para circuitos eléctricos
// Cada valor corresponde al campo `status` de la interfaz Circuit.
// ---------------------------------------------------------------------------
export const CIRCUIT_STATUS_COLORS: Record<string, string> = {
  operative_normal: '#22c55e',   // verde — en servicio normal
  reserve_r: '#eab308',          // amarillo — en reserva sin equipar
  reserve_equipped_re: '#3b82f6', // azul — en reserva equipada
  inactive: '#6b7280',           // gris — fuera de servicio
};

// ---------------------------------------------------------------------------
// Etiquetas legibles para los estados de circuito (usadas en badges y filtros)
// ---------------------------------------------------------------------------
export const CIRCUIT_STATUS_LABELS: Record<string, string> = {
  operative_normal: 'Operativo Normal',
  reserve_r: 'Reserva (R)',
  reserve_equipped_re: 'Reserva Equipada (R/E)',
  inactive: 'Inactivo',
};

// ---------------------------------------------------------------------------
// Colores de estado energético para estaciones
// Refleja el campo `status` de la interfaz Station:
//   'red'    → debe energía (potencia disponible negativa)
//   'yellow' → menos del 20 % de potencia disponible
//   'green'  → potencia suficiente
// ---------------------------------------------------------------------------
export const STATION_STATUS_COLORS: Record<string, string> = {
  red: '#ef4444',
  yellow: '#eab308',
  green: '#22c55e',
};

// ---------------------------------------------------------------------------
// Colores de severidad para observaciones técnicas
// Usados en badges y marcadores de la interfaz de observaciones.
// ---------------------------------------------------------------------------
export const OBSERVATION_SEVERITY_COLORS: Record<string, string> = {
  urgent: '#ef4444',         // rojo — atención inmediata
  warning: '#eab308',        // amarillo — advertencia
  recommendation: '#3b82f6', // azul — sugerencia de mejora
};

// ---------------------------------------------------------------------------
// Razones predefinidas para justificar la actualización de imágenes de estación
// El usuario puede seleccionar una de estas opciones o elegir 'Otro'.
// ---------------------------------------------------------------------------
export const IMAGE_JUSTIFICATION_REASONS = [
  'Actualizacion de infraestructura',
  'Correccion de imagen',
  'Revision periodica',
  'Mantenimiento realizado',
  'Cambio de equipo',
  'Otro',
];
