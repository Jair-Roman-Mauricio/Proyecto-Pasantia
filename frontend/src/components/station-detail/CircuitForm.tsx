import { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import type { Bar, Circuit } from '../../types';
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

/**
 * Formulario modal para crear un nuevo circuito en una barra dada.
 * Incluye cálculo automático de MD, validación de fecha de reserva
 * y configuración de barras secundaria/terciaria para circuitos UPS.
 */
export default function CircuitForm({ barId, bars, onClose, onCreated }: CircuitFormProps) {
  const [denomination, setDenomination] = useState('');
  const [name, setName] = useState('');
  const [status, setStatus] = useState('operative_normal');
  // Fecha de vencimiento de la reserva; solo aplica cuando el estado es reserve_r o reserve_equipped_re
  const [reserveExpiresAt, setReserveExpiresAt] = useState('');
  const [description, setDescription] = useState('');
  // Potencia instalada en kW (PI); junto con FD determina la MD
  const [piKw, setPiKw] = useState('');
  // Factor de demanda (FD); valor por defecto 1.0 representa uso al 100%
  const [fd, setFd] = useState('1.0');
  // Indica si el circuito está alimentado por un UPS (requiere dos barras de conexión)
  const [isUps, setIsUps] = useState(false);
  // Barra secundaria de conexión UPS (Conexion 1)
  const [secondaryBarId, setSecondaryBarId] = useState<number | null>(null);
  // Barra terciaria de conexión UPS (Conexion 2); no puede coincidir con la secundaria
  const [tertiaryBarId, setTertiaryBarId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  // Mensaje de advertencia del backend cuando la creación requiere confirmación forzada
  const [forceMessage, setForceMessage] = useState<string | null>(null);
  // Payload guardado temporalmente mientras el usuario decide si confirmar la creación forzada
  const [pendingPayload, setPendingPayload] = useState<Record<string, unknown> | null>(null);

  // Determina si el estado seleccionado corresponde a una reserva (excluye UPS, que no puede ser reserva)
  const isReserve = !isUps && (status === 'reserve_r' || status === 'reserve_equipped_re');
  const today = new Date().toISOString().split('T')[0];

  // Cálculo automático de MD (Máxima Demanda) = PI × FD en tiempo real
  // El campo MD es de solo lectura y se recalcula con cada cambio en PI o FD
  const mdKw = (parseFloat(piKw) || 0) * (parseFloat(fd) || 1);

  // Barras disponibles para conexiones UPS: excluye la barra principal (barId)
  const otherBars = bars.filter((b) => b.id !== barId);
  // La barra terciaria excluye además la que ya fue seleccionada como secundaria para evitar duplicados
  const tertiaryOptions = otherBars.filter((b) => b.id !== secondaryBarId);

  /**
   * Actualiza la barra secundaria y limpia la terciaria si coincidía con la nueva selección,
   * garantizando que las dos conexiones UPS sean siempre barras distintas.
   */
  const handleSecondaryChange = (id: number | null) => {
    setSecondaryBarId(id);
    if (id && tertiaryBarId === id) {
      setTertiaryBarId(null);
    }
  };

  /**
   * Construye el payload para la API.
   * reserve_expires_at solo se incluye si el circuito es de tipo reserva.
   * secondary_bar_id y tertiary_bar_id solo se incluyen si el circuito es UPS.
   */
  const buildPayload = () => ({
    denomination,
    name,
    status,
    reserve_expires_at: isReserve ? reserveExpiresAt : undefined,
    description: description || undefined,
    pi_kw: parseFloat(piKw),
    fd: parseFloat(fd),
    is_ups: isUps,
    secondary_bar_id: isUps ? secondaryBarId : undefined,
    tertiary_bar_id: isUps ? tertiaryBarId : undefined,
  });

  const handleSubmit = async () => {
    // Validación de campos obligatorios básicos
    if (!denomination || !name || !piKw) {
      setError('Complete los campos obligatorios');
      return;
    }
    // Validación de fecha de expiración: obligatoria para circuitos en estado de reserva
    if (isReserve && !reserveExpiresAt) {
      setError('Debe indicar la fecha de vencimiento de la reserva');
      return;
    }
    // Validación de conexiones UPS: ambas barras son requeridas cuando isUps es verdadero
    if (isUps && (!secondaryBarId || !tertiaryBarId)) {
      setError('UPS requiere seleccionar ambas barras de conexion');
      return;
    }
    // Validación de valores numéricos no negativos
    if (parseFloat(piKw) < 0) {
      setError('PI (kW) no puede ser negativo');
      return;
    }
    if (parseFloat(fd) < 0) {
      setError('El Factor de Demanda no puede ser negativo');
      return;
    }
    setIsSubmitting(true);
    setError('');

    const payload = buildPayload();

    try {
      await circuitService.create(barId, payload as Partial<Circuit> & { force?: boolean });
      onCreated();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      // Si el backend requiere confirmación explícita (ej. superar capacidad del tablero),
      // se guarda el payload y se muestra el modal de confirmación forzada
      if (detail?.requires_force) {
        setPendingPayload(payload);
        setForceMessage(detail.message);
      } else {
        setError(typeof detail === 'string' ? detail : 'Error al crear el circuito');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Reintenta la creación con el flag force:true para confirmar explícitamente la advertencia del backend
  const handleForceConfirm = async () => {
    if (!pendingPayload) return;
    setIsSubmitting(true);
    setForceMessage(null);
    try {
      await circuitService.create(barId, { ...pendingPayload, force: true } as Partial<Circuit> & { force?: boolean });
      onCreated();
    } catch {
      setError('Error al crear el circuito');
    } finally {
      setIsSubmitting(false);
      setPendingPayload(null);
    }
  };

  // Cancela la creación forzada y descarta el payload pendiente
  const handleForceCancel = () => {
    setForceMessage(null);
    setPendingPayload(null);
  };

  return (
    <>
      <Modal isOpen onClose={onClose} title="Agregar Nuevo Circuito" size="lg">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Denominacion *" value={denomination} onChange={(e) => setDenomination(e.target.value)} />
            <Input label="Nombre *" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Estado</label>
              {/* Al cambiar el estado se limpia la fecha de reserva previa para evitar inconsistencias */}
              <select value={status} onChange={(e) => { setStatus(e.target.value); setReserveExpiresAt(''); }} className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]">
                <option value="operative_normal">Operativo Normal</option>
                <option value="reserve_r">Reserva (R)</option>
                <option value="reserve_equipped_re">Reserva Equipada (R/E)</option>
              </select>
            </div>
            <Input label="Descripcion" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          {/* Campo de fecha de expiración: aparece condicionalmente solo para estados de reserva */}
          {isReserve && (
            <Input
              label="Reserva válida hasta *"
              type="date"
              value={reserveExpiresAt}
              onChange={(e) => setReserveExpiresAt(e.target.value)}
              min={today}
            />
          )}
          {/* Bloque de potencia: PI y FD son editables; MD se calcula automáticamente y es de solo lectura */}
          <div className="grid grid-cols-3 gap-4">
            <Input label="PI (kW) *" type="number" step="0.01" min="0" value={piKw} onChange={(e) => setPiKw(e.target.value)} />
            <Input label="F.D" type="number" step="0.0001" min="0" max="1" value={fd} onChange={(e) => setFd(e.target.value)} />
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">MD (kW)</label>
              {/* MD = PI × FD — campo de solo lectura, actualizado en tiempo real */}
              <div className="px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)]">
                {mdKw.toFixed(2)}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="isUps" checked={isUps} onChange={(e) => setIsUps(e.target.checked)} className="rounded border-[var(--border-color)]" />
            <label htmlFor="isUps" className="text-sm text-[var(--text-secondary)]">Es UPS?</label>
          </div>
          {/* Selectores de barras secundaria y terciaria: visibles solo cuando isUps está activo */}
          {isUps && otherBars.length > 0 && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Conexion 1</label>
                {/* Barra secundaria (primera conexión UPS); su cambio puede limpiar la terciaria */}
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
                {/* Barra terciaria (segunda conexión UPS); excluye la barra ya usada como secundaria */}
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

      {/* Modal de confirmación forzada: aparece cuando el backend detecta una condición de advertencia
          (ej. superar la capacidad instalada) y requiere que el usuario acepte explícitamente */}
      {forceMessage && (
        <Modal isOpen onClose={handleForceCancel} title="Confirmar accion" size="sm">
          <div className="space-y-4">
            <div className="flex gap-3">
              <AlertTriangle className="text-yellow-500 shrink-0 mt-0.5" size={20} />
              <p className="text-sm text-[var(--text-primary)]">
                {forceMessage}. ¿Desea continuar de todas formas?
              </p>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="secondary" onClick={handleForceCancel}>Cancelar</Button>
              <Button onClick={handleForceConfirm} disabled={isSubmitting}>
                {isSubmitting ? 'Creando...' : 'Continuar'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
