import { useState, useEffect } from 'react';
import api from '../../config/api';
import type { User, Permission } from '../../types';
import Card from '../ui/Card';
import Button from '../ui/Button';

const FEATURE_LABELS: Record<string, string> = {
  view_stations: 'Ver estaciones',
  view_circuits: 'Ver circuitos',
  send_requests: 'Enviar solicitudes',
  add_observations: 'Agregar observaciones',
  view_reports: 'Ver reportes',
};

const ALL_FEATURES = Object.keys(FEATURE_LABELS);

interface PermissionState {
  feature_key: string;
  is_allowed: boolean;
}

export default function PermissionsManager() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [permissions, setPermissions] = useState<PermissionState[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  useEffect(() => {
    api.get('/users').then((res) => {
      setUsers(res.data.filter((u: User) => u.role === 'opersac'));
    });
  }, []);

  useEffect(() => {
    if (selectedUserId) {
      api.get<Permission[]>(`/permissions/users/${selectedUserId}`).then((res) => {
        const existing = res.data;
        const merged = ALL_FEATURES.map((key) => {
          const found = existing.find((p) => p.feature_key === key);
          return { feature_key: key, is_allowed: found ? found.is_allowed : false };
        });
        setPermissions(merged);
        setSaveMessage('');
      });
    }
  }, [selectedUserId]);

  const togglePermission = (featureKey: string) => {
    setPermissions((prev) =>
      prev.map((p) => p.feature_key === featureKey ? { ...p, is_allowed: !p.is_allowed } : p)
    );
  };

  const handleSave = async () => {
    if (!selectedUserId) return;
    setIsSaving(true);
    setSaveMessage('');
    try {
      await api.put(`/permissions/users/${selectedUserId}`, {
        permissions: permissions.map((p) => ({ feature_key: p.feature_key, is_allowed: p.is_allowed })),
      });
      setSaveMessage('Permisos guardados exitosamente');
    } catch {
      setSaveMessage('Error al guardar permisos');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4">Gestion de Permisos</h2>
      <div className="mb-4">
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Seleccionar Opersac</label>
        <select value={selectedUserId || ''} onChange={(e) => setSelectedUserId(Number(e.target.value))} className="w-64 px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]">
          <option value="">Seleccione usuario</option>
          {users.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
        </select>
      </div>
      {selectedUserId && (
        <Card>
          <div className="space-y-3">
            {permissions.map((p) => (
              <label key={p.feature_key} className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={p.is_allowed} onChange={() => togglePermission(p.feature_key)} className="rounded border-[var(--border-color)]" />
                <span className="text-sm text-[var(--text-primary)]">{FEATURE_LABELS[p.feature_key] || p.feature_key}</span>
              </label>
            ))}
          </div>
          <div className="mt-4 flex items-center gap-3">
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? 'Guardando...' : 'Guardar Permisos'}
            </Button>
            {saveMessage && (
              <span className={`text-sm ${saveMessage.includes('Error') ? 'text-red-500' : 'text-green-500'}`}>
                {saveMessage}
              </span>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
