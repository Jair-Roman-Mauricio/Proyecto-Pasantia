/**
 * Formulario modal para que un opersac cree una solicitud de ampliación de carga.
 * Soporta dos flujos:
 *  1. Nuevo circuito en la barra: el usuario elige estación, barra y proporciona datos del circuito.
 *  2. Nuevo sub-circuito en un circuito existente: el usuario selecciona además el circuito padre
 *     y completa los datos adicionales del sub-circuito (ITM, MM2, etc.).
 * Los selectores de barra y circuito son dependientes (se recargan en cascada al cambiar la estación).
 */
import { useState, useEffect } from 'react';
import type { Station, Bar } from '../../types';
import { stationService } from '../../services/stationService';
import api from '../../config/api';
import Modal from '../ui/Modal';
import Input from '../ui/Input';
import Button from '../ui/Button';

/** Props del formulario de nueva solicitud */
interface RequestFormProps {
  /** Callback para cerrar el modal sin crear la solicitud */
  onClose: () => void;
  /** Callback invocado tras la creación exitosa para refrescar la tabla padre */
  onCreated: () => void;
}

/** Etiquetas legibles en español para cada tipo de barra */
const BAR_TYPE_LABELS: Record<string, string> = {
  normal: 'Normal',
  emergency: 'Emergencia',
  continuity: 'Continuidad',
};

