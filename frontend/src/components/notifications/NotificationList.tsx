import { useState, useEffect } from 'react';
import { Bell, Clock, Zap } from 'lucide-react';
import api from '../../config/api';
import type { Notification } from '../../types';
import Card from '../ui/Card';
import Button from '../ui/Button';

export default function NotificationList() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filter, setFilter] = useState('all');

  useEffect(() => { loadNotifications(); }, [filter]);

  const loadNotifications = async () => {
    const params: Record<string, string> = {};
    if (filter === 'unread') params.is_read = 'false';
    if (filter !== 'all' && filter !== 'unread') params.type = filter;
    const { data } = await api.get('/notifications', { params });
    setNotifications(data);
  };

  const handleMarkRead = async (id: number) => {
    await api.put(`/notifications/${id}/read`);
    loadNotifications();
  };

  const handleDismiss = async (id: number) => {
    await api.put(`/notifications/${id}/dismiss`);
    loadNotifications();
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'reserve_no_contact': return <Clock size={18} className="text-yellow-500" />;
      case 'negative_energy': return <Zap size={18} className="text-red-500" />;
      default: return <Bell size={18} className="text-blue-500" />;
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4">Notificaciones</h2>
      <div className="flex gap-2 mb-4">
        {[
          { id: 'all', label: 'Todas' },
          { id: 'unread', label: 'No leidas' },
          { id: 'reserve_no_contact', label: 'Reservas' },
          { id: 'negative_energy', label: 'Energia' },
        ].map((f) => (
          <Button key={f.id} variant={filter === f.id ? 'primary' : 'secondary'} size="sm" onClick={() => setFilter(f.id)}>
            {f.label}
          </Button>
        ))}
      </div>
      <div className="space-y-3">
        {notifications.length === 0 && (
          <Card><p className="text-center text-[var(--text-muted)] py-8">No hay notificaciones</p></Card>
        )}
        {notifications.map((n) => (
          <Card key={n.id} className={!n.is_read ? 'border-l-4 border-l-primary-500' : ''}>
            <div className="flex items-start gap-3">
              {getIcon(n.type)}
              <div className="flex-1">
                <p className="text-sm text-[var(--text-primary)]">{n.message}</p>
                <p className="text-xs text-[var(--text-muted)] mt-1">{new Date(n.created_at).toLocaleString()}</p>
              </div>
              <div className="flex gap-1">
                {!n.is_read && <Button variant="ghost" size="sm" onClick={() => handleMarkRead(n.id)}>Leido</Button>}
                <Button variant="ghost" size="sm" onClick={() => handleDismiss(n.id)}>Descartar</Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
