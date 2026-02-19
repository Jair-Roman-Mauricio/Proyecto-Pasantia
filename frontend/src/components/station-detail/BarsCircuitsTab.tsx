import { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, Plus } from 'lucide-react';
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
}

export default function BarsCircuitsTab({ station }: BarsCircuitsTabProps) {
  const { user } = useAuth();
  const { viewMode } = useSidebar();
  const [bars, setBars] = useState<Bar[]>([]);
  const [expandedBars, setExpandedBars] = useState<Set<number>>(new Set());
  const [barCircuits, setBarCircuits] = useState<Record<number, Circuit[]>>({});
  const [selectedBar, setSelectedBar] = useState<Bar | null>(null);
  const [selectedCircuit, setSelectedCircuit] = useState<Circuit | null>(null);
  const [powerSummary, setPowerSummary] = useState<BarPowerSummary | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [showCircuitForm, setShowCircuitForm] = useState(false);
  const [showObservations, setShowObservations] = useState(false);
  const [showStatusChange, setShowStatusChange] = useState(false);
  const [subCircuits, setSubCircuits] = useState<SubCircuit[]>([]);
  const [showSubCircuitForm, setShowSubCircuitForm] = useState(false);
  const [formBarId, setFormBarId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAdmin = user?.role === 'admin' && viewMode === 'admin';

  useEffect(() => {
    stationService.getBars(station.id).then((data) => {
      setBars(data);
      if (data.length > 0) {
        setExpandedBars(new Set([data[0].id]));
        setSelectedBar(data[0]);
      }
    }).catch(console.error).finally(() => setIsLoading(false));
  }, [station.id]);

  useEffect(() => {
    if (selectedBar) {
      circuitService.getByBar(selectedBar.id).then((circuits) => {
        setBarCircuits((prev) => ({ ...prev, [selectedBar.id]: circuits }));
      });
      circuitService.getBarPowerSummary(selectedBar.id).then(setPowerSummary);
    }
  }, [selectedBar]);

  useEffect(() => {
    if (selectedCircuit) {
      circuitService.getSubCircuits(selectedCircuit.id).then(setSubCircuits).catch(() => setSubCircuits([]));
    } else {
      setSubCircuits([]);
    }
  }, [selectedCircuit]);

  const loadSubCircuits = () => {
    if (selectedCircuit) {
      circuitService.getSubCircuits(selectedCircuit.id).then(setSubCircuits);
    }
  };

  const toggleBar = (barId: number) => {
    setExpandedBars((prev) => {
      const next = new Set(prev);
      if (next.has(barId)) next.delete(barId); else next.add(barId);
      return next;
    });
  };

  const loadBarCircuits = (barId: number) => {
    circuitService.getByBar(barId).then((circuits) => {
      setBarCircuits((prev) => ({ ...prev, [barId]: circuits }));
    });
  };

  const handleBarSelect = (bar: Bar) => {
    setSelectedBar(bar);
    setSelectedCircuit(null);
    setIsEditMode(false);
  };

  const handleCircuitCreated = () => {
    setShowCircuitForm(false);
    if (formBarId) loadBarCircuits(formBarId);
    if (selectedBar) circuitService.getBarPowerSummary(selectedBar.id).then(setPowerSummary);
  };

  const handleCircuitDeleted = () => {
    if (selectedBar) {
      loadBarCircuits(selectedBar.id);
      circuitService.getBarPowerSummary(selectedBar.id).then(setPowerSummary);
    }
  };

  if (isLoading) return <div className="flex justify-center py-12"><Spinner size="lg" /></div>;

  return (
    <div className="flex gap-4">
      {/* Left panel - Tree */}
      <div className="w-64 shrink-0">
        <Card className="sticky top-0">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Tableros</h3>
          <div className="space-y-1">
            {bars.map((bar) => (
              <div key={bar.id}>
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
                  {isAdmin && (
                    <button onClick={() => { setFormBarId(bar.id); setShowCircuitForm(true); }} className="p-1 rounded hover:bg-[var(--hover-bg)] text-[var(--text-muted)] cursor-pointer" title="Agregar circuito">
                      <Plus size={14} />
                    </button>
                  )}
                </div>
                {expandedBars.has(bar.id) && barCircuits[bar.id] && (
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

      {/* Right panel */}
      <div className="flex-1 min-w-0">
        {selectedCircuit && (selectedCircuit.status === 'reserve_r' || selectedCircuit.status === 'reserve_equipped_re') ? (
          <Card>
            <div className="text-center py-12">
              <Badge color="yellow">{CIRCUIT_STATUS_LABELS[selectedCircuit.status]}</Badge>
              <p className="text-[var(--text-muted)] mt-4">Pendiente a cambio de estado</p>
            </div>
          </Card>
        ) : selectedBar ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                  {station.name} - {selectedCircuit ? `${selectedCircuit.denomination} / ${selectedCircuit.name}` : selectedBar.name}
                </h3>
                <Badge color={selectedBar.status === 'operative' ? 'green' : 'gray'}>
                  {selectedBar.status === 'operative' ? 'Operativo' : 'Inactivo'}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                {isAdmin && selectedCircuit && (
                  <Button variant="secondary" size="sm" onClick={() => setShowSubCircuitForm(true)}>
                    <Plus size={14} className="mr-1" /> Agregar Sub-circuito
                  </Button>
                )}
                {isAdmin && !isEditMode && (
                  <Button variant="secondary" size="sm" onClick={() => setIsEditMode(true)}>Modo Edicion</Button>
                )}
                {isEditMode && (
                  <>
                    <Button variant="secondary" size="sm" onClick={() => setShowStatusChange(true)}>Cambiar Estado</Button>
                    <Button variant="ghost" size="sm" onClick={() => setIsEditMode(false)}>Salir Edicion</Button>
                  </>
                )}
                <Button variant="ghost" size="sm" onClick={() => setShowObservations(true)}>Observaciones</Button>
              </div>
            </div>

            {powerSummary && <PowerCards summary={powerSummary} />}

            {selectedCircuit ? (
              <SubCircuitTable
                subCircuits={subCircuits}
                isEditMode={isEditMode}
                onDelete={loadSubCircuits}
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
            )}
          </div>
        ) : (
          <Card>
            <p className="text-center text-[var(--text-muted)] py-12">Seleccione un tablero o circuito del panel izquierdo</p>
          </Card>
        )}
      </div>

      {/* Modals */}
      {showCircuitForm && formBarId && (
        <CircuitForm barId={formBarId} bars={bars} onClose={() => setShowCircuitForm(false)} onCreated={handleCircuitCreated} />
      )}
      {showSubCircuitForm && selectedCircuit && (
        <SubCircuitForm circuitId={selectedCircuit.id} onClose={() => setShowSubCircuitForm(false)} onCreated={() => { setShowSubCircuitForm(false); loadSubCircuits(); }} />
      )}
      {showObservations && (selectedBar || selectedCircuit) && (
        <ObservationsModal barId={selectedBar?.id} circuitId={selectedCircuit?.id} onClose={() => setShowObservations(false)} />
      )}
      {showStatusChange && selectedBar && (
        <StatusChangeModal barId={selectedBar.id} circuits={barCircuits[selectedBar.id] || []} onClose={() => setShowStatusChange(false)} onSaved={() => { setShowStatusChange(false); if (selectedBar) loadBarCircuits(selectedBar.id); }} />
      )}
    </div>
  );
}