export default function RequestForm({ onClose, onCreated }: RequestFormProps) {
  const [stations, setStations] = useState<Station[]>([]);
  const [bars, setBars] = useState<Bar[]>([]);
  const [circuits, setCircuits] = useState<{ id: number; denomination: string; name: string }[]>([]);

  const [stationId, setStationId] = useState<number | ''>('');
  const [barType, setBarType] = useState('');
  const [circuitId, setCircuitId] = useState<number | ''>('');
  const [localItem, setLocalItem] = useState('');
  const [loadKw, setLoadKw] = useState('');
  const [fd, setFd] = useState('1.0');
  const [subName, setSubName] = useState('');
  const [subDescription, setSubDescription] = useState('');
  const [subItm, setSubItm] = useState('');
  const [subMm2, setSubMm2] = useState('');
  const [justification, setJustification] = useState('');

  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Carga todas las estaciones al montar para poblar el primer selector
  useEffect(() => {
    stationService.getAll().then(setStations).catch(() => {});
  }, []);

  // Al cambiar de estación, resetea barra, circuitos y carga las nuevas barras
  useEffect(() => {
    setBars([]);
    setBarType('');
    setCircuits([]);
    setCircuitId('');
    if (stationId) {
      stationService.getBars(Number(stationId)).then(setBars).catch(() => {});
    }
  }, [stationId]);

  // Al cambiar el tipo de barra, carga los circuitos disponibles para esa barra
  // El endpoint /requests/circuit-options retorna solo los circuitos operativos elegibles
  useEffect(() => {
    setCircuits([]);
    setCircuitId('');
    if (barType && stationId) {
      const selectedBar = bars.find((b) => b.bar_type === barType);
      if (selectedBar) {
        api.get(`/requests/circuit-options/${selectedBar.id}`).then((res) => setCircuits(res.data)).catch(() => {});
      }
    }
  }, [barType, bars, stationId]);

  /**
   * Valida los campos obligatorios y envía la solicitud al servidor.
   * Los campos de sub-circuito se incluyen en el payload solo cuando hay un circuito
   * padre seleccionado (circuitId != ''), evitando enviar datos vacíos al backend.
   */
  const handleSubmit = async () => {
    if (!stationId || !barType || !loadKw) {
      setError('Complete los campos obligatorios');
      return;
    }
    // Si se seleccionó un circuito padre, la denominación del sub-circuito es obligatoria
    if (circuitId && !subName) {
      setError('Ingrese la denominacion del sub-circuito');
      return;
    }
    if (parseFloat(loadKw) < 0) {
      setError('PI (kW) no puede ser negativo');
      return;
    }
    if (parseFloat(fd) < 0) {
      setError('El Factor de Demanda no puede ser negativo');
      return;
    }
    setIsSubmitting(true);
    setError('');
    try {
      await api.post('/requests', {
        station_id: Number(stationId),
        bar_type: barType,
        circuit_id: circuitId || null,
        local_item: localItem || null,
        requested_load_kw: parseFloat(loadKw),
        // FD por defecto 1.0 si el usuario no ingresó un valor válido
        fd: parseFloat(fd) || 1.0,
        // Los campos de sub-circuito se envían solo si se seleccionó un circuito padre
        sub_circuit_name: circuitId ? subName || null : null,
        sub_circuit_description: circuitId ? subDescription || null : null,
        sub_circuit_itm: circuitId ? subItm || null : null,
        sub_circuit_mm2: circuitId ? subMm2 || null : null,
        justification: justification || null,
      });
      onCreated();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Error al enviar solicitud');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} title="Nueva Solicitud de Ampliacion" size="lg">
      <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
        <div>
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Estacion *</label>
          <select
            value={stationId}
            onChange={(e) => setStationId(e.target.value ? Number(e.target.value) : '')}
            className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]"
          >
            <option value="">Seleccione estacion</option>
            {stations.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Barra *</label>
          <select
            value={barType}
            onChange={(e) => setBarType(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]"
            disabled={!stationId}
          >
            <option value="">Seleccione barra</option>
            {bars.map((b) => (
              <option key={b.id} value={b.bar_type}>
                {b.name} ({BAR_TYPE_LABELS[b.bar_type] || b.bar_type})
              </option>
            ))}
          </select>
        </div>

        {circuits.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
              Circuito <span className="text-[var(--text-muted)] font-normal">(opcional - si es para sub-circuito)</span>
            </label>
            <select
              value={circuitId}
              onChange={(e) => setCircuitId(e.target.value ? Number(e.target.value) : '')}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]"
            >
              <option value="">Nuevo circuito en la barra</option>
              {circuits.map((c) => (
                <option key={c.id} value={c.id}>{c.denomination} / {c.name}</option>
              ))}
            </select>
          </div>
        )}

        {circuitId && (
          <div className="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-4">
            <p className="text-sm font-medium text-[var(--text-primary)]">Datos del Sub-circuito</p>
            <Input
              label="Denominacion *"
              value={subName}
              onChange={(e) => setSubName(e.target.value)}
              placeholder="Ej: Alumbrado zona A"
            />
            <Input
              label="Descripcion"
              value={subDescription}
              onChange={(e) => setSubDescription(e.target.value)}
              placeholder="Descripcion del sub-circuito"
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="ITM"
                value={subItm}
                onChange={(e) => setSubItm(e.target.value)}
                placeholder="Ej: 3x20A"
              />
              <Input
                label="MM2"
                value={subMm2}
                onChange={(e) => setSubMm2(e.target.value)}
                placeholder="Ej: 4"
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <Input
                label="PI (kW) *"
                type="number"
                step="0.01"
                min="0"
                value={loadKw}
                onChange={(e) => setLoadKw(e.target.value)}
                placeholder="Ej: 50.00"
              />
              <Input
                label="F.D"
                type="number"
                step="0.0001"
                min="0"
                value={fd}
                onChange={(e) => setFd(e.target.value)}
              />
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">MD (kW)</label>
                <div className="px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)]">
                  {((parseFloat(loadKw) || 0) * (parseFloat(fd) || 1)).toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        )}

        {!circuitId && (
          <>
            <Input
              label="Descripcion"
              value={localItem}
              onChange={(e) => setLocalItem(e.target.value)}
              placeholder="Descripcion del circuito solicitado"
            />

            <div className="grid grid-cols-3 gap-4">
              <Input
                label="PI (kW) *"
                type="number"
                step="0.01"
                min="0"
                value={loadKw}
                onChange={(e) => setLoadKw(e.target.value)}
                placeholder="Ej: 50.00"
              />
              <Input
                label="F.D"
                type="number"
                step="0.0001"
                min="0"
                value={fd}
                onChange={(e) => setFd(e.target.value)}
              />
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">MD (kW)</label>
                <div className="px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)]">
                  {((parseFloat(loadKw) || 0) * (parseFloat(fd) || 1)).toFixed(2)}
                </div>
              </div>
            </div>
          </>
        )}

        <div>
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Justificacion</label>
          <textarea
            value={justification}
            onChange={(e) => setJustification(e.target.value)}
            placeholder="Describa el motivo de la solicitud..."
            className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] min-h-[80px]"
          />
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <div className="flex gap-2 justify-end">
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Enviando...' : 'Enviar Solicitud'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
