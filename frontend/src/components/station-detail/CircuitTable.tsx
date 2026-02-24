import { useState } from 'react';
import { Trash2, Eye } from 'lucide-react';
import type { Circuit, Bar } from '../../types';
import { CIRCUIT_STATUS_COLORS } from '../../config/constants';
import Table from '../ui/Table';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import DeleteCircuitModal from './DeleteCircuitModal';

interface CircuitTableProps {
  circuits: Circuit[];
  isEditMode: boolean;
  onDelete: () => void;
  onView: (circuit: Circuit) => void;
  onNavigateToBar: (bar: Bar) => void;
  bars: Bar[];
  barName?: string;
  showDenomination?: boolean;
}

export default function CircuitTable({ circuits, isEditMode, onDelete, onView, onNavigateToBar, bars, barName = '', showDenomination = true }: CircuitTableProps) {
  const [circuitToDelete, setCircuitToDelete] = useState<Circuit | null>(null);
  const [upsCircuit, setUpsCircuit] = useState<Circuit | null>(null);

  const getBarName = (barId: number | null) => {
    if (!barId) return '';
    return bars.find((b) => b.id === barId)?.name || '';
  };

  const handleView = (c: Circuit) => {
    if (c.is_ups) {
      setUpsCircuit(c);
    } else {
      onView(c);
    }
  };

  const handleUpsChoice = (barId: number | null) => {
    if (!barId) return;
    const bar = bars.find((b) => b.id === barId);
    if (bar) {
      setUpsCircuit(null);
      onNavigateToBar(bar);
    }
  };

  const columns = [
    ...(showDenomination
      ? [{
          key: 'circuit',
          header: 'Circuito',
          render: (c: Circuit) => (
            <span className="font-medium">{c.name} / {c.denomination}</span>
          ),
        }]
      : [{
          key: 'name',
          header: 'Circuito',
          render: (c: Circuit) => <span className="font-medium">{c.name}</span>,
        }]),
    { key: 'description', header: 'Descripcion' },
    { key: 'local_item', header: 'Local/ITEM' },
    { key: 'pi_kw', header: 'PI (kW)', render: (c: Circuit) => Number(c.pi_kw).toFixed(2) },
    { key: 'fd', header: 'F.D', render: (c: Circuit) => Number(c.fd).toFixed(4) },
    { key: 'md_kw', header: 'MD (kW)', render: (c: Circuit) => Number(c.md_kw).toFixed(2) },
    ...(isEditMode
      ? [{
          key: 'actions',
          header: 'Acciones',
          render: (c: Circuit) => (
            <Button variant="danger" size="sm" onClick={() => setCircuitToDelete(c)}>
              <Trash2 size={14} />
            </Button>
          ),
        }]
      : [{
          key: 'actions',
          header: 'Acciones',
          render: (c: Circuit) => (
            <Button variant="ghost" size="sm" onClick={() => handleView(c)}>
              <Eye size={14} className="mr-1" /> Ver
            </Button>
          ),
        }]),
  ];

  return (
    <>
      <Table
        columns={columns}
        data={circuits}
        rowKey={(c) => c.id}
        rowClassName={(c) => {
          if (c.status === 'reserve_r') return 'bg-yellow-500/10';
          if (c.status === 'reserve_equipped_re') return 'bg-blue-500/10';
          return '';
        }}
      />
      <DeleteCircuitModal
        circuit={circuitToDelete}
        barName={barName}
        onCancel={() => setCircuitToDelete(null)}
        onConfirm={() => { setCircuitToDelete(null); onDelete(); }}
      />
      {upsCircuit && (
        <Modal isOpen onClose={() => setUpsCircuit(null)} title="Circuito UPS - Elegir conexion" size="sm">
          <div className="space-y-3">
            <p className="text-sm text-[var(--text-secondary)]">
              El circuito <strong>{upsCircuit.name}</strong> es UPS y esta conectado a dos barras. Seleccione a cual desea ir:
            </p>
            <div className="flex flex-col gap-2">
              <Button
                variant="secondary"
                onClick={() => handleUpsChoice(upsCircuit.secondary_bar_id)}
              >
                {getBarName(upsCircuit.secondary_bar_id)}
              </Button>
              <Button
                variant="secondary"
                onClick={() => handleUpsChoice(upsCircuit.tertiary_bar_id)}
              >
                {getBarName(upsCircuit.tertiary_bar_id)}
              </Button>
            </div>
            <div className="flex justify-end">
              <Button variant="ghost" size="sm" onClick={() => setUpsCircuit(null)}>Cancelar</Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
