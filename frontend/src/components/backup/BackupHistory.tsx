import { useState, useEffect } from 'react';
import { Plus, RotateCcw, Trash2 } from 'lucide-react';
import api from '../../config/api';
import type { Backup } from '../../types';
import Table from '../ui/Table';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import Input from '../ui/Input';

export default function BackupHistory() {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [showRestore, setShowRestore] = useState<Backup | null>(null);
  const [showDelete, setShowDelete] = useState<Backup | null>(null);
  const [description, setDescription] = useState('');
  const [confirmText, setConfirmText] = useState('');

  useEffect(() => { loadBackups(); }, []);

  const loadBackups = async () => {
    const { data } = await api.get('/backups');
    setBackups(data);
  };

  const handleCreate = async () => {
    await api.post('/backups', { description, includes_audit: true });
    setShowCreate(false);
    setDescription('');
    loadBackups();
  };

  const handleRestore = async () => {
    if (!showRestore || confirmText !== 'CONFIRMAR') return;
    await api.post(`/backups/${showRestore.id}/restore`);
    setShowRestore(null);
    setConfirmText('');
  };

  const handleDelete = async () => {
    if (!showDelete) return;
    await api.delete(`/backups/${showDelete.id}`);
    setShowDelete(null);
    loadBackups();
  };

  const columns = [
    { key: 'id', header: 'ID' },
    { key: 'creator_name', header: 'Creado por' },
    { key: 'created_at', header: 'Fecha', render: (b: Backup) => new Date(b.created_at).toLocaleString() },
    { key: 'description', header: 'Descripcion' },
    { key: 'size_bytes', header: 'Tamano', render: (b: Backup) => b.size_bytes ? `${(b.size_bytes / 1024).toFixed(1)} KB` : '-' },
    { key: 'actions', header: 'Acciones', render: (b: Backup) => (
      <div className="flex gap-2">
        <Button variant="secondary" size="sm" onClick={() => setShowRestore(b)}>
          <RotateCcw size={14} className="mr-1" /> Restaurar
        </Button>
        <Button variant="danger" size="sm" onClick={() => setShowDelete(b)}>
          <Trash2 size={14} className="mr-1" /> Eliminar
        </Button>
      </div>
    )},
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-[var(--text-primary)]">Historial de Backups</h2>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus size={16} className="mr-1" /> Crear Backup
        </Button>
      </div>
      <Table columns={columns} data={backups} rowKey={(b) => b.id} />

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Crear Nuevo Backup" size="md">
        <div className="space-y-4">
          <Input label="Descripcion (opcional)" value={description} onChange={(e) => setDescription(e.target.value)} />
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancelar</Button>
            <Button onClick={handleCreate}>Crear Backup</Button>
          </div>
        </div>
      </Modal>

      {showRestore && (
        <Modal isOpen onClose={() => setShowRestore(null)} title="Restaurar Backup" size="md">
          <div className="space-y-4">
            <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-600 dark:text-red-400 font-medium">
                Esta accion reemplazara todos los datos actuales con los datos del backup.
              </p>
            </div>
            <p className="text-sm text-[var(--text-secondary)]">
              Backup: {showRestore.file_name} ({new Date(showRestore.created_at).toLocaleString()})
            </p>
            <Input label='Escriba CONFIRMAR para continuar' value={confirmText} onChange={(e) => setConfirmText(e.target.value)} />
            <div className="flex gap-2 justify-end">
              <Button variant="secondary" onClick={() => setShowRestore(null)}>Cancelar</Button>
              <Button variant="danger" onClick={handleRestore} disabled={confirmText !== 'CONFIRMAR'}>Restaurar</Button>
            </div>
          </div>
        </Modal>
      )}

      {showDelete && (
        <Modal isOpen onClose={() => setShowDelete(null)} title="Eliminar Backup" size="md">
          <div className="space-y-4">
            <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-600 dark:text-red-400 font-medium">
                Esta accion eliminara permanentemente este backup y no se podra recuperar.
              </p>
            </div>
            <p className="text-sm text-[var(--text-secondary)]">
              Backup: {showDelete.file_name} ({new Date(showDelete.created_at).toLocaleString()})
            </p>
            <div className="flex gap-2 justify-end">
              <Button variant="secondary" onClick={() => setShowDelete(null)}>Cancelar</Button>
              <Button variant="danger" onClick={handleDelete}>Eliminar</Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
