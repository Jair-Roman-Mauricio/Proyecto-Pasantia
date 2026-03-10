/**
 * Representa a un usuario registrado en el sistema con su rol y estado de cuenta.
 * Los roles posibles son 'admin' (acceso total) y 'opersac' (acceso restringido por permisos).
 */
export interface User {
  id: number;
  username: string;
  full_name: string;
  /** Rol del usuario: 'admin' tiene acceso completo; 'opersac' solo accede según permisos asignados */
  role: 'admin' | 'opersac';
  /** Estado de la cuenta: 'reported' indica que el usuario tiene observaciones pendientes */
  status: 'active' | 'inactive' | 'reported';
  created_at: string;
  updated_at: string;
}

/**
 * Versión reducida del usuario usada en el payload del token JWT y en el contexto de autenticación.
 * Incluye solo los campos necesarios para renderizar la interfaz sin exponer datos sensibles.
 */
export interface UserBrief {
  id: number;
  username: string;
  full_name: string;
  role: string;
  /** Mapa de claves de permiso a booleano; indica qué funcionalidades tiene habilitadas el usuario */
  permissions?: Record<string, boolean>;
}

/**
 * Respuesta de la API al iniciar sesión correctamente.
 * El token debe almacenarse en localStorage para ser adjuntado en solicitudes posteriores.
 */
export interface LoginResponse {
  access_token: string;
  /** Tipo de token; siempre 'bearer' en este sistema */
  token_type: string;
  user: UserBrief;
}

/**
 * Estación de la Línea 1 del Metro de Lima con su capacidad eléctrica actual.
 * El estado de energía ('status') se calcula en el backend a partir de la potencia disponible.
 */
export interface Station {
  id: number;
  /** Código alfanumérico de la estación (p.ej. 'E01', 'E26') */
  code: string;
  name: string;
  /** Posición ordinal en la línea: 1 = Villa El Salvador, 26 = Bayovar */
  order_index: number;
  transformer_capacity_kw: number;
  max_demand_kw: number;
  /**
   * Potencia disponible en kW (capacidad del transformador menos la demanda máxima).
   * Puede ser negativa cuando la demanda supera la capacidad instalada.
   */
  available_power_kw: number;
  /**
   * Estado energético de la estación:
   * - 'green': potencia suficiente (>20 % disponible)
   * - 'yellow': menos del 20 % disponible
   * - 'red': debe energía (available_power_kw negativo)
   */
  status: 'red' | 'yellow' | 'green';
  created_at: string;
  updated_at: string;
}

/**
 * Resumen de potencia de una estación, utilizado en las vistas de reportes y dashboard.
 * Equivale a los campos energéticos de {@link Station} sin los metadatos de auditoría.
 */
export interface PowerSummary {
  station_id: number;
  station_name: string;
  transformer_capacity_kw: number;
  max_demand_kw: number;
  /** Puede ser negativo si la demanda supera la capacidad del transformador */
  available_power_kw: number;
  status: string;
}

/**
 * Barra eléctrica dentro de una estación.
 * Agrupa circuitos según su tipo de alimentación (normal, emergencia o continuidad).
 */
export interface Bar {
  id: number;
  station_id: number;
  name: string;
  /** Tipo de barra: 'normal' (red principal), 'emergency' (grupo electrógeno), 'continuity' (UPS) */
  bar_type: 'normal' | 'emergency' | 'continuity';
  /** 'operative': en servicio; 'inactive': fuera de operación */
  status: 'operative' | 'inactive';
  capacity_kw: number;
  capacity_a: number;
  created_at: string;
  updated_at: string;
}

/**
 * Circuito eléctrico conectado a una barra de una estación.
 * Puede tener barras secundaria y terciaria para alimentación redundante.
 */
