import { useState, useEffect } from 'react';
import { Download, Star } from 'lucide-react';
import api from '../../config/api';
import type { AuditLog } from '../../types';
import Table from '../ui/Table';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

export default function AuditTable() {
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => { loadLogs(); }, []);

  const loadLogs = async () => {
    const { data } = await api.get('/audit');
    setLogs(data);
  };

  const handleFlag = async (log: AuditLog) => {
    const reason = log.is_flagged ? null : prompt('Razon para destacar esta accion:');
    await api.put(`/audit/${log.id}/flag`, { is_flagged: !log.is_flagged, flag_reason: reason });
    loadLogs();
  };

  const handleExportExcel = async () => {
    const response = await api.get('/audit/export/excel', { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'auditoria.xlsx';
    link.click();
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
      <Table
        columns={columns}
        data={logs}
        rowKey={(l) => l.id}
        rowClassName={(l) => l.is_flagged ? 'bg-yellow-50 dark:bg-yellow-900/10' : ''}
      />
    </div>
  );
}
