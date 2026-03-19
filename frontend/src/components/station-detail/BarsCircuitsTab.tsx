import { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, Plus, Pencil } from 'lucide-react';
import api from '../../config/api';
import Modal from '../ui/Modal';
import Input from '../ui/Input';
import type { Station, Bar, Circuit, SubCircuit, BarPowerSummary } from '../../types';
import { stationService } from '../../services/stationService';
import { circuitService } from '../../services/circuitService';
import { useAuth } from '../../context/AuthContext';
import { useSidebar } from '../../context/SidebarContext';
import { CIRCUIT_STATUS_COLORS, CIRCUIT_STATUS_LABELS } from '../../config/constants';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Spinner from '../ui/Spinner';
import PowerCards from './PowerCards';
import CircuitTable from './CircuitTable';
import SubCircuitTable from './SubCircuitTable';
import CircuitForm from './CircuitForm';
import SubCircuitForm from './SubCircuitForm';
import ObservationsModal from './ObservationsModal';
import StatusChangeModal from './StatusChangeModal';

interface BarsCircuitsTabProps {
  station: Station;
  onStationChanged?: () => void;
}

/**
 * Pestaña principal de tableros (barras) y circuitos de una estación.
 * Muestra un árbol expandible en el panel izquierdo y el detalle en el derecho.
 * Gestiona la selección de barra/circuito y coordina la apertura de modales.
 */
