/**
 * @file useLoginNotifications.ts
 * Hook personalizado que genera notificaciones toast al iniciar sesión, adaptadas
 * al rol del usuario autenticado. Consulta el backend una sola vez por montaje y
 * gestiona un timestamp de corte en `localStorage` para los operadores SAC,
 * de modo que solo se muestran los cambios ocurridos desde la última sesión.
 */

import { useState, useEffect, useRef } from 'react';
import api from '../config/api';
import type { ToastItem } from '../components/ui/LoginToast';

/** Estructura cruda de una notificación del sistema devuelta por el backend. */
interface NotificationRaw {
  id: number;
  type: string;
  message: string;
  is_read: boolean;
}

/** Estructura cruda de una solicitud devuelta por el backend. */
interface RequestRaw {
  id: number;
  status: string;
  local_item: string | null;
  station_name: string | null;
  updated_at: string;
}

/**
 * Hook que consulta el backend al iniciar sesión y genera toasts de bienvenida
 * con información relevante según el rol del usuario.
 *
 * - Para **administradores**: muestra solicitudes pendientes de aprobación y
 *   notificaciones del sistema no leídas (máximo 3 toasts en total).
 * - Para **operadores SAC**: muestra actualizaciones de estado de sus propias solicitudes
 *   (aprobadas/rechazadas desde el último login) y un resumen de las que siguen pendientes.
 *
 * La consulta se ejecuta una sola vez por montaje gracias a la ref `fetched`.
 *
 * @param role   - Rol del usuario autenticado (`'admin'` u `'opersac'`). Si es `undefined`,
 *                 el efecto no se ejecuta y no se generan notificaciones.
 * @param userId - Identificador numérico del usuario. Se usa como sufijo de la clave en
 *                 localStorage para que distintos operadores no compartan el mismo timestamp de corte.
 * @returns Un objeto con:
 *   - `toasts`  – arreglo de items de notificación listos para renderizar.
 *   - `dismiss` – función para eliminar un toast por su `id`.
 */
export function useLoginNotifications(role: 'admin' | 'opersac' | undefined, userId?: string) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const fetched = useRef(false);
  const userIdRef = useRef(userId);
  userIdRef.current = userId;

  useEffect(() => {
    if (!role || fetched.current) return;
    fetched.current = true;

    if (role === 'admin') {
      Promise.all([
        api.get<NotificationRaw[]>('/notifications', { params: { is_read: false } }).catch(() => ({ data: [] as NotificationRaw[] })),
        api.get<RequestRaw[]>('/requests').catch(() => ({ data: [] as RequestRaw[] })),
      ]).then(([notifRes, reqRes]) => {
        const items: ToastItem[] = [];

        // Solicitudes pendientes → navega a la sección Solicitudes
        const pendingCount = reqRes.data.filter((r) => r.status === 'pending').length;
        if (pendingCount > 0) {
          items.push({
            id: 'pending-requests',
            message: `Tienes ${pendingCount} solicitud${pendingCount > 1 ? 'es' : ''} pendiente${pendingCount > 1 ? 's' : ''} de aprobar`,
            type: 'warning',
            role: 'admin',
            navigateTo: 'requests',
          });
        }

        // Notificaciones del sistema no leídas → navega a Notificaciones
        const unread = notifRes.data.slice(0, 3 - items.length);
        for (const n of unread) {
          items.push({
            id: `notif-${n.id}`,
            message: n.message,
            type: n.type === 'negative_energy' ? 'error' : 'warning',
            role: 'admin',
            navigateTo: 'notifications',
          });
        }

        setToasts(items);
      });
    } else {
      // Clave por usuario para que distintos operadores no compartan timestamps
      const cutoffKey = `notif_cutoff_${userIdRef.current ?? 'opersac'}`;
      const stored = localStorage.getItem(cutoffKey);
      const cutoff = stored ? new Date(stored) : new Date(Date.now() - 24 * 60 * 60 * 1000);

      // Guarda el timestamp actual; el próximo login solo mostrará items más recientes
      localStorage.setItem(cutoffKey, new Date().toISOString());

      api
        .get<RequestRaw[]>('/requests/my')
        .then(({ data }) => {
          const items: ToastItem[] = [];

          // Solicitudes aprobadas/rechazadas desde la última revisión
          const recentUpdated = data.filter((r) => {
            if (r.status !== 'approved' && r.status !== 'rejected') return false;
            return new Date(r.updated_at) > cutoff;
          });

          for (const r of recentUpdated.slice(0, 2)) {
            items.push({
              id: `req-${r.id}`,
              message:
                r.status === 'approved'
                  ? `Tu solicitud "${r.local_item ?? r.station_name ?? `#${r.id}`}" fue aprobada`
                  : `Tu solicitud "${r.local_item ?? r.station_name ?? `#${r.id}`}" fue rechazada`,
              type: r.status === 'approved' ? 'info' : 'warning',
              role: 'opersac',
              navigateTo: 'requests',
            });
          }

          // Cantidad de solicitudes propias pendientes de revisión
          const myPending = data.filter((r) => r.status === 'pending').length;
          if (myPending > 0 && items.length < 3) {
            items.push({
              id: 'my-pending',
              message: `Tienes ${myPending} solicitud${myPending > 1 ? 'es' : ''} pendiente${myPending > 1 ? 's' : ''} de revision`,
              type: 'info',
              role: 'opersac',
              navigateTo: 'requests',
            });
          }

          setToasts(items);
        })
        .catch(() => {});
    }
  }, [role]);

  const dismiss = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));

  return { toasts, dismiss };
}
