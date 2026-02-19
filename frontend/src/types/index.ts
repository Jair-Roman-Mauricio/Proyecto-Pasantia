export interface User {
  id: number;
  username: string;
  full_name: string;
  role: 'admin' | 'opersac';
  status: 'active' | 'inactive' | 'reported';
  created_at: string;
  updated_at: string;
}

export interface UserBrief {
  id: number;
  username: string;
  full_name: string;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserBrief;
}

export interface Station {
  id: number;
  code: string;
  name: string;
  order_index: number;
  transformer_capacity_kw: number;
  max_demand_kw: number;
  available_power_kw: number;
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

export interface Circuit {
  id: number;
  bar_id: number;
  secondary_bar_id: number | null;
  denomination: string;
  name: string;
  description: string | null;
  local_item: string | null;
  pi_kw: number;
  fd: number;
  md_kw: number;
  status: 'operative_normal' | 'reserve_r' | 'reserve_equipped_re' | 'inactive';
  is_ups: boolean;
  reserve_since: string | null;
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
  created_at: string;
  updated_at: string;
}

export interface LoadRequest {
  id: number;
  opersac_user_id: number;
  opersac_name: string | null;
  station_id: number;
  station_name: string | null;
  bar_type: string;
  requested_load_kw: number;
  justification: string | null;
  status: 'pending' | 'approved' | 'rejected';
  rejection_reason: string | null;
  reviewed_by: number | null;
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
  user_id: number;
  user_name: string | null;
  user_role: string | null;
  severity: 'urgent' | 'warning' | 'recommendation';
  content: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  user_id: number;
  user_role: string;
  user_name: string;
  action_date: string;
  action: string;
  entity_type: string;
  entity_id: number | null;
  details: Record<string, unknown> | null;
  is_flagged: boolean;
  flag_reason: string | null;
}

export interface Backup {
  id: number;
  created_by: number;
  creator_name: string | null;
  file_name: string;
  description: string | null;
  includes_audit: boolean;
  size_bytes: number | null;
  created_at: string;
}

export interface Permission {
  id: number;
  user_id: number;
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
