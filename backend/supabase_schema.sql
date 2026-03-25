-- ============================================================
-- Ejecutar en Supabase Studio → SQL Editor
-- Crea todas las tablas en el schema Subest
-- ============================================================

CREATE TABLE IF NOT EXISTS "Subest".stations (
    id bigserial PRIMARY KEY,
    code varchar(10) UNIQUE NOT NULL,
    name varchar(100) NOT NULL,
    order_index int NOT NULL,
    transformer_capacity_kw numeric(10,2) DEFAULT 500,
    max_demand_kw numeric(10,2) DEFAULT 0,
    available_power_kw numeric(10,2) DEFAULT 500,
    status varchar(10) DEFAULT 'green',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "Subest".bars (
    id bigserial PRIMARY KEY,
    station_id bigint REFERENCES "Subest".stations(id) ON DELETE CASCADE,
    name varchar(100) NOT NULL,
    bar_type varchar(20) NOT NULL,
    status varchar(20) DEFAULT 'operative',
    capacity_kw numeric(10,2) DEFAULT 200,
    capacity_a numeric(10,2) DEFAULT 300,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "Subest".circuits (
    id bigserial PRIMARY KEY,
    bar_id bigint REFERENCES "Subest".bars(id) ON DELETE CASCADE,
    secondary_bar_id bigint REFERENCES "Subest".bars(id),
    tertiary_bar_id bigint REFERENCES "Subest".bars(id),
    denomination varchar(50),
    name varchar(100) NOT NULL,
    description text,
    local_item varchar(100),
    pi_kw numeric(10,2) DEFAULT 0,
    fd numeric(5,3) DEFAULT 1,
    md_kw numeric(10,2) DEFAULT 0,
    status varchar(30) DEFAULT 'operative_normal',
    is_ups boolean DEFAULT false,
    reserve_since date,
    reserve_expires_at date,
    client_last_contact date,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "Subest".sub_circuits (
    id bigserial PRIMARY KEY,
    circuit_id bigint REFERENCES "Subest".circuits(id) ON DELETE CASCADE,
    name varchar(100) NOT NULL,
    description text,
    itm varchar(50),
    mm2 varchar(50),
    pi_kw numeric(10,2) DEFAULT 0,
    fd numeric(5,3) DEFAULT 1,
    md_kw numeric(10,2) DEFAULT 0,
    status varchar(30) DEFAULT 'operative_normal',
    reserve_since date,
    reserve_expires_at date,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "Subest".permissions (
    id bigserial PRIMARY KEY,
    user_id uuid REFERENCES "Subest".users(id) ON DELETE CASCADE,
    feature_key varchar(50) NOT NULL,
    is_allowed boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE(user_id, feature_key)
);

CREATE TABLE IF NOT EXISTS "Subest".observations (
    id bigserial PRIMARY KEY,
    circuit_id bigint REFERENCES "Subest".circuits(id) ON DELETE SET NULL,
    sub_circuit_id bigint REFERENCES "Subest".sub_circuits(id) ON DELETE SET NULL,
    bar_id bigint REFERENCES "Subest".bars(id) ON DELETE SET NULL,
    user_id uuid REFERENCES "Subest".users(id),
    severity varchar(20) DEFAULT 'recommendation',
    content text NOT NULL,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "Subest".notifications (
    id bigserial PRIMARY KEY,
    station_id bigint REFERENCES "Subest".stations(id) ON DELETE SET NULL,
    circuit_id bigint REFERENCES "Subest".circuits(id) ON DELETE SET NULL,
    type varchar(30) NOT NULL,
    message text NOT NULL,
    is_read boolean DEFAULT false,
    is_dismissed boolean DEFAULT false,
    extended_until date,
    auto_delete_at date,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "Subest".requests (
    id bigserial PRIMARY KEY,
    opersac_user_id uuid REFERENCES "Subest".users(id),
    station_id bigint REFERENCES "Subest".stations(id),
    bar_type varchar(20),
    circuit_id bigint REFERENCES "Subest".circuits(id),
    local_item varchar(100),
    requested_load_kw numeric(10,2),
    fd numeric(5,3) DEFAULT 1,
    sub_circuit_name varchar(100),
    sub_circuit_description text,
    sub_circuit_itm varchar(50),
    sub_circuit_mm2 varchar(50),
    justification text,
    status varchar(20) DEFAULT 'pending',
    rejection_reason text,
    reviewed_by uuid REFERENCES "Subest".users(id),
    reviewed_at timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "Subest".audit_logs (
    id bigserial PRIMARY KEY,
    user_id uuid REFERENCES "Subest".users(id),
    user_role varchar(20),
    user_name varchar(100),
    action_date timestamptz DEFAULT now(),
    action varchar(100),
    entity_type varchar(50),
    entity_id varchar(100),
    details jsonb,
    is_flagged boolean DEFAULT false,
    flag_reason text
);

CREATE TABLE IF NOT EXISTS "Subest".backups (
    id bigserial PRIMARY KEY,
    created_by uuid REFERENCES "Subest".users(id),
    file_name varchar(200),
    description text,
    backup_data jsonb,
    includes_audit boolean DEFAULT false,
    size_bytes bigint DEFAULT 0,
    created_at timestamptz DEFAULT now()
);

-- Grant access to anon and authenticated roles
GRANT USAGE ON SCHEMA "Subest" TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA "Subest" TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA "Subest" TO anon, authenticated, service_role;
