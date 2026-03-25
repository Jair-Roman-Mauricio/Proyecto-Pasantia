-- ============================================================
-- SOLUCIÓN: Crear vistas en schema PUBLIC que apuntan a Subest
-- PostgREST solo expone 'public' → las vistas hacen de puente
-- Ejecutar en Supabase Studio → SQL Editor
-- ============================================================

CREATE OR REPLACE VIEW public.stations       AS SELECT * FROM "Subest".stations;
CREATE OR REPLACE VIEW public.bars           AS SELECT * FROM "Subest".bars;
CREATE OR REPLACE VIEW public.circuits       AS SELECT * FROM "Subest".circuits;
CREATE OR REPLACE VIEW public.sub_circuits   AS SELECT * FROM "Subest".sub_circuits;
CREATE OR REPLACE VIEW public.users          AS SELECT * FROM "Subest".users;
CREATE OR REPLACE VIEW public.permissions    AS SELECT * FROM "Subest".permissions;
CREATE OR REPLACE VIEW public.observations   AS SELECT * FROM "Subest".observations;
CREATE OR REPLACE VIEW public.notifications  AS SELECT * FROM "Subest".notifications;
CREATE OR REPLACE VIEW public.requests       AS SELECT * FROM "Subest".requests;
CREATE OR REPLACE VIEW public.audit_logs     AS SELECT * FROM "Subest".audit_logs;
CREATE OR REPLACE VIEW public.backups        AS SELECT * FROM "Subest".backups;

-- Grants para que PostgREST pueda leer y escribir a través de las vistas
GRANT SELECT, INSERT, UPDATE, DELETE ON public.stations      TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.bars          TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.circuits      TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.sub_circuits  TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.users         TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.permissions   TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.observations  TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.notifications TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.requests      TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.audit_logs    TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.backups       TO anon, authenticated, service_role;

-- Eliminar función anterior y recrear con el tipo correcto
DROP FUNCTION IF EXISTS public.get_user_by_id(uuid);

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
    FROM "Subest".users
    WHERE id = p_id;
$$;

-- Verificación: debe listar las 11 vistas creadas
SELECT table_name FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name IN ('stations','bars','circuits','sub_circuits','users',
                     'permissions','observations','notifications','requests',
                     'audit_logs','backups')
ORDER BY table_name;
