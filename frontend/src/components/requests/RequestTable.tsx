import { useState, useEffect } from 'react';
import api from '../../config/api';
import type { LoadRequest } from '../../types';
import { useAuth } from '../../context/AuthContext';
import Table from '../ui/Table';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Modal from '../ui/Modal';

export default function RequestTable() {
  const { user } = useAuth();
  const [requests, setRequests] = useState<LoadRequest[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<LoadRequest | null>(null);
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const isAdmin = user?.role === 'admin';

  useEffect(() => { loadRequests(); }, []);

  const loadRequests = async () => {
    const endpoint = isAdmin ? '/requests' : '/requests/my';
    const { data } = await api.get(endpoint);
    setRequests(data);
  };

  const handleApprove = async (id: number) => {
    await api.put(`/requests/${id}/approve`);
    setSelectedRequest(null);
    loadRequests();
  };

  const handleReject = async (id: number) => {
    if (!rejectionReason) return;
    await api.put(`/requests/${id}/reject`, { rejection_reason: rejectionReason });
    setShowRejectForm(false);
    setSelectedRequest(null);
    setRejectionReason('');
    loadRequests();
  };

  const statusColor = (s: string) => s === 'pending' ? 'yellow' : s === 'approved' ? 'green' : 'red';
  const statusLabel = (s: string) => s === 'pending' ? 'Pendiente' : s === 'approved' ? 'Aprobado' : 'Rechazado';

  const columns = [
    { key: 'id', header: 'ID' },
    { key: 'opersac_name', header: 'Opersac' },
    { key: 'station_name', header: 'Estacion' },
    { key: 'bar_type', header: 'Barra', render: (r: LoadRequest) => r.bar_type.charAt(0).toUpperCase() + r.bar_type.slice(1) },
    { key: 'created_at', header: 'Fecha', render: (r: LoadRequest) => new Date(r.created_at).toLocaleDateString() },
    { key: 'requested_load_kw', header: 'Carga (kW)', render: (r: LoadRequest) => `${r.requested_load_kw} kW` },
    { key: 'status', header: 'Estado', render: (r: LoadRequest) => <Badge color={statusColor(r.status)}>{statusLabel(r.status)}</Badge> },
    { key: 'actions', header: 'Accion', render: (r: LoadRequest) => <Button variant="ghost" size="sm" onClick={() => setSelectedRequest(r)}>Ver Detalle</Button> },
  ];

  return (
    <div>
      <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4">
        {isAdmin ? 'Solicitudes de Ampliacion' : 'Mis Solicitudes'}
      </h2>
      <Table columns={columns} data={requests} rowKey={(r) => r.id} />

      {selectedRequest && (
        <Modal isOpen onClose={() => setSelectedRequest(null)} title={`Solicitud #${selectedRequest.id}`} size="md">
          <div className="space-y-3">
            <p className="text-sm"><strong>Opersac:</strong> {selectedRequest.opersac_name}</p>
            <p className="text-sm"><strong>Estacion:</strong> {selectedRequest.station_name}</p>
            <p className="text-sm"><strong>Barra:</strong> {selectedRequest.bar_type}</p>
            <p className="text-sm"><strong>Carga solicitada:</strong> {selectedRequest.requested_load_kw} kW</p>
            <p className="text-sm"><strong>Justificacion:</strong> {selectedRequest.justification || 'N/A'}</p>
            <p className="text-sm"><strong>Estado:</strong> <Badge color={statusColor(selectedRequest.status)}>{statusLabel(selectedRequest.status)}</Badge></p>
            {isAdmin && selectedRequest.status === 'pending' && (
              <div className="flex gap-2 pt-4 border-t border-[var(--border-color)]">
                <Button onClick={() => handleApprove(selectedRequest.id)}>Aprobar</Button>
                <Button variant="danger" onClick={() => setShowRejectForm(true)}>Rechazar</Button>
              </div>
            )}
          </div>
        </Modal>
      )}

      {showRejectForm && selectedRequest && (
        <Modal isOpen onClose={() => setShowRejectForm(false)} title="Rechazar Solicitud" size="md">
          <div className="space-y-4">
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="Escriba la razon del rechazo..."
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] min-h-[100px]"
            />
            <div className="flex gap-2 justify-end">
              <Button variant="secondary" onClick={() => setShowRejectForm(false)}>Cancelar</Button>
              <Button variant="danger" onClick={() => handleReject(selectedRequest.id)} disabled={!rejectionReason}>Confirmar Rechazo</Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
