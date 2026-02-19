import { useState } from 'react';
import type { Circuit } from '../../types';
import { CIRCUIT_STATUS_LABELS, CIRCUIT_STATUS_COLORS } from '../../config/constants';
import { circuitService } from '../../services/circuitService';
import Modal from '../ui/Modal';
import Button from '../ui/Button';

interface StatusChangeModalProps {
  barId: number;
  circuits: Circuit[];
  onClose: () => void;
  onSaved: () => void;
}

export default function StatusChangeModal({ barId, circuits, onClose, onSaved }: StatusChangeModalProps) {
  const [statuses, setStatuses] = useState<Record<number, string>>(
    Object.fromEntries(circuits.map((c) => [c.id, c.status]))
  );
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      for (const circuit of circuits) {
        if (statuses[circuit.id] !== circuit.status) {
          await circuitService.updateStatus(circuit.id, statuses[circuit.id]);
        }
      }
      onSaved();
    } catch (error) {
      console.error('Error saving statuses:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} title="Cambiar Estado de Circuitos" size="lg">
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {circuits.map((circuit) => (
          <div key={circuit.id} className="flex items-center justify-between p-3 rounded-lg border border-[var(--border-color)]">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CIRCUIT_STATUS_COLORS[statuses[circuit.id]] }} />
              <span className="text-sm text-[var(--text-primary)]">{circuit.name}</span>
            </div>
            <select
              value={statuses[circuit.id]}
              onChange={(e) => setStatuses({ ...statuses, [circuit.id]: e.target.value })}
              className="px-2 py-1 text-sm rounded border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]"
            >
              {Object.entries(CIRCUIT_STATUS_LABELS).filter(([k]) => k !== 'inactive').map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        ))}
      </div>
      <div className="flex gap-2 justify-end mt-4">
        <Button variant="secondary" onClick={onClose}>Cancelar</Button>
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? 'Guardando...' : 'Guardar Cambios'}
        </Button>
      </div>
    </Modal>
  );
}
