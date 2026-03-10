import { useState, useEffect, useRef } from 'react';
import api from '../config/api';
import type { ToastItem } from '../components/ui/LoginToast';

interface NotificationRaw {
  id: number;
  type: string;
  message: string;
  is_read: boolean;
}

interface RequestRaw {
  id: number;
  status: string;
  local_item: string | null;
  station_name: string | null;
  updated_at: string;
}

export function useLoginNotifications(role: 'admin' | 'opersac' | undefined, userId?: number) {
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

        // Pending requests → navigates to Solicitudes
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

        // Unread system notifications → navigates to Notificaciones
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
      // Key per user so different opersac users don't share timestamps
      const cutoffKey = `notif_cutoff_${userIdRef.current ?? 'opersac'}`;
      const stored = localStorage.getItem(cutoffKey);
      const cutoff = stored ? new Date(stored) : new Date(Date.now() - 24 * 60 * 60 * 1000);

      // Save current timestamp so next login only shows newer items
      localStorage.setItem(cutoffKey, new Date().toISOString());

      api
        .get<RequestRaw[]>('/requests/my')
        .then(({ data }) => {
          const items: ToastItem[] = [];

          // Approved/rejected after last check
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

          // Own pending count
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
