import { useState, useEffect } from 'react';
import { Download, Star, Search } from 'lucide-react';
import api from '../../config/api';
import type { AuditLog } from '../../types';
import Table from '../ui/Table';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Card from '../ui/Card';

export default function AuditTable() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');
  const [flaggedFilter, setFlaggedFilter] = useState('');

  useEffect(() => { loadLogs(); }, []);

  const loadLogs = async (filters?: Record<string, string>) => {
    const params: Record<string, string> = { limit: '200', ...filters };
    const { data } = await api.get('/audit', { params });
    setLogs(data);
  };

  const handleFilter = () => {
    const params: Record<string, string> = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (actionFilter) params.action = actionFilter;
    if (entityFilter) params.entity_type = entityFilter;
    if (flaggedFilter === 'true') params.is_flagged = 'true';
    if (flaggedFilter === 'false') params.is_flagged = 'false';
    loadLogs(params);
  };

  const handleClear = () => {
    setStartDate('');
    setEndDate('');
    setActionFilter('');
    setEntityFilter('');
    setFlaggedFilter('');
    loadLogs();
  };

  const hasFilters = startDate || endDate || actionFilter || entityFilter || flaggedFilter;

  const handleFlag = async (log: AuditLog) => {
    const reason = log.is_flagged ? null : prompt('Razon para destacar esta accion:');
    await api.put(`/audit/${log.id}/flag`, { is_flagged: !log.is_flagged, flag_reason: reason });
    handleFilter();
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
    { key: 'user_id', header: 'ID Usuario' },
    { key: 'user_role', header: 'Rol', render: (l: AuditLog) => <Badge color={l.user_role === 'admin' ? 'green' : 'blue'}>{l.user_role}</Badge> },
    { key: 'user_name', header: 'Nombre' },
    { key: 'action_date', header: 'Fecha', render: (l: AuditLog) => new Date(l.action_date).toLocaleString() },
    { key: 'action', header: 'Accion' },
    { key: 'entity_type', header: 'Entidad' },
    { key: 'entity_id', header: 'ID Entidad' },
    {
      key: 'flagged',
      header: 'Destacar',
      render: (l: AuditLog) => (
        <button onClick={() => handleFlag(l)} className="cursor-pointer p-1 rounded hover:bg-[var(--hover-bg)]">
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
          <div className="w-44">
            <Input label="Accion" placeholder="Ej: crear, aprobar..." value={actionFilter} onChange={(e) => setActionFilter(e.target.value)} />
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
          rowClassName={(l) => l.is_flagged ? 'bg-yellow-50 dark:bg-yellow-900/10' : ''}
        />
      </div>
    </div>
  );
}
