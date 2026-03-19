/**
 * Formulario modal para crear o editar un sub-circuito dentro de un circuito padre.
 * - Modo creación (editingSubCircuit ausente): usa POST /sub-circuits/circuit/{circuitId}
 * - Modo edición (editingSubCircuit presente): usa PUT /sub-circuits/{id}, pre-llena todos los campos
 * El campo MD se calcula automáticamente como PI × FD pero puede sobrescribirse manualmente.
 * La fecha de vencimiento de reserva es obligatoria solo cuando el estado es de tipo reserva.
 */
import { useState } from 'react';
import type { SubCircuit } from '../../types';
import { circuitService } from '../../services/circuitService';
import Modal from '../ui/Modal';
import Input from '../ui/Input';
import Button from '../ui/Button';

/** Props del formulario de sub-circuito */
interface SubCircuitFormProps {
  /** ID del circuito padre al que pertenecerá el nuevo sub-circuito */
  circuitId: number;
  /** Callback para cerrar el modal sin guardar */
  onClose: () => void;
  /** Callback invocado tras la creación o edición exitosa del sub-circuito */
  onCreated: () => void;
  /** Si se provee, el formulario opera en modo edición pre-llenando los campos con los datos del sub-circuito */
  editingSubCircuit?: SubCircuit;
}

export default function SubCircuitForm({ circuitId, onClose, onCreated, editingSubCircuit }: SubCircuitFormProps) {
  const isEditMode = !!editingSubCircuit;

  const [name, setName] = useState(editingSubCircuit?.name ?? '');
  const [description, setDescription] = useState(editingSubCircuit?.description ?? '');
  // ITM: especificación del interruptor termomagnético (ej. "3x20A")
  const [itm, setItm] = useState(editingSubCircuit?.itm ?? '');
  // MM2: sección del conductor en mm² (ej. "4")
  const [mm2, setMm2] = useState(editingSubCircuit?.mm2 ?? '');
  const [piKw, setPiKw] = useState(editingSubCircuit ? String(editingSubCircuit.pi_kw) : '');
  // Factor de demanda; 1.0 significa que el circuito opera al 100% de la PI
  const [fd, setFd] = useState(editingSubCircuit ? String(editingSubCircuit.fd) : '1.0');
  // MD puede ser ingresado manualmente o calculado automáticamente como PI × FD
  const [mdKw, setMdKw] = useState(editingSubCircuit ? String(editingSubCircuit.md_kw) : '');
  const [status, setStatus] = useState(editingSubCircuit?.status ?? 'operative_normal');
  const [reserveExpiresAt, setReserveExpiresAt] = useState(editingSubCircuit?.reserve_expires_at ?? '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Determina si el estado actual requiere fecha de vencimiento de reserva
  const isReserve = status === 'reserve_r' || status === 'reserve_equipped_re';
  const today = new Date().toISOString().split('T')[0];

  // Valores numéricos parseados para el cálculo automático de MD
  const piNum = parseFloat(piKw) || 0;
  const fdNum = parseFloat(fd) || 1;
  // MD calculada automáticamente; se muestra como referencia aunque el campo sea editable
  const calculatedMd = (piNum * fdNum).toFixed(2);

  /** Actualiza PI y recalcula MD automáticamente como PI × FD */
  const handlePiChange = (val: string) => {
    setPiKw(val);
    const pi = parseFloat(val) || 0;
    setMdKw((pi * fdNum).toFixed(2));
  };

  /** Actualiza FD y recalcula MD automáticamente como PI × FD */
  const handleFdChange = (val: string) => {
    setFd(val);
    const f = parseFloat(val) || 1;
    setMdKw((piNum * f).toFixed(2));
  };

  /**
   * Valida los campos requeridos y envía el sub-circuito al servidor.
   * - Modo creación: POST /sub-circuits/circuit/{circuitId}
   * - Modo edición: PUT /sub-circuits/{id}
   * MD usa el valor ingresado manualmente si existe; si no, usa el valor calculado.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !piKw) return;
    if (isReserve && !reserveExpiresAt) return;
    if (parseFloat(piKw) < 0) return;
    if (parseFloat(fd) < 0) return;
    if (mdKw && parseFloat(mdKw) < 0) return;
    setIsSubmitting(true);
    try {
      const payload = {
        name,
        description: description || undefined,
        itm: itm || undefined,
        mm2: mm2 || undefined,
        pi_kw: parseFloat(piKw),
        fd: parseFloat(fd),
        // Si el usuario editó MD manualmente usa ese valor; si no, usa el calculado
        md_kw: parseFloat(mdKw) || parseFloat(calculatedMd),
        status,
        reserve_expires_at: isReserve ? reserveExpiresAt : undefined,
      };

      if (isEditMode && editingSubCircuit) {
        await circuitService.updateSubCircuit(editingSubCircuit.id, payload);
      } else {
        await circuitService.createSubCircuit(circuitId, payload);
      }
      onCreated();
    } catch (error) {
      console.error(isEditMode ? 'Error updating sub-circuit:' : 'Error creating sub-circuit:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} title={isEditMode ? 'Editar Sub-circuito' : 'Agregar Sub-circuito'} size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Denominacion *"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Ej: Alumbrado zona A"
          required
        />
        <Input
          label="Descripcion"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Descripcion del sub-circuito"
        />
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="ITM"
            value={itm}
            onChange={(e) => setItm(e.target.value)}
            placeholder="Ej: 3x20A"
          />
          <Input
            label="MM2"
            value={mm2}
            onChange={(e) => setMm2(e.target.value)}
            placeholder="Ej: 4"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Estado</label>
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setReserveExpiresAt(''); }}
            className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]"
          >
            <option value="operative_normal">Operativo Normal</option>
            <option value="reserve_r">Reserva (R)</option>
            <option value="reserve_equipped_re">Reserva Equipada (R/E)</option>
          </select>
        </div>
        {isReserve && (
          <Input
            label="Reserva válida hasta *"
            type="date"
            value={reserveExpiresAt}
            onChange={(e) => setReserveExpiresAt(e.target.value)}
            min={today}
          />
        )}
        <div className="grid grid-cols-3 gap-4">
          <Input
            label="PI (kW) *"
            type="number"
            step="0.01"
            min="0"
            value={piKw}
            onChange={(e) => handlePiChange(e.target.value)}
            placeholder="0.00"
            required
          />
          <Input
            label="F.D"
            type="number"
            step="0.0001"
            min="0"
            max="1"
            value={fd}
            onChange={(e) => handleFdChange(e.target.value)}
            placeholder="1.0"
          />
          <Input
            label="MD (kW)"
            type="number"
            step="0.01"
            min="0"
            value={mdKw || calculatedMd}
            onChange={(e) => setMdKw(e.target.value)}
            placeholder="Auto"
          />
        </div>
        <p className="text-xs text-[var(--text-muted)]">
          MD se calcula automaticamente como PI x F.D = {calculatedMd} kW
        </p>
        <div className="flex gap-2 justify-end">
          <Button variant="secondary" type="button" onClick={onClose}>Cancelar</Button>
          <Button type="submit" disabled={!name || !piKw || (isReserve && !reserveExpiresAt) || isSubmitting}>
            {isSubmitting ? (isEditMode ? 'Guardando...' : 'Creando...') : (isEditMode ? 'Guardar cambios' : 'Crear Sub-circuito')}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
