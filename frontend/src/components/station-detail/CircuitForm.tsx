import { useState } from 'react';
import type { Bar } from '../../types';
import { circuitService } from '../../services/circuitService';
import Modal from '../ui/Modal';
import Input from '../ui/Input';
import Button from '../ui/Button';

interface CircuitFormProps {
  barId: number;
  bars: Bar[];
  onClose: () => void;
  onCreated: () => void;
}

export default function CircuitForm({ barId, bars, onClose, onCreated }: CircuitFormProps) {
  const [denomination, setDenomination] = useState('');
  const [name, setName] = useState('');
  const [status, setStatus] = useState('operative_normal');
  const [localItem, setLocalItem] = useState('');
  const [piKw, setPiKw] = useState('');
  const [fd, setFd] = useState('1.0');
  const [isUps, setIsUps] = useState(false);
  const [secondaryBarId, setSecondaryBarId] = useState<number | null>(null);
  const [tertiaryBarId, setTertiaryBarId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const mdKw = (parseFloat(piKw) || 0) * (parseFloat(fd) || 1);
  const otherBars = bars.filter((b) => b.id !== barId);
  const tertiaryOptions = otherBars.filter((b) => b.id !== secondaryBarId);

  const handleSecondaryChange = (id: number | null) => {
    setSecondaryBarId(id);
    if (id && tertiaryBarId === id) {
      setTertiaryBarId(null);
    }
  };

  const handleSubmit = async () => {
    if (!denomination || !name || !piKw) {
      setError('Complete los campos obligatorios');
      return;
    }
    if (isUps && (!secondaryBarId || !tertiaryBarId)) {
      setError('UPS requiere seleccionar ambas barras de conexion');
      return;
    }
    setIsSubmitting(true);
    setError('');

    const payload = {
      denomination,
      name,
      status,
      local_item: localItem || undefined,
      pi_kw: parseFloat(piKw),
      fd: parseFloat(fd),
      is_ups: isUps,
      secondary_bar_id: isUps ? secondaryBarId : undefined,
      tertiary_bar_id: isUps ? tertiaryBarId : undefined,
    };

    try {
      await circuitService.create(barId, payload);
      onCreated();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (detail?.requires_force) {
        if (confirm(`${detail.message}. Desea continuar de todas formas?`)) {
          try {
            await circuitService.create(barId, { ...payload, force: true });
            onCreated();
          } catch {
            setError('Error al crear el circuito');
          }
        }
      } else {
        setError(typeof detail === 'string' ? detail : 'Error al crear el circuito');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} title="Agregar Nuevo Circuito" size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Input label="Denominacion *" value={denomination} onChange={(e) => setDenomination(e.target.value)} />
          <Input label="Nombre *" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Estado</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]">
              <option value="operative_normal">Operativo Normal</option>
              <option value="reserve_r">Reserva (R)</option>
              <option value="reserve_equipped_re">Reserva Equipada (R/E)</option>
            </select>
          </div>
          <Input label="Local/ITEM" value={localItem} onChange={(e) => setLocalItem(e.target.value)} />
        </div>
        <div className="grid grid-cols-3 gap-4">
          <Input label="PI (kW) *" type="number" step="0.01" value={piKw} onChange={(e) => setPiKw(e.target.value)} />
          <Input label="F.D" type="number" step="0.0001" value={fd} onChange={(e) => setFd(e.target.value)} />
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">MD (kW)</label>
            <div className="px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)]">
              {mdKw.toFixed(2)}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <input type="checkbox" id="isUps" checked={isUps} onChange={(e) => setIsUps(e.target.checked)} className="rounded border-[var(--border-color)]" />
          <label htmlFor="isUps" className="text-sm text-[var(--text-secondary)]">Es UPS?</label>
        </div>
        {isUps && otherBars.length > 0 && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Conexion 1</label>
              <select
                value={secondaryBarId || ''}
                onChange={(e) => handleSecondaryChange(e.target.value ? Number(e.target.value) : null)}
                className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]"
              >
                <option value="">Seleccione barra</option>
                {otherBars.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Conexion 2</label>
              <select
                value={tertiaryBarId || ''}
                onChange={(e) => setTertiaryBarId(e.target.value ? Number(e.target.value) : null)}
                className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]"
              >
                <option value="">Seleccione barra</option>
                {tertiaryOptions.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>
          </div>
        )}
        {error && <p className="text-sm text-red-500">{error}</p>}
        <div className="flex gap-2 justify-end">
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Creando...' : 'Crear Circuito'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
