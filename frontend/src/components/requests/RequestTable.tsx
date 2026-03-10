import { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import api from '../../config/api';
import type { LoadRequest } from '../../types';
import { useAuth } from '../../context/AuthContext';
import Table from '../ui/Table';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import RequestForm from './RequestForm';

/**
 * Tabla de solicitudes de ampliación de carga eléctrica.
 * Los administradores ven todas las solicitudes y pueden aprobarlas o rechazarlas.
 * Los opersac solo ven sus propias solicitudes y pueden crear nuevas.
 *
 * Flujo de aprobación:
 *  1. El opersac crea una solicitud con los datos del circuito/sub-circuito solicitado.
 *  2. El admin revisa el detalle y aprueba o rechaza.
 *  3. Al aprobar, el backend crea automáticamente el circuito correspondiente en la estación.
 *  4. Al rechazar, el admin debe proporcionar una razón que queda registrada en la solicitud.
 */
export default function RequestTable() {
  const { user } = useAuth();
  // Lista de solicitudes cargadas según el rol del usuario
  const [requests, setRequests] = useState<LoadRequest[]>([]);
  // Solicitud seleccionada para ver su detalle o gestionar aprobación/rechazo
  const [selectedRequest, setSelectedRequest] = useState<LoadRequest | null>(null);
  // Controla la visibilidad del formulario inline de motivo de rechazo
  const [showRejectForm, setShowRejectForm] = useState(false);
  // Texto del motivo de rechazo ingresado por el admin
  const [rejectionReason, setRejectionReason] = useState('');
  // Controla la visibilidad del formulario de nueva solicitud (solo opersac)
  const [showNewRequest, setShowNewRequest] = useState(false);
  const isAdmin = user?.role === 'admin';

  // Carga las solicitudes al montar el componente
  useEffect(() => { loadRequests(); }, []);

  /**
   * Carga solicitudes desde el endpoint correspondiente al rol:
   *  - admin:    /requests   → todas las solicitudes del sistema
   *  - opersac:  /requests/my → solo las solicitudes del usuario autenticado
   */
  const loadRequests = async () => {
    const endpoint = isAdmin ? '/requests' : '/requests/my';
    const { data } = await api.get(endpoint);
    setRequests(data);
  };

  /**
   * Aprueba una solicitud pendiente.
   * El backend procesa la aprobación y crea automáticamente el circuito
   * (o sub-circuito) en la estación/barra indicada en la solicitud.
   * Después de aprobar, cierra el modal de detalle y recarga la tabla.
   */
  const handleApprove = async (id: number) => {
    await api.put(`/requests/${id}/approve`);
    setSelectedRequest(null);
    loadRequests();
  };

  /**
   * Rechaza una solicitud pendiente con un motivo obligatorio.
   * La razón queda registrada en la solicitud y es visible para el opersac.
   * Requiere que rejectionReason no esté vacío antes de enviar.
   */
  const handleReject = async (id: number) => {
    if (!rejectionReason) return;
    await api.put(`/requests/${id}/reject`, { rejection_reason: rejectionReason });
    setShowRejectForm(false);
    setSelectedRequest(null);
    setRejectionReason('');
    loadRequests();
  };

  /**
   * Retorna el color del badge según el estado de la solicitud:
   *  - pending:  amarillo (en espera de revisión)
   *  - approved: verde    (aprobada, circuito creado)
   *  - rejected: rojo     (rechazada con motivo)
   */
  const statusColor = (s: string) => s === 'pending' ? 'yellow' : s === 'approved' ? 'green' : 'red';

  /** Retorna la etiqueta en español para cada estado de solicitud */
  const statusLabel = (s: string) => s === 'pending' ? 'Pendiente' : s === 'approved' ? 'Aprobado' : 'Rechazado';

  const columns = [
    { key: 'id', header: 'ID', className: 'hidden sm:table-cell' },
    { key: 'opersac_name', header: 'Opersac', className: 'hidden md:table-cell' },
    { key: 'station_name', header: 'Estacion' },
    { key: 'bar_type', header: 'Barra', render: (r: LoadRequest) => r.bar_type.charAt(0).toUpperCase() + r.bar_type.slice(1), className: 'hidden sm:table-cell' },
    { key: 'created_at', header: 'Fecha', render: (r: LoadRequest) => new Date(r.created_at).toLocaleDateString(), className: 'hidden sm:table-cell' },
    { key: 'requested_load_kw', header: 'Carga (kW)', render: (r: LoadRequest) => `${r.requested_load_kw} kW` },
    { key: 'status', header: 'Estado', render: (r: LoadRequest) => <Badge color={statusColor(r.status)}>{statusLabel(r.status)}</Badge> },
    { key: 'actions', header: 'Accion', render: (r: LoadRequest) => <Button variant="ghost" size="sm" onClick={() => setSelectedRequest(r)}>Ver Detalle</Button> },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-[var(--text-primary)]">
          {isAdmin ? 'Solicitudes de Ampliacion' : 'Mis Solicitudes'}
        </h2>
        {/* El botón de nueva solicitud solo es visible para usuarios opersac */}
        {!isAdmin && (
          <Button onClick={() => setShowNewRequest(true)}>
            <Plus size={16} className="mr-1" /> Nueva Solicitud
          </Button>
        )}
      </div>

      {/* Tabla principal con la lista de solicitudes */}
      <Table columns={columns} data={requests} rowKey={(r) => r.id} />

      {/* Modal de detalle de solicitud con datos técnicos y acciones de aprobación/rechazo para admin */}
      {selectedRequest && (
        <Modal isOpen onClose={() => setSelectedRequest(null)} title={`Solicitud #${selectedRequest.id}`} size="md">
          <div className="space-y-3">
            <p className="text-sm"><strong>Opersac:</strong> {selectedRequest.opersac_name}</p>
            <p className="text-sm"><strong>Estacion:</strong> {selectedRequest.station_name}</p>
            <p className="text-sm"><strong>Barra:</strong> {selectedRequest.bar_type}</p>
            {selectedRequest.circuit_name && (
              <p className="text-sm"><strong>Circuito:</strong> {selectedRequest.circuit_name}</p>
            )}
            {/* Datos del sub-circuito, visibles solo si la solicitud incluye uno */}
            {selectedRequest.sub_circuit_name && (
              <div className="p-3 rounded-lg bg-[var(--bg-secondary)] space-y-1">
                <p className="text-xs font-medium text-[var(--text-muted)] mb-2">Datos del Sub-circuito</p>
                <p className="text-sm"><strong>Denominacion:</strong> {selectedRequest.sub_circuit_name}</p>
                {selectedRequest.sub_circuit_description && (
                  <p className="text-sm"><strong>Descripcion:</strong> {selectedRequest.sub_circuit_description}</p>
                )}
                {selectedRequest.sub_circuit_itm && (
                  <p className="text-sm"><strong>ITM:</strong> {selectedRequest.sub_circuit_itm}</p>
                )}
                {selectedRequest.sub_circuit_mm2 && (
                  <p className="text-sm"><strong>MM2:</strong> {selectedRequest.sub_circuit_mm2}</p>
                )}
              </div>
            )}
            <p className="text-sm"><strong>Local/ITEM:</strong> {selectedRequest.local_item || 'N/A'}</p>
            <p className="text-sm"><strong>PI (kW):</strong> {selectedRequest.requested_load_kw} kW</p>
            <p className="text-sm"><strong>F.D:</strong> {selectedRequest.fd}</p>
            {/* MD calculado en frontend como PI × FD para visualización en el detalle */}
            <p className="text-sm"><strong>MD (kW):</strong> {(selectedRequest.requested_load_kw * selectedRequest.fd).toFixed(2)} kW</p>
            <p className="text-sm"><strong>Justificacion:</strong> {selectedRequest.justification || 'N/A'}</p>
            <p className="text-sm"><strong>Estado:</strong> <Badge color={statusColor(selectedRequest.status)}>{statusLabel(selectedRequest.status)}</Badge></p>
            {/* Botones de aprobar/rechazar: solo visibles para admin y cuando la solicitud está pendiente */}
            {isAdmin && selectedRequest.status === 'pending' && (
              <div className="flex gap-2 pt-4 border-t border-[var(--border-color)]">
                {/* Aprobar: el backend crea el circuito automáticamente al procesar esta acción */}
                <Button onClick={() => handleApprove(selectedRequest.id)}>Aprobar</Button>
                {/* Rechazar: abre el modal secundario para ingresar el motivo de rechazo */}
                <Button variant="danger" onClick={() => setShowRejectForm(true)}>Rechazar</Button>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Modal secundario para ingresar el motivo de rechazo; requiere texto no vacío para confirmar */}
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
              {/* El botón se habilita solo cuando el admin ha escrito un motivo */}
              <Button variant="danger" onClick={() => handleReject(selectedRequest.id)} disabled={!rejectionReason}>Confirmar Rechazo</Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal con el formulario de nueva solicitud (solo opersac) */}
      {showNewRequest && (
        <RequestForm onClose={() => setShowNewRequest(false)} onCreated={() => { setShowNewRequest(false); loadRequests(); }} />
      )}
    </div>
  );
}
