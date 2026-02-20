import { useState } from 'react';
import type { Circuit, SubCircuit } from '../../types';
import { CIRCUIT_STATUS_LABELS, CIRCUIT_STATUS_COLORS } from '../../config/constants';
import { circuitService } from '../../services/circuitService';
import Modal from '../ui/Modal';
import Button from '../ui/Button';

type StatusChangeModalProps = {
  onClose: () => void;
  onSaved: () => void;
} & (
  | { mode: 'circuits'; barId: number; circuits: Circuit[] }
  | { mode: 'sub-circuits'; circuitId: number; subCircuits: SubCircuit[] }
);

export default function StatusChangeModal(props: StatusChangeModalProps) {
  const items = props.mode === 'circuits' ? props.circuits : props.subCircuits;

  const [statuses, setStatuses] = useState<Record<number, string>>(
    Object.fromEntries(items.map((item) => [item.id, item.status]))
  );
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      for (const item of items) {
        if (statuses[item.id] !== item.status) {
          if (props.mode === 'circuits') {
            await circuitService.updateStatus(item.id, statuses[item.id]);
          } else {
            await circuitService.updateSubCircuitStatus(item.id, statuses[item.id]);
          }
        }
      }
      props.onSaved();
    } catch (error) {
      console.error('Error saving statuses:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const title = props.mode === 'circuits'
    ? 'Cambiar Estado de Circuitos'
    : 'Cambiar Estado de Sub-Circuitos';

  return (
    <Modal isOpen onClose={props.onClose} title={title} size="lg">
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {items.map((item) => (
          <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-[var(--border-color)]">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CIRCUIT_STATUS_COLORS[statuses[item.id]] }} />
              <span className="text-sm text-[var(--text-primary)]">{item.name}</span>
            </div>
            <select
              value={statuses[item.id]}
              onChange={(e) => setStatuses({ ...statuses, [item.id]: e.target.value })}
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
        <Button variant="secondary" onClick={props.onClose}>Cancelar</Button>
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? 'Guardando...' : 'Guardar Cambios'}
        </Button>
      </div>
    </Modal>
  );
}
