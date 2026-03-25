-- ============================================================
-- Fix: dar permisos en secuencias de schema Subest
-- Ejecutar en Supabase Studio → SQL Editor
-- ============================================================

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA "Subest" TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA "Subest" TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA "Subest" TO anon, authenticated, service_role;
