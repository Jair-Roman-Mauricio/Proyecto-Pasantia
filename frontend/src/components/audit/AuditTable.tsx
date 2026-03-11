import { useState, useEffect } from 'react';
import { Download, Star, Search } from 'lucide-react';
import api from '../../config/api';
import type { AuditLog } from '../../types';
import Table from '../ui/Table';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Card from '../ui/Card';
import Modal from '../ui/Modal';

/**
 * Tabla de auditoría del sistema.
 * Permite filtrar los registros por fecha, acción, tipo de entidad y estado de marcado.
 * Los registros pueden marcarse como destacados (starred) para revisión posterior.
 * También permite exportar el historial completo a Excel.
 */
export default function AuditTable() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');
  const [flaggedFilter, setFlaggedFilter] = useState('');

  // Estado del modal de marcado
  const [flagTarget, setFlagTarget] = useState<AuditLog | null>(null);
  const [flagReason, setFlagReason] = useState('');
  const [flagLoading, setFlagLoading] = useState(false);

  useEffect(() => { loadLogs(); }, []);

  const buildParams = () => {
    const params: Record<string, string> = { limit: '200' };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (actionFilter) params.action = actionFilter;
    if (entityFilter) params.entity_type = entityFilter;
    if (flaggedFilter === 'true') params.is_flagged = 'true';
    if (flaggedFilter === 'false') params.is_flagged = 'false';
    return params;
  };

  const loadLogs = async (params?: Record<string, string>) => {
    const { data } = await api.get('/audit', { params: params ?? { limit: '200' } });
    setLogs(data);
  };

  const handleFilter = () => loadLogs(buildParams());

  const handleClear = () => {
    setStartDate('');
    setEndDate('');
    setActionFilter('');
    setEntityFilter('');
    setFlaggedFilter('');
    loadLogs();
  };

  const hasFilters = startDate || endDate || actionFilter || entityFilter || flaggedFilter;

  // Click en botón de marcar
  const handleFlagClick = async (log: AuditLog) => {
    if (log.is_flagged) {
      // Desmarcar directamente, sin necesidad de motivo
      await api.put(`/audit/${log.id}/flag`, { is_flagged: false, flag_reason: null });
      setLogs(prev => prev.map(l => l.id === log.id ? { ...l, is_flagged: false, flag_reason: null } : l));
    } else {
      // Abrir modal para ingresar el motivo
      setFlagTarget(log);
      setFlagReason('');
    }
  };

  // Confirmar marcado desde el modal
  const handleConfirmFlag = async () => {
    if (!flagTarget || !flagReason.trim()) return;
    setFlagLoading(true);
    try {
      await api.put(`/audit/${flagTarget.id}/flag`, { is_flagged: true, flag_reason: flagReason.trim() });
      setLogs(prev => prev.map(l =>
        l.id === flagTarget.id ? { ...l, is_flagged: true, flag_reason: flagReason.trim() } : l
      ));
      setFlagTarget(null);
      setFlagReason('');
    } finally {
      setFlagLoading(false);
    }
  };

  const handleCloseModal = () => {
    setFlagTarget(null);
    setFlagReason('');
  };

  const handleExportExcel = async () => {
    try {
      const response = await api.get('/audit/export/excel', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'auditoria.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Error al exportar auditoria.');
    }
  };

  const columns = [
    { key: 'user_id', header: 'ID Usuario', className: 'hidden lg:table-cell' },
    {
      key: 'user_role', header: 'Rol',
      render: (l: AuditLog) => <Badge color={l.user_role === 'admin' ? 'green' : 'blue'}>{l.user_role}</Badge>,
      className: 'hidden sm:table-cell',
    },
    { key: 'user_name', header: 'Nombre', className: 'hidden md:table-cell' },
    { key: 'action_date', header: 'Fecha', render: (l: AuditLog) => new Date(l.action_date).toLocaleString() },
    { key: 'action', header: 'Accion' },
    { key: 'entity_type', header: 'Entidad', className: 'hidden sm:table-cell' },
    { key: 'entity_id', header: 'ID Entidad', className: 'hidden lg:table-cell' },
    {
      key: 'flagged',
      header: 'Destacar',
      render: (l: AuditLog) => (
        <button
          onClick={() => handleFlagClick(l)}
          title={l.is_flagged ? (l.flag_reason ?? '') : 'Destacar registro'}
          className="cursor-pointer p-1 rounded hover:bg-[var(--hover-bg)]"
        >
          <Star size={16} className={l.is_flagged ? 'text-yellow-500 fill-yellow-500' : 'text-[var(--text-muted)]'} />
        </button>
      ),
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-[var(--text-primary)]">Auditoria</h2>
        <Button variant="secondary" size="sm" onClick={handleExportExcel}>
          <Download size={16} className="mr-1" /> Exportar Excel
        </Button>
      </div>

      <Card>
        <div className="flex items-end gap-4 flex-wrap">
          <div className="w-40">
            <Input label="Desde" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div className="w-40">
            <Input label="Hasta" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
          <div className="w-52">
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Accion</label>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Todas</option>
              <optgroup label="Circuitos">
                <option value="CREATE_CIRCUIT">Crear circuito</option>
                <option value="UPDATE_CIRCUIT">Editar circuito</option>
                <option value="CHANGE_CIRCUIT_STATUS">Cambiar estado circuito</option>
                <option value="DELETE_CIRCUIT">Eliminar circuito</option>
              </optgroup>
              <optgroup label="Sub-circuitos">
                <option value="CREATE_SUB_CIRCUIT">Crear sub-circuito</option>
                <option value="CHANGE_SUB_CIRCUIT_STATUS">Cambiar estado sub-circuito</option>
                <option value="DELETE_SUB_CIRCUIT">Eliminar sub-circuito</option>
              </optgroup>
              <optgroup label="Solicitudes">
                <option value="CREATE_REQUEST">Crear solicitud</option>
                <option value="APPROVE_REQUEST">Aprobar solicitud</option>
                <option value="REJECT_REQUEST">Rechazar solicitud</option>
              </optgroup>
              <optgroup label="Usuarios">
                <option value="CREATE_USER">Crear usuario</option>
                <option value="UPDATE_USER">Editar usuario</option>
                <option value="DELETE_USER">Eliminar usuario</option>
              </optgroup>
              <optgroup label="Otros">
                <option value="CREATE_BACKUP">Crear backup</option>
                <option value="RESTORE_BACKUP">Restaurar backup</option>
                <option value="DELETE_BACKUP">Eliminar backup</option>
                <option value="REPLACE_IMAGE">Reemplazar imagen</option>
                <option value="DELETE_OBSERVATION">Eliminar observacion</option>
              </optgroup>
            </select>
          </div>
          <div className="w-40">
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Entidad</label>
            <select
              value={entityFilter}
              onChange={(e) => setEntityFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Todas</option>
              <option value="station">Estacion</option>
              <option value="circuit">Circuito</option>
              <option value="sub_circuit">Sub-circuito</option>
              <option value="request">Solicitud</option>
              <option value="user">Usuario</option>
            </select>
          </div>
          <div className="w-36">
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Destacados</label>
            <select
              value={flaggedFilter}
              onChange={(e) => setFlaggedFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Todos</option>
              <option value="true">Solo destacados</option>
              <option value="false">No destacados</option>
            </select>
          </div>
          <Button size="sm" onClick={handleFilter}>
            <Search size={16} className="mr-1" /> Buscar
          </Button>
          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={handleClear}>
              Limpiar
            </Button>
          )}
        </div>
      </Card>

      <div className="mt-4">
        <Table
          columns={columns}
          data={logs}
          rowKey={(l) => l.id}
          rowClassName={(l) => l.is_flagged ? 'bg-yellow-500/10 border-l-4 border-yellow-500' : ''}
        />
      </div>

      {/* Flag reason modal */}
      <Modal isOpen={flagTarget !== null} onClose={handleCloseModal} title="Destacar registro" size="sm">
        <div className="space-y-4">
          {flagTarget && (
            <div className="p-3 bg-[var(--bg-secondary)] rounded-lg text-sm text-[var(--text-secondary)] space-y-1">
              <p><span className="font-medium text-[var(--text-primary)]">Accion:</span> {flagTarget.action}</p>
              <p><span className="font-medium text-[var(--text-primary)]">Usuario:</span> {flagTarget.user_name}</p>
              <p><span className="font-medium text-[var(--text-primary)]">Fecha:</span> {new Date(flagTarget.action_date).toLocaleString()}</p>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
              Razon <span className="text-red-500">*</span>
            </label>
            <textarea
              value={flagReason}
              onChange={(e) => setFlagReason(e.target.value)}
              placeholder="Indica por que este registro es importante..."
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
            {flagReason.trim() === '' && (
              <p className="text-xs text-red-500 mt-1">La razon es obligatoria para destacar un registro.</p>
            )}
          </div>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={handleCloseModal}>Cancelar</Button>
            <Button
              onClick={handleConfirmFlag}
              disabled={!flagReason.trim() || flagLoading}
            >
              <Star size={14} className="mr-1" />
              {flagLoading ? 'Guardando...' : 'Destacar'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
