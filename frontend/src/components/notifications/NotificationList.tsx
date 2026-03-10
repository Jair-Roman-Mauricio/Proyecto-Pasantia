import { useState, useEffect } from 'react';
import { Bell, Clock, Zap } from 'lucide-react';
import api from '../../config/api';
import type { Notification } from '../../types';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import Input from '../ui/Input';

/**
 * Lista de notificaciones del sistema con soporte para filtrado por tipo.
 * Tipos soportados:
 *  - reserve_no_contact: reservas sin contacto, permiten extender fecha o resolver/eliminar la reserva.
 *  - negative_energy:    alertas de energía negativa en una estación.
 *  - (otros):            notificaciones genéricas del sistema.
 */
export default function NotificationList() {
  // Lista de notificaciones cargadas según el filtro activo
  const [notifications, setNotifications] = useState<Notification[]>([]);
  // Filtro activo: 'all' | 'unread' | 'reserve_no_contact' | 'negative_energy'
  const [filter, setFilter] = useState('all');

  // Estado del modal de extensión de fecha de reserva
  // extendTarget almacena el ID de la notificación que se está extendiendo
  const [extendTarget, setExtendTarget] = useState<number | null>(null);
  // Nueva fecha límite seleccionada por el usuario para la extensión
  const [extendDate, setExtendDate] = useState('');
  // Indica que la operación de extensión está en curso
  const [extendLoading, setExtendLoading] = useState(false);

  // ID de la notificación cuya reserva se está resolviendo/eliminando; null si ninguna está en proceso
  const [resolving, setResolving] = useState<number | null>(null);

  // Recarga notificaciones cada vez que cambia el filtro activo
  useEffect(() => { loadNotifications(); }, [filter]);

  /**
   * Carga notificaciones aplicando los parámetros del filtro activo:
   *  - 'unread' → filtra por is_read=false
   *  - tipo específico → filtra por type=<tipo>
   *  - 'all' → no aplica filtros, retorna todas
   */
  const loadNotifications = async () => {
    const params: Record<string, string> = {};
    if (filter === 'unread') params.is_read = 'false';
    if (filter !== 'all' && filter !== 'unread') params.type = filter;
    const { data } = await api.get('/notifications', { params });
    setNotifications(data);
  };

  // Marca una notificación como leída y recarga la lista para actualizar el indicador visual
  const handleMarkRead = async (id: number) => {
    await api.put(`/notifications/${id}/read`);
    loadNotifications();
  };

  // Descarta (archiva) una notificación para que no aparezca en la lista activa
  const handleDismiss = async (id: number) => {
    await api.put(`/notifications/${id}/dismiss`);
    loadNotifications();
  };

  /**
   * Extiende la fecha límite de una reserva asociada a una notificación de tipo reserve_no_contact.
   * Acción disponible cuando la reserva aún está vigente pero se necesita más tiempo.
   * Flujo: valida que haya fecha → envía PUT con extended_until → cierra modal → recarga lista.
   */
  const handleExtendConfirm = async () => {
    if (!extendTarget || !extendDate) return;
    setExtendLoading(true);
    try {
      await api.put(`/notifications/${extendTarget}/extend`, { extended_until: extendDate });
      setExtendTarget(null);
      setExtendDate('');
      loadNotifications();
    } finally {
      setExtendLoading(false);
    }
  };

  /**
   * Resuelve y elimina la reserva vinculada a una notificación de tipo reserve_no_contact.
   * Acción más drástica que la extensión: libera el circuito reservado cambiando su estado.
   * El ID de la notificación en proceso se guarda en `resolving` para deshabilitar el botón
   * y mostrar feedback visual durante la operación.
   */
  const handleResolveReserve = async (id: number) => {
    setResolving(id);
    try {
      await api.put(`/notifications/${id}/resolve-reserve`);
      loadNotifications();
    } finally {
      setResolving(null);
    }
  };

  /**
   * Devuelve el icono correspondiente al tipo de notificación:
   *  - reserve_no_contact → reloj amarillo (urgencia temporal)
   *  - negative_energy    → rayo rojo (alerta de energía)
   *  - (default)          → campana azul (notificación genérica)
   */
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

      {/* Barra de filtros: permite mostrar todas, no leídas o filtradas por tipo */}
      <div className="flex gap-2 mb-4">
        {[
          { id: 'all', label: 'Todas' },
          { id: 'unread', label: 'No leidas' },
          // Filtro específico para notificaciones de reservas sin contacto
          { id: 'reserve_no_contact', label: 'Reservas' },
          // Filtro específico para alertas de energía negativa
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
          // Las notificaciones no leídas tienen un borde izquierdo destacado
          <Card key={n.id} className={!n.is_read ? 'border-l-4 border-l-primary-500' : ''}>
            <div className="flex items-start gap-3">
              {/* Icono diferenciado según el tipo de notificación */}
              {getIcon(n.type)}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-[var(--text-primary)]">{n.message}</p>
                <p className="text-xs text-[var(--text-muted)] mt-1">{new Date(n.created_at).toLocaleString()}</p>
                <div className="flex gap-1 flex-wrap mt-2">
                  {!n.is_read && <Button variant="ghost" size="sm" onClick={() => handleMarkRead(n.id)}>Leido</Button>}
                  {/* Acciones exclusivas para notificaciones de reserva sin contacto */}
                  {n.type === 'reserve_no_contact' && (
                    <>
                      {/* Extender: abre el modal para seleccionar nueva fecha límite de la reserva */}
                      <Button variant="ghost" size="sm" onClick={() => { setExtendTarget(n.id); setExtendDate(''); }}>
                        Extender
                      </Button>
                      {/* Eliminar reserva: resuelve el circuito reservado de forma definitiva */}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleResolveReserve(n.id)}
                        disabled={resolving === n.id}
                      >
                        {resolving === n.id ? '...' : 'Eliminar reserva'}
                      </Button>
                    </>
                  )}
                  <Button variant="ghost" size="sm" onClick={() => handleDismiss(n.id)}>Descartar</Button>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Modal para extender la fecha de una reserva sin contacto */}
      <Modal
        isOpen={extendTarget !== null}
        onClose={() => { setExtendTarget(null); setExtendDate(''); }}
        title="Extender reserva"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-sm text-[var(--text-secondary)]">
            Selecciona hasta qué fecha se extiende el plazo de esta reserva.
          </p>
          <Input
            label="Extender hasta"
            type="date"
            value={extendDate}
            onChange={(e) => setExtendDate(e.target.value)}
          />
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => { setExtendTarget(null); setExtendDate(''); }}>
              Cancelar
            </Button>
            {/* El botón se habilita solo cuando el usuario ha seleccionado una fecha */}
            <Button onClick={handleExtendConfirm} disabled={!extendDate || extendLoading}>
              {extendLoading ? 'Guardando...' : 'Confirmar'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
