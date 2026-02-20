import { useState, useEffect } from 'react';
import { Trash2 } from 'lucide-react';
import type { Observation } from '../../types';
import { OBSERVATION_SEVERITY_COLORS } from '../../config/constants';
import { useAuth } from '../../context/AuthContext';
import api from '../../config/api';
import Modal from '../ui/Modal';
import Button from '../ui/Button';

interface ObservationsModalProps {
  barId?: number;
  circuitId?: number;
  onClose: () => void;
}

export default function ObservationsModal({ barId, circuitId, onClose }: ObservationsModalProps) {
  const { user, hasPermission } = useAuth();
  const isAdmin = user?.role === 'admin';
  const canAddObservations = hasPermission('add_observations');
  const [observations, setObservations] = useState<Observation[]>([]);
  const [content, setContent] = useState('');
  const [severity, setSeverity] = useState('recommendation');

  const loadObservations = async () => {
    const endpoint = circuitId
      ? `/observations/circuit/${circuitId}`
      : `/observations/bar/${barId}`;
    const res = await api.get(endpoint);
    setObservations(res.data);
  };

  useEffect(() => {
    loadObservations();
  }, [barId, circuitId]);

  const handleDelete = async (id: number) => {
    await api.delete(`/observations/${id}`);
    loadObservations();
  };

  const handleSubmit = async () => {
    if (!content) return;
    await api.post('/observations', {
      content,
      severity,
      circuit_id: circuitId || null,
      bar_id: barId || null,
    });
    setContent('');
    loadObservations();
  };

  return (
    <Modal isOpen onClose={onClose} title="Observaciones" size="lg">
      <div className="max-h-96 overflow-y-auto space-y-3 mb-4">
        {observations.length === 0 && (
          <p className="text-sm text-[var(--text-muted)] text-center py-4">No hay observaciones</p>
        )}
        {observations.map((obs) => (
          <div
            key={obs.id}
            className="p-3 rounded-lg border-l-4 bg-[var(--bg-secondary)]"
            style={{ borderColor: OBSERVATION_SEVERITY_COLORS[obs.severity] }}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-[var(--text-secondary)]">
                {obs.user_role} - {obs.user_name}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--text-muted)]">
                  {new Date(obs.created_at).toLocaleDateString()}
                </span>
                {isAdmin && (
                  <button
                    onClick={() => handleDelete(obs.id)}
                    className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/20 text-[var(--text-muted)] hover:text-red-500 transition-colors cursor-pointer"
                    title="Eliminar observacion"
                  >
                    <Trash2 size={12} />
                  </button>
                )}
              </div>
            </div>
            <p className="text-sm text-[var(--text-primary)]">{obs.content}</p>
          </div>
        ))}
      </div>

      {canAddObservations && (
        <div className="border-t border-[var(--border-color)] pt-4 space-y-3">
          <div className="flex gap-2">
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] text-sm"
            >
              <option value="recommendation">Recomendacion</option>
              <option value="warning">Advertencia</option>
              <option value="urgent">Urgente</option>
            </select>
            <input
              type="text"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Escribir observacion..."
              className="flex-1 px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] text-sm"
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            />
            <Button size="sm" onClick={handleSubmit} disabled={!content}>Enviar</Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
