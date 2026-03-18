/**
 * @file supabaseClient.ts
 * Instancia singleton del cliente de Supabase utilizada en toda la aplicación.
 * Las credenciales se leen desde variables de entorno de Vite para evitar
 * exponer valores sensibles en el código fuente.
 *
 * Variables de entorno requeridas en `.env`:
 *   - `VITE_SUPABASE_URL`      — URL del proyecto Supabase.
 *   - `VITE_SUPABASE_ANON_KEY` — Clave pública anónima del proyecto.
 */

import { createClient } from '@supabase/supabase-js';

// Credenciales inyectadas en tiempo de build por Vite desde el archivo .env
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

/** Cliente de Supabase configurado y listo para usar en servicios y contextos. */
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
