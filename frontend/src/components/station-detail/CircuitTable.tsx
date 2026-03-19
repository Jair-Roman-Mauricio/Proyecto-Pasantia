/**
 * Tabla de circuitos de una barra de distribución.
 * En modo edición muestra el botón de eliminación; en modo lectura muestra el botón "Ver".
 * Los circuitos UPS muestran un modal de selección de barra destino antes de navegar.
 */
import { useState } from 'react';
import { Trash2, Eye, Pencil } from 'lucide-react';
import type { Circuit, Bar } from '../../types';
import Table from '../ui/Table';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import DeleteCircuitModal from './DeleteCircuitModal';
import CircuitForm from './CircuitForm';

/** Props de la tabla de circuitos */
interface CircuitTableProps {
  /** Lista de circuitos a mostrar */
  circuits: Circuit[];
  /** Cuando es true, reemplaza la columna de acciones por botones de eliminación */
  isEditMode: boolean;
  /** Callback invocado tras eliminar un circuito para refrescar el estado padre */
  onDelete: () => void;
  /** Callback para seleccionar un circuito y mostrar sus sub-circuitos */
  onView: (circuit: Circuit) => void;
  /** Callback para navegar a la barra secundaria/terciaria de un circuito UPS */
  onNavigateToBar: (bar: Bar) => void;
  /** Lista completa de barras de la estación (necesaria para resolver nombres UPS) */
  bars: Bar[];
  /** Nombre de la barra mostrado en el modal de confirmación de eliminación */
  barName?: string;
  /** Si es false, omite la columna de denominación (útil cuando se muestra en contexto de barra ya conocida) */
  showDenomination?: boolean;
}

export default function CircuitTable({ circuits, isEditMode, onDelete, onView, onNavigateToBar, bars, barName = '', showDenomination = true }: CircuitTableProps) {
  const [circuitToDelete, setCircuitToDelete] = useState<Circuit | null>(null);
  // Almacena el circuito UPS sobre el que se está eligiendo la barra de destino
  const [upsCircuit, setUpsCircuit] = useState<Circuit | null>(null);
  // Circuito seleccionado para editar; al asignarlo abre CircuitForm en modo edición
  const [editingCircuit, setEditingCircuit] = useState<Circuit | null>(null);

  /** Busca el nombre legible de una barra por su ID; retorna cadena vacía si no se encuentra */
  const getBarName = (barId: number | null) => {
    if (!barId) return '';
    return bars.find((b) => b.id === barId)?.name || '';
  };

  /**
   * Gestiona el clic en "Ver" de un circuito.
   * Si el circuito es UPS, abre el modal de selección de barra; si no, navega directamente.
   */
  const handleView = (c: Circuit) => {
    if (c.is_ups) {
      setUpsCircuit(c);
    } else {
      onView(c);
    }
  };

  /**
   * Resuelve la elección de barra en el modal UPS y navega a la barra seleccionada.
   * Recibe el ID de la barra secundaria o terciaria según la selección del usuario.
   */
  const handleUpsChoice = (barId: number | null) => {
    if (!barId) return;
    const bar = bars.find((b) => b.id === barId);
    if (bar) {
      setUpsCircuit(null);
      onNavigateToBar(bar);
    }
  };

  // Columnas dinámicas según showDenomination e isEditMode
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
    { key: 'description', header: 'Descripcion', className: 'hidden md:table-cell' },
    { key: 'pi_kw', header: 'PI (kW)', render: (c: Circuit) => Number(c.pi_kw).toFixed(2), className: 'hidden lg:table-cell' },
    { key: 'fd', header: 'F.D', render: (c: Circuit) => Number(c.fd).toFixed(4), className: 'hidden lg:table-cell' },
    { key: 'md_kw', header: 'MD (kW)', render: (c: Circuit) => Number(c.md_kw).toFixed(2) },
    ...(isEditMode
      ? [{
          key: 'actions',
          header: 'Acciones',
          render: (c: Circuit) => (
            <div className="flex gap-1">
              {/* Botón editar: abre CircuitForm pre-llenado con los datos del circuito */}
              <Button variant="ghost" size="sm" onClick={() => setEditingCircuit(c)} title="Editar circuito">
                <Pencil size={14} />
              </Button>
              <Button variant="danger" size="sm" onClick={() => setCircuitToDelete(c)} title="Eliminar circuito">
                <Trash2 size={14} />
              </Button>
            </div>
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
          // Colorea la fila según el estado de reserva para identificación visual rápida
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
      {/* Modal de edición: se abre al hacer clic en el botón lápiz de una fila en modo edición */}
      {editingCircuit && (
        <CircuitForm
          barId={editingCircuit.bar_id}
          bars={bars}
          editingCircuit={editingCircuit}
          onClose={() => setEditingCircuit(null)}
          onCreated={() => { setEditingCircuit(null); onDelete(); }}
        />
      )}
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
