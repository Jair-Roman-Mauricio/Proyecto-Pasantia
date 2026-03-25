-- ============================================================
-- Crear todas las tablas en schema PUBLIC
-- (PostgREST en fp.lineauno.pe solo expone public)
-- Ejecutar en Supabase Studio → SQL Editor
-- ============================================================

-- stations
CREATE TABLE IF NOT EXISTS public.stations (
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

-- bars
CREATE TABLE IF NOT EXISTS public.bars (
    id bigserial PRIMARY KEY,
    station_id bigint REFERENCES public.stations(id) ON DELETE CASCADE,
    name varchar(100) NOT NULL,
    bar_type varchar(20) NOT NULL,
    status varchar(20) DEFAULT 'operative',
    capacity_kw numeric(10,2) DEFAULT 200,
    capacity_a numeric(10,2) DEFAULT 300,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- circuits
CREATE TABLE IF NOT EXISTS public.circuits (
    id bigserial PRIMARY KEY,
    bar_id bigint REFERENCES public.bars(id) ON DELETE CASCADE,
    secondary_bar_id bigint REFERENCES public.bars(id),
    tertiary_bar_id bigint REFERENCES public.bars(id),
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

-- sub_circuits
CREATE TABLE IF NOT EXISTS public.sub_circuits (
    id bigserial PRIMARY KEY,
    circuit_id bigint REFERENCES public.circuits(id) ON DELETE CASCADE,
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

-- users (perfil de app, el UUID viene de Supabase Auth)
CREATE TABLE IF NOT EXISTS public.metro_users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username varchar(50) UNIQUE NOT NULL,
    full_name varchar(150),
    role varchar(20) NOT NULL DEFAULT 'opersac',
    status varchar(20) NOT NULL DEFAULT 'active',
    email varchar(150),
    phone varchar(30),
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- permissions
CREATE TABLE IF NOT EXISTS public.permissions (
    id bigserial PRIMARY KEY,
    user_id uuid REFERENCES public.metro_users(id) ON DELETE CASCADE,
    feature_key varchar(50) NOT NULL,
    is_allowed boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE(user_id, feature_key)
);

-- observations
CREATE TABLE IF NOT EXISTS public.observations (
    id bigserial PRIMARY KEY,
    circuit_id bigint REFERENCES public.circuits(id) ON DELETE SET NULL,
    sub_circuit_id bigint REFERENCES public.sub_circuits(id) ON DELETE SET NULL,
    bar_id bigint REFERENCES public.bars(id) ON DELETE SET NULL,
    user_id uuid,
    severity varchar(20) DEFAULT 'recommendation',
    content text NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- notifications
CREATE TABLE IF NOT EXISTS public.notifications (
    id bigserial PRIMARY KEY,
    station_id bigint REFERENCES public.stations(id) ON DELETE SET NULL,
    circuit_id bigint REFERENCES public.circuits(id) ON DELETE SET NULL,
    type varchar(30) NOT NULL,
    message text NOT NULL,
    is_read boolean DEFAULT false,
    is_dismissed boolean DEFAULT false,
    extended_until date,
    auto_delete_at date,
    created_at timestamptz DEFAULT now()
);

-- requests
CREATE TABLE IF NOT EXISTS public.requests (
    id bigserial PRIMARY KEY,
    opersac_user_id uuid,
    station_id bigint REFERENCES public.stations(id),
    bar_type varchar(20),
    circuit_id bigint REFERENCES public.circuits(id),
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
    reviewed_by uuid,
    reviewed_at timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- audit_logs
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id bigserial PRIMARY KEY,
    user_id uuid,
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

-- backups
CREATE TABLE IF NOT EXISTS public.backups (
    id bigserial PRIMARY KEY,
    created_by uuid,
    file_name varchar(200),
    description text,
    backup_data jsonb,
    includes_audit boolean DEFAULT false,
    size_bytes bigint DEFAULT 0,
    created_at timestamptz DEFAULT now()
);

-- RLS: deshabilitar para que el service_role pueda operar sin restricciones
ALTER TABLE public.stations DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.bars DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.circuits DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sub_circuits DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.metro_users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.permissions DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.observations DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.requests DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.backups DISABLE ROW LEVEL SECURITY;

-- Grants
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;

-- Función RPC para obtener usuario por ID (usada en auth)
CREATE OR REPLACE FUNCTION public.get_user_by_id(p_id uuid)
RETURNS TABLE (
    id uuid,
    username varchar,
    full_name varchar,
    role varchar,
    status varchar
)
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT id, username, full_name, role, status
    FROM public.metro_users
    WHERE id = p_id;
$$;