export interface Circuit {
  id: number;
  bar_id: number;
  /** Barra de respaldo; null si el circuito no tiene alimentación secundaria */
  secondary_bar_id: number | null;
  /** Barra terciaria de respaldo; null en la mayoría de los circuitos */
  tertiary_bar_id: number | null;
  denomination: string;
  name: string;
  description: string | null;
  /** Ítem local de referencia física en la estación (plano o etiqueta de tablero) */
  local_item: string | null;
  /** Potencia instalada en kW */
  pi_kw: number;
  /** Factor de demanda (0-1); multiplica pi_kw para obtener md_kw */
  fd: number;
  /** Máxima demanda en kW (pi_kw × fd) */
  md_kw: number;
  /**
   * Estado operativo del circuito:
   * - 'operative_normal': en servicio normal
   * - 'reserve_r': en reserva sin equipar
   * - 'reserve_equipped_re': en reserva equipada
   * - 'inactive': fuera de servicio
   */
  status: 'operative_normal' | 'reserve_r' | 'reserve_equipped_re' | 'inactive';
  /** Indica si el circuito está alimentado por un UPS */
  is_ups: boolean;
  /** Fecha desde la que el circuito está en estado de reserva; null si no aplica */
  reserve_since: string | null;
  /** Fecha de vencimiento del período de reserva; null si no aplica */
  reserve_expires_at: string | null;
  /** Última vez que el cliente (carga) realizó contacto o consumo; null si no aplica */
  client_last_contact: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Sub-circuito dentro de un circuito principal.
 * Representa subdivisiones de carga con su propio calibre de cable y protección.
 */
export interface SubCircuit {
  id: number;
  circuit_id: number;
  name: string;
  description: string | null;
  /** Identificación del interruptor termomagnético (ITM) de protección */
  itm: string | null;
  /** Sección del conductor en mm²; almacenado como string por variantes (p.ej. '2×6') */
  mm2: string | null;
  pi_kw: number;
  fd: number;
  md_kw: number;
  status: string;
  reserve_since: string | null;
  reserve_expires_at: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Solicitud de carga generada por un usuario Opersac para conectar una nueva carga a la red.
 * El admin la revisa y la aprueba o rechaza.
 */
export interface LoadRequest {
  id: number;
  opersac_user_id: number;
  opersac_name: string | null;
  station_id: number;
  station_name: string | null;
  bar_type: string;
  circuit_id: number | null;
  circuit_name: string | null;
  local_item: string | null;
  requested_load_kw: number;
  fd: number;
  sub_circuit_name: string | null;
  sub_circuit_description: string | null;
  sub_circuit_itm: string | null;
  sub_circuit_mm2: string | null;
  justification: string | null;
  /** Estado del flujo de aprobación: 'pending' → 'approved' | 'rejected' */
  status: 'pending' | 'approved' | 'rejected';
  /** Motivo de rechazo; presente solo cuando status === 'rejected' */
  rejection_reason: string | null;
  /** ID del admin que revisó la solicitud; null si aún no ha sido revisada */
  reviewed_by: number | null;
  /** Fecha/hora en que fue revisada; null si aún está pendiente */
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Notificación del sistema enviada a los administradores.
 * Puede estar vinculada a una estación, a un circuito o ser de alcance global.
 */
export interface Notification {
  id: number;
  /** Estación relacionada; null si la notificación es de alcance global */
  station_id: number | null;
  /** Circuito relacionado; null si no aplica */
  circuit_id: number | null;
  /**
   * Tipo de notificación:
   * - 'reserve_no_contact': circuito en reserva sin contacto del cliente
   * - 'negative_energy': estación con energía disponible negativa
   * - 'request_pending': solicitud de carga esperando revisión
   * - 'system': mensaje general del sistema
   */
  type: 'reserve_no_contact' | 'negative_energy' | 'request_pending' | 'system';
  message: string;
  is_read: boolean;
  /** true si el usuario la descartó manualmente */
  is_dismissed: boolean;
  /** Si fue extendida, indica hasta cuándo; null si no aplica */
  extended_until: string | null;
  /** Fecha en que el sistema la eliminará automáticamente; null si es permanente */
  auto_delete_at: string | null;
  created_at: string;
}

/**
 * Observación técnica registrada por un usuario sobre un circuito, sub-circuito o barra.
 * La severidad determina la prioridad visual y de atención.
 */
export interface Observation {
  id: number;
  /** Circuito al que pertenece la observación; null si aplica a barra o sub-circuito */
  circuit_id: number | null;
  /** Sub-circuito relacionado; null si no aplica */
  sub_circuit_id: number | null;
  /** Barra relacionada; null si no aplica */
  bar_id: number | null;
  user_id: number;
  user_name: string | null;
  user_role: string | null;
  /**
   * Severidad de la observación:
   * - 'urgent': requiere atención inmediata (rojo)
   * - 'warning': advertencia (amarillo)
   * - 'recommendation': sugerencia de mejora (azul)
   */
  severity: 'urgent' | 'warning' | 'recommendation';
  content: string;
  created_at: string;
}

/**
 * Entrada del registro de auditoría del sistema.
 * Cada acción relevante (crear, editar, aprobar, etc.) genera un registro.
 * Los registros pueden ser marcados ('flagged') por el admin para revisión posterior.
 */
export interface AuditLog {
  id: number;
  user_id: number;
  user_role: string;
  user_name: string;
  action_date: string;
  /** Acción realizada (p.ej. 'crear_circuito', 'aprobar_solicitud') */
  action: string;
  /** Tipo de entidad afectada (p.ej. 'circuit', 'station', 'user') */
  entity_type: string;
  /** ID de la entidad afectada; null si la acción es de alcance global */
  entity_id: number | null;
  /** Detalle adicional en formato JSON (valores anteriores/nuevos, contexto, etc.) */
  details: Record<string, unknown> | null;
  /** true si el admin marcó este registro como relevante para revisión */
  is_flagged: boolean;
  /** Motivo del marcado; presente solo cuando is_flagged === true */
  flag_reason: string | null;
}

/**
 * Registro de copia de seguridad de la base de datos.
 * Creado manualmente por el admin desde la sección de Backup.
 */
export interface Backup {
  id: number;
  created_by: number;
  creator_name: string | null;
  file_name: string;
  description: string | null;
  /** Indica si el backup incluye también la tabla de auditoría */
  includes_audit: boolean;
  /** Tamaño del archivo en bytes; null si aún no se calculó */
  size_bytes: number | null;
  created_at: string;
}

/**
 * Permiso granular asignado a un usuario Opersac para una funcionalidad específica.
 * Permite al admin controlar el acceso a secciones como 'view_reports', 'send_requests', etc.
 */
export interface Permission {
  id: number;
  user_id: number;
  /** Clave de la funcionalidad controlada (p.ej. 'view_stations', 'send_requests') */
  feature_key: string;
  is_allowed: boolean;
}

/**
 * Resumen de potencia agregada de una barra eléctrica.
 * Muestra los totales de potencia instalada, demanda máxima y capacidad del tablero.
 */
export interface BarPowerSummary {
  total_installed_power_kw: number;
  total_max_demand_kw: number;
  max_board_capacity_kw: number;
  max_board_capacity_a: number;
  /** Puede ser negativa si la demanda total supera la capacidad del tablero */
  available_power_kw: number;
}
