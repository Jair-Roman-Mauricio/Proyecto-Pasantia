/** Usuario completo devuelto por GET /users y GET /users/:id */
export interface User {
  id: string;  // UUID de Supabase Auth
  username: string;
  full_name: string;
  /** 'admin' tiene acceso total; 'opersac' acceso limitado por permisos */
  role: 'admin' | 'opersac';
  /** 'reported' bloquea el login sin eliminar el usuario */
  status: 'active' | 'inactive' | 'reported';
  created_at: string;
  updated_at: string;
}

/** Perfil resumido almacenado en AuthContext tras login */
export interface UserBrief {
  id: string;  // UUID de Supabase Auth
  username: string;
  full_name: string;
  role: string;
  /** Mapa feature_key → is_allowed; solo presente para rol 'opersac' */
  permissions?: Record<string, boolean>;
}

/**
 * @deprecated LoginResponse ya no se usa — el login se realiza con supabase-js.
 * Conservado para compatibilidad durante la transición.
 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserBrief;
}

/**
 * Estación eléctrica (E01–E26).
 * El status refleja la carga del transformador:
 *   green  → disponible > 20% de transformer_capacity_kw
 *   yellow → disponible ≤ 20%
 *   red    → demanda > capacidad (sobrecarga)
 */
export interface Station {
  id: number;
  code: string;       // Ej: "E01", "E26"
  name: string;       // Ej: "Villa El Salvador", "Bayóvar"
  order_index: number;
  transformer_capacity_kw: number;
  max_demand_kw: number;      // Suma de md_kw de circuitos activos
  available_power_kw: number; // transformer_capacity_kw - max_demand_kw
  status: 'red' | 'yellow' | 'green';
  created_at: string;
  updated_at: string;
}

export interface PowerSummary {
  station_id: number;
  station_name: string;
  transformer_capacity_kw: number;
  max_demand_kw: number;
  available_power_kw: number;
  status: string;
}

export interface Bar {
  id: number;
  station_id: number;
  name: string;
  bar_type: 'normal' | 'emergency' | 'continuity';
  status: 'operative' | 'inactive';
  capacity_kw: number;
  capacity_a: number;
  created_at: string;
  updated_at: string;
}

/**
 * Circuito eléctrico dentro de una barra.
 * md_kw = pi_kw × fd (demanda máxima)
 *
 * Estados:
 *   operative_normal     → en operación (cuenta en la demanda)
 *   reserve_r            → reserva sin equipar (cuenta en la demanda)
 *   reserve_equipped_re  → reserva equipada (cuenta en la demanda)
 *   inactive             → fuera de servicio (NO cuenta en la demanda)
 */
export interface Circuit {
  id: number;
  bar_id: number;
  secondary_bar_id: number | null;
  tertiary_bar_id: number | null;
  denomination: string;   // Código corto, ej: "ESC-01"
  name: string;
  description: string | null;
  local_item: string | null;
  pi_kw: number;    // Potencia instalada
  fd: number;       // Factor de demanda (0–1)
  md_kw: number;    // Demanda máxima = pi_kw × fd
  status: 'operative_normal' | 'reserve_r' | 'reserve_equipped_re' | 'inactive';
  is_ups: boolean;
  reserve_since: string | null;
  reserve_expires_at: string | null;
  client_last_contact: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubCircuit {
  id: number;
  circuit_id: number;
  name: string;
  description: string | null;
  itm: string | null;
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
 * Solicitud de ampliación de carga enviada por un usuario opersac.
 * Si circuit_id es null → se crea un nuevo circuito al aprobar.
 * Si circuit_id tiene valor → se crea un sub-circuito en ese circuito.
 */
export interface LoadRequest {
  id: number;
  opersac_user_id: string;  // UUID
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
  status: 'pending' | 'approved' | 'rejected';
  rejection_reason: string | null;
  reviewed_by: string | null;  // UUID
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: number;
  station_id: number | null;
  circuit_id: number | null;
  type: 'reserve_no_contact' | 'negative_energy' | 'request_pending' | 'system';
  message: string;
  is_read: boolean;
  is_dismissed: boolean;
  extended_until: string | null;
  auto_delete_at: string | null;
  created_at: string;
}

export interface Observation {
  id: number;
  circuit_id: number | null;
  sub_circuit_id: number | null;
  bar_id: number | null;
  user_id: string;  // UUID
  user_name: string | null;
  user_role: string | null;
  severity: 'urgent' | 'warning' | 'recommendation';
  content: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  user_id: string;  // UUID
  user_role: string;
  user_name: string;
  action_date: string;
  action: string;
  entity_type: string;
  entity_id: string | null;  // String para soportar int IDs y UUIDs
  details: Record<string, unknown> | null;
  is_flagged: boolean;
  flag_reason: string | null;
}

export interface Backup {
  id: number;
  created_by: string;  // UUID
  creator_name: string | null;
  file_name: string;
  description: string | null;
  includes_audit: boolean;
  size_bytes: number | null;
  created_at: string;
}

export interface Permission {
  id: number;
  user_id: string;  // UUID
  feature_key: string;
  is_allowed: boolean;
}

export interface BarPowerSummary {
  total_installed_power_kw: number;
  total_max_demand_kw: number;
  max_board_capacity_kw: number;
  max_board_capacity_a: number;
  available_power_kw: number;
}
