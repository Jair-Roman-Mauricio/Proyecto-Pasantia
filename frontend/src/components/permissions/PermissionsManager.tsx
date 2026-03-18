import { useState, useEffect } from 'react';
import api from '../../config/api';
import type { User, Permission } from '../../types';
import Card from '../ui/Card';
import Button from '../ui/Button';

/**
 * Mapa de claves de feature a sus etiquetas legibles en español.
 * Sirve como fuente de verdad para las features que pueden configurarse.
 */
const FEATURE_LABELS: Record<string, string> = {
  view_stations: 'Ver estaciones',
  view_circuits: 'Ver circuitos',
  send_requests: 'Enviar solicitudes',
  add_observations: 'Agregar observaciones',
  view_reports: 'Ver reportes',
};

// Lista completa de features disponibles en el sistema, derivada del mapa de etiquetas
const ALL_FEATURES = Object.keys(FEATURE_LABELS);

interface PermissionState {
  feature_key: string;
  is_allowed: boolean;
}

/**
 * Componente de gestión de permisos para usuarios con rol "opersac".
 * Permite al administrador activar o desactivar cada feature por usuario
 * y guardar los cambios en el servidor con un único request PUT.
 */
export default function PermissionsManager() {
  // Lista de usuarios con rol opersac disponibles para seleccionar
  const [users, setUsers] = useState<User[]>([]);
  // ID del usuario opersac cuyo perfil de permisos se está editando
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  // Estado local de permisos del usuario seleccionado (una entrada por cada feature)
  const [permissions, setPermissions] = useState<PermissionState[]>([]);
  // Indica que el guardado está en curso (deshabilita el botón)
  const [isSaving, setIsSaving] = useState(false);
  // Mensaje de éxito o error mostrado tras intentar guardar
  const [saveMessage, setSaveMessage] = useState('');

  // Carga solo los usuarios opersac al montar el componente
  useEffect(() => {
    api.get('/users').then((res) => {
      setUsers(res.data.filter((u: User) => u.role === 'opersac'));
    });
  }, []);

  /**
   * Al seleccionar un usuario, obtiene sus permisos existentes del servidor
   * y los combina (merge) con la lista completa de features disponibles.
   * Las features sin registro en el servidor se inicializan en false (denegado).
   * Esto garantiza que el formulario siempre muestre todas las features,
   * incluso las que aún no tienen un registro en la base de datos.
   */
  useEffect(() => {
    if (selectedUserId) {
      api.get<Permission[]>(`/permissions/users/${selectedUserId}`).then((res) => {
        const existing = res.data;
        // Construye la lista completa: para cada feature, busca el permiso existente
        // o asigna is_allowed: false si el usuario no tiene registro para esa feature
        const merged = ALL_FEATURES.map((key) => {
          const found = existing.find((p) => p.feature_key === key);
          return { feature_key: key, is_allowed: found ? found.is_allowed : false };
        });
        setPermissions(merged);
        setSaveMessage('');
      });
    }
  }, [selectedUserId]);

  // Alterna el valor de is_allowed de una feature específica en el estado local
  const togglePermission = (featureKey: string) => {
    setPermissions((prev) =>
      prev.map((p) => p.feature_key === featureKey ? { ...p, is_allowed: !p.is_allowed } : p)
    );
  };

  /**
   * Guarda todos los permisos del usuario en un único request PUT.
   * Envía el estado completo (todas las features con su valor actual),
   * permitiendo al backend hacer un upsert de cada registro de permiso.
   */
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

      {/* Selector de usuario opersac; al cambiar dispara la carga y merge de permisos */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Seleccionar Opersac</label>
        <select value={selectedUserId || ''} onChange={(e) => setSelectedUserId(e.target.value || null)} className="w-64 px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]">
          <option value="">Seleccione usuario</option>
          {users.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
        </select>
      </div>

      {/* Panel de checkboxes: visible solo cuando hay un usuario seleccionado */}
      {selectedUserId && (
        <Card>
          <div className="space-y-3">
            {permissions.map((p) => (
              // Cada checkbox representa una feature; su estado refleja is_allowed en tiempo real
              <label key={p.feature_key} className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={p.is_allowed} onChange={() => togglePermission(p.feature_key)} className="rounded border-[var(--border-color)]" />
                <span className="text-sm text-[var(--text-primary)]">{FEATURE_LABELS[p.feature_key] || p.feature_key}</span>
              </label>
            ))}
          </div>
          {/* Botón de guardado y mensaje de resultado (éxito en verde, error en rojo) */}
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