export default function BarsCircuitsTab({ station, onStationChanged }: BarsCircuitsTabProps) {
  const { user, hasPermission } = useAuth();
  const { viewMode } = useSidebar();

  // Lista de barras/tableros de la estación
  const [bars, setBars] = useState<Bar[]>([]);
  // Conjunto de IDs de barras con el árbol expandido en el panel izquierdo
  const [expandedBars, setExpandedBars] = useState<Set<number>>(new Set());
  // Mapa de barraId → lista de circuitos cargados para esa barra
  const [barCircuits, setBarCircuits] = useState<Record<number, Circuit[]>>({});
  // Barra actualmente seleccionada para mostrar su detalle en el panel derecho
  const [selectedBar, setSelectedBar] = useState<Bar | null>(null);
  // Circuito actualmente seleccionado; al seleccionarlo se muestra la tabla de sub-circuitos
  const [selectedCircuit, setSelectedCircuit] = useState<Circuit | null>(null);
  // Mapa de barraId → resumen de potencia; cada barra mantiene su propio valor independiente
  const [powerSummaries, setPowerSummaries] = useState<Record<number, BarPowerSummary>>({});

  // Resumen de potencia de la barra actualmente seleccionada
  const powerSummary = selectedBar ? (powerSummaries[selectedBar.id] ?? null) : null;
  // Activa/desactiva el modo edición que habilita botones de cambio de estado y eliminación
  const [isEditMode, setIsEditMode] = useState(false);
  // Controla la visibilidad del modal de creación de nuevo circuito
  const [showCircuitForm, setShowCircuitForm] = useState(false);
  // Controla la visibilidad del modal de observaciones (barra o circuito)
  const [showObservations, setShowObservations] = useState(false);
  // Controla la visibilidad del modal de cambio de estado (circuitos o sub-circuitos)
  const [showStatusChange, setShowStatusChange] = useState(false);
  // Lista de sub-circuitos del circuito seleccionado
  const [subCircuits, setSubCircuits] = useState<SubCircuit[]>([]);
  // Controla la visibilidad del modal de creación de nuevo sub-circuito
  const [showSubCircuitForm, setShowSubCircuitForm] = useState(false);
  // ID de la barra para la que se está creando un circuito (se pasa al modal CircuitForm)
  const [formBarId, setFormBarId] = useState<number | null>(null);
  // Indica si la carga inicial de barras está en progreso
  const [isLoading, setIsLoading] = useState(true);
  // Controla el modal de edición de capacidad del tablero
  const [showCapacityForm, setShowCapacityForm] = useState(false);
  const [capacityKw, setCapacityKw] = useState('');
  const [capacityA, setCapacityA] = useState('');
  const [capacityError, setCapacityError] = useState('');

  // Solo los admins en modo admin pueden crear/editar; los opersac solo visualizan
  const isAdmin = user?.role === 'admin' && viewMode === 'admin';
  const canViewCircuits = hasPermission('view_circuits');

  // Carga las barras de la estación al montar el componente y expande la primera por defecto
  useEffect(() => {
    stationService.getBars(station.id).then((data) => {
      setBars(data);
      if (data.length > 0) {
        setExpandedBars(new Set([data[0].id]));
        setSelectedBar(data[0]);
      }
    }).catch(console.error).finally(() => setIsLoading(false));
  }, [station.id]);

  /**
   * Carga el resumen de potencia de una barra y lo guarda en el mapa por ID.
   * Cada barra mantiene su propio valor, evitando que una sobreescriba a otra.
   */
  const loadBarPowerSummary = (barId: number) => {
    circuitService.getBarPowerSummary(barId).then((summary) => {
      setPowerSummaries((prev) => ({ ...prev, [barId]: summary }));
    });
  };

  // Al cambiar la barra seleccionada, carga sus circuitos y el resumen de potencia
  useEffect(() => {
    if (selectedBar) {
      if (canViewCircuits) {
        circuitService.getByBar(selectedBar.id).then((circuits) => {
          setBarCircuits((prev) => ({ ...prev, [selectedBar.id]: circuits }));
        });
      }
      loadBarPowerSummary(selectedBar.id);
    }
  }, [selectedBar, canViewCircuits]);

  // Al seleccionar un circuito, carga sus sub-circuitos; al deseleccionar, limpia la lista
  useEffect(() => {
    if (selectedCircuit) {
      circuitService.getSubCircuits(selectedCircuit.id).then(setSubCircuits).catch(() => setSubCircuits([]));
    } else {
      setSubCircuits([]);
    }
  }, [selectedCircuit]);

  /**
   * Recarga los sub-circuitos, el resumen de potencia y los circuitos de la barra
   * después de cualquier cambio en sub-circuitos (creación, edición o eliminación).
   */
  const refreshAfterSubCircuitChange = () => {
    if (selectedCircuit) {
      circuitService.getSubCircuits(selectedCircuit.id).then(setSubCircuits);
    }
    if (selectedBar) {
      loadBarPowerSummary(selectedBar.id);
      loadBarCircuits(selectedBar.id);
    }
    onStationChanged?.();
  };

  /**
   * Alterna la expansión de una barra en el árbol del panel izquierdo.
   * Si la barra ya está expandida la colapsa, y viceversa.
   */
  const toggleBar = (barId: number) => {
    setExpandedBars((prev) => {
      const next = new Set(prev);
      if (next.has(barId)) next.delete(barId); else next.add(barId);
      return next;
    });
  };

  /**
   * Solicita al servicio los circuitos de una barra específica y actualiza el mapa barCircuits.
   * Se llama tras crear o eliminar un circuito para refrescar la lista sin recargar toda la página.
   */
  const loadBarCircuits = (barId: number) => {
    circuitService.getByBar(barId).then((circuits) => {
      setBarCircuits((prev) => ({ ...prev, [barId]: circuits }));
    });
  };

  // Cambia la barra seleccionada y limpia el circuito y el modo edición activos
  const handleBarSelect = (bar: Bar) => {
    setSelectedBar(bar);
    setSelectedCircuit(null);
    setIsEditMode(false);
  };

  // Callback tras crear un circuito: cierra el modal, recarga circuitos y resumen de potencia
  const handleCircuitCreated = () => {
    setShowCircuitForm(false);
    if (formBarId) loadBarCircuits(formBarId);
    if (selectedBar) loadBarPowerSummary(selectedBar.id);
    onStationChanged?.();
  };

  // Abre el modal de capacidad precargando los valores actuales de la barra seleccionada
  const openCapacityForm = () => {
    if (!selectedBar) return;
    setCapacityKw(Number(selectedBar.capacity_kw).toString());
    setCapacityA(Number(selectedBar.capacity_a).toString());
    setCapacityError('');
    setShowCapacityForm(true);
  };

  // Guarda la nueva capacidad del tablero y refresca el resumen de potencia
  const handleSaveCapacity = async () => {
    if (!selectedBar) return;
    const kw = parseFloat(capacityKw);
    const a = parseFloat(capacityA);
    if (isNaN(kw) || kw < 0 || isNaN(a) || a < 0) {
      setCapacityError('Ingrese valores numéricos válidos mayores o iguales a 0');
      return;
    }
    try {
      const { data } = await api.put(`/bars/${selectedBar.id}/capacity`, { capacity_kw: kw, capacity_a: a });
      setBars((prev) => prev.map((b) => b.id === selectedBar.id ? { ...b, capacity_kw: data.capacity_kw, capacity_a: data.capacity_a } : b));
      setShowCapacityForm(false);
      loadBarPowerSummary(selectedBar.id);
    } catch {
      setCapacityError('Error al guardar la capacidad');
    }
  };

  // Callback tras eliminar un circuito: recarga circuitos y resumen de potencia de la barra activa
  const handleCircuitDeleted = () => {
    if (selectedBar) {
      loadBarCircuits(selectedBar.id);
      loadBarPowerSummary(selectedBar.id);
    }
    onStationChanged?.();
  };

  if (isLoading) return <div className="flex justify-center py-12"><Spinner size="lg" /></div>;

  return (
    <div className="flex flex-col md:flex-row gap-4">
      {/* Panel izquierdo: árbol de tableros y sus circuitos */}
      <div className="w-full md:w-64 md:shrink-0">
        <Card className="sticky top-0">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Tableros</h3>
          <div className="space-y-1">
            {bars.map((bar) => (
              <div key={bar.id}>
                {/* Fila de barra: botón para expandir/colapsar y botón para agregar circuito (solo admin) */}
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => { toggleBar(bar.id); handleBarSelect(bar); }}
                    className={`flex-1 flex items-center gap-2 px-2 py-1.5 text-sm rounded-md transition-colors cursor-pointer ${
                      selectedBar?.id === bar.id ? 'bg-primary-600/20 text-primary-500 font-medium' : 'text-[var(--text-secondary)] hover:bg-[var(--hover-bg)]'
                    }`}
                  >
                    {expandedBars.has(bar.id) ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    <span className="truncate">{bar.name}</span>
                  </button>
                  {isAdmin && canViewCircuits && (
                    <button onClick={() => { setFormBarId(bar.id); setShowCircuitForm(true); }} className="p-1 rounded hover:bg-[var(--hover-bg)] text-[var(--text-muted)] cursor-pointer" title="Agregar circuito">
                      <Plus size={14} />
                    </button>
                  )}
                </div>
                {/* Lista de circuitos de la barra, visible solo si la barra está expandida y el usuario tiene permiso */}
                {canViewCircuits && expandedBars.has(bar.id) && barCircuits[bar.id] && (
                  <div className="ml-6 mt-1 space-y-0.5">
                    {barCircuits[bar.id].map((circuit) => (
                      <button
                        key={circuit.id}
                        onClick={() => setSelectedCircuit(circuit)}
                        className={`w-full text-left px-2 py-1 text-xs rounded transition-colors cursor-pointer ${
                          selectedCircuit?.id === circuit.id ? 'bg-primary-600/20 text-primary-500' : 'text-[var(--text-muted)] hover:bg-[var(--hover-bg)]'
                        }`}
                      >
                        <span className="flex items-center gap-1.5">
                          {/* Indicador de color según el estado del circuito (constantes globales) */}
                          <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: CIRCUIT_STATUS_COLORS[circuit.status] }} />
                          <span className="truncate">{circuit.name}</span>
                        </span>
                      </button>
                    ))}
                    {barCircuits[bar.id].length === 0 && (
                      <p className="text-xs text-[var(--text-muted)] px-2 py-1 italic">Sin circuitos</p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Panel derecho: detalle de la barra o circuito seleccionado */}
      <div className="flex-1 min-w-0">
        {/* Si el circuito está en estado de reserva, muestra un mensaje de espera en lugar del detalle */}
        {selectedCircuit && (selectedCircuit.status === 'reserve_r' || selectedCircuit.status === 'reserve_equipped_re') ? (
          <Card>
            <div className="text-center py-12">
              <Badge color="yellow">{CIRCUIT_STATUS_LABELS[selectedCircuit.status]}</Badge>
              <p className="text-[var(--text-muted)] mt-4">Pendiente a cambio de estado</p>
            </div>
          </Card>
        ) : selectedBar ? (
          <div className="space-y-4">
            {/* Encabezado con nombre de estación/barra/circuito, estado y botones de acción */}
            <div className="flex flex-wrap items-start gap-2 justify-between">
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                  {station.name} - {selectedCircuit ? `${selectedCircuit.denomination} / ${selectedCircuit.name}` : selectedBar.name}
                </h3>
                <Badge color={selectedBar.status === 'operative' ? 'green' : 'gray'}>
                  {selectedBar.status === 'operative' ? 'Operativo' : 'Inactivo'}
                </Badge>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {isAdmin && canViewCircuits && selectedCircuit && (
                  <Button variant="secondary" size="sm" onClick={() => setShowSubCircuitForm(true)}>
                    <Plus size={14} className="mr-1" /> Agregar Sub-circuito
                  </Button>
                )}
                {/* Botón para entrar al modo edición (solo admin) */}
                {isAdmin && !isEditMode && (
                  <Button variant="secondary" size="sm" onClick={() => setIsEditMode(true)}>Modo Edicion</Button>
                )}
                {/* En modo edición se habilitan Cambiar Estado y Salir Edicion */}
                {isEditMode && (
                  <>
                    <Button variant="secondary" size="sm" onClick={() => setShowStatusChange(true)}>Cambiar Estado</Button>
                    <Button variant="ghost" size="sm" onClick={() => setIsEditMode(false)}>Salir Edicion</Button>
                  </>
                )}
                {isAdmin && (
                  <button
                    onClick={openCapacityForm}
                    title="Editar capacidad del tablero"
                    className="p-1.5 rounded hover:bg-[var(--hover-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                  >
                    <Pencil size={15} />
                  </button>
                )}
                <Button variant="ghost" size="sm" onClick={() => setShowObservations(true)}>Observaciones</Button>
              </div>
            </div>

            {/* Tarjetas de resumen de potencia (PI, MD, capacidad disponible).
                Los totales PI y MD siempre se calculan a partir de los datos visibles
                en la tabla, para que coincidan exactamente con la suma de las columnas:
                - Vista de barra: suma de PI/MD de los circuitos de esa barra.
                - Vista de circuito: suma de PI/MD de los sub-circuitos de ese circuito.
                La capacidad del tablero y la potencia disponible usan la capacidad
                configurada en la barra. */}
            {powerSummary && (() => {
              const circuits = barCircuits[selectedBar!.id] || [];
              // Las barras de emergencia y continuidad aplican factor 0.75 sobre la MD total
              const mdFactor = (selectedBar!.bar_type === 'emergency' || selectedBar!.bar_type === 'continuity') ? 0.75 : 1;
              const circuitPI = circuits.reduce((sum, c) => sum + Number(c.pi_kw), 0);
              const circuitMD = circuits.reduce((sum, c) => sum + Number(c.md_kw), 0) * mdFactor;
              const subPI = subCircuits.reduce((sum, s) => sum + Number(s.pi_kw), 0);
              const subMD = subCircuits.reduce((sum, s) => sum + Number(s.md_kw), 0) * mdFactor;
              const cap = powerSummary.max_board_capacity_kw;
              return (
                <PowerCards summary={
                  selectedCircuit
                    ? { total_installed_power_kw: subPI, total_max_demand_kw: subMD, max_board_capacity_kw: cap, max_board_capacity_a: powerSummary.max_board_capacity_a, available_power_kw: cap - subMD }
                    : { total_installed_power_kw: circuitPI, total_max_demand_kw: circuitMD, max_board_capacity_kw: cap, max_board_capacity_a: powerSummary.max_board_capacity_a, available_power_kw: cap - circuitMD }
                } />
              );
            })()}

            {canViewCircuits && (
              // Si hay un circuito seleccionado muestra sus sub-circuitos; si no, muestra los circuitos de la barra
              selectedCircuit ? (
                <SubCircuitTable
                  subCircuits={subCircuits}
                  isEditMode={isEditMode}
                  onDelete={refreshAfterSubCircuitChange}
                />
              ) : (
                <CircuitTable
                  circuits={barCircuits[selectedBar.id] || []}
                  isEditMode={isEditMode}
                  onDelete={handleCircuitDeleted}
                  onView={(circuit) => setSelectedCircuit(circuit)}
                  onNavigateToBar={(bar) => { handleBarSelect(bar); if (!expandedBars.has(bar.id)) toggleBar(bar.id); }}
                  bars={bars}
                  barName={selectedBar.name}
                />
              )
            )}
          </div>
        ) : (
          <Card>
            <p className="text-center text-[var(--text-muted)] py-12">Seleccione un tablero o circuito del panel izquierdo</p>
          </Card>
        )}
      </div>

      {/* Modales — se montan solo cuando su bandera de visibilidad es true */}

      {/* Modal de creación de circuito: recibe el ID de la barra para la que se crea */}
      {showCircuitForm && formBarId && (
        <CircuitForm barId={formBarId} bars={bars} onClose={() => setShowCircuitForm(false)} onCreated={handleCircuitCreated} />
      )}
      {/* Modal de creación de sub-circuito: requiere un circuito seleccionado */}
      {showSubCircuitForm && selectedCircuit && (
        <SubCircuitForm circuitId={selectedCircuit.id} onClose={() => setShowSubCircuitForm(false)} onCreated={() => { setShowSubCircuitForm(false); refreshAfterSubCircuitChange(); }} />
      )}
      {/* Modal de observaciones: puede recibir barId, circuitId o ambos según el contexto */}
      {showObservations && (selectedBar || selectedCircuit) && (
        <ObservationsModal barId={selectedBar?.id} circuitId={selectedCircuit?.id} onClose={() => setShowObservations(false)} />
      )}
      {/* Modal de cambio de estado: opera en modo "circuits" (sobre la barra) o "sub-circuits" (sobre el circuito) */}
      {showStatusChange && selectedBar && (
        selectedCircuit ? (
          <StatusChangeModal
            mode="sub-circuits"
            circuitId={selectedCircuit.id}
            subCircuits={subCircuits}
            onClose={() => setShowStatusChange(false)}
            onSaved={() => { setShowStatusChange(false); refreshAfterSubCircuitChange(); }}
          />
        ) : (
          <StatusChangeModal
            mode="circuits"
            barId={selectedBar.id}
            circuits={barCircuits[selectedBar.id] || []}
            onClose={() => setShowStatusChange(false)}
            onSaved={() => { setShowStatusChange(false); if (selectedBar) loadBarCircuits(selectedBar.id); onStationChanged?.(); }}
          />
        )
      )}
      {/* Modal de edición de capacidad del tablero */}
      {showCapacityForm && selectedBar && (
        <Modal isOpen onClose={() => setShowCapacityForm(false)} title={`Capacidad — ${selectedBar.name}`} size="sm">
          <div className="space-y-4">
            <Input
              label="Capacidad (kW)"
              type="number"
              step="0.01"
              min="0"
              value={capacityKw}
              onChange={(e) => setCapacityKw(e.target.value)}
            />
            <Input
              label="Capacidad (A)"
              type="number"
              step="0.01"
              min="0"
              value={capacityA}
              onChange={(e) => setCapacityA(e.target.value)}
            />
            {capacityError && <p className="text-sm text-red-500">{capacityError}</p>}
            <div className="flex gap-2 justify-end">
              <Button variant="secondary" onClick={() => setShowCapacityForm(false)}>Cancelar</Button>
              <Button onClick={handleSaveCapacity}>Guardar</Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
