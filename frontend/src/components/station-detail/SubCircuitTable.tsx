/**
 * Tabla de sub-circuitos de un circuito padre.
 * Muestra estado con indicador de color, datos eléctricos (ITM, MM2, PI, FD, MD)
 * y, en modo edición, botones de edición (✏️) y eliminación (🗑).
 */
import { useState } from 'react';
import { Trash2, Pencil } from 'lucide-react';
import type { SubCircuit } from '../../types';
import { CIRCUIT_STATUS_COLORS, CIRCUIT_STATUS_LABELS } from '../../config/constants';
import { circuitService } from '../../services/circuitService';
import Table from '../ui/Table';
import Button from '../ui/Button';
import SubCircuitForm from './SubCircuitForm';

/** Props de la tabla de sub-circuitos */
interface SubCircuitTableProps {
  /** Lista de sub-circuitos a mostrar */
  subCircuits: SubCircuit[];
  /** Cuando es true, añade la columna de eliminación a la tabla */
  isEditMode: boolean;
  /** Callback invocado tras eliminar un sub-circuito para refrescar el estado padre */
  onDelete: () => void;
}

export default function SubCircuitTable({ subCircuits, isEditMode, onDelete }: SubCircuitTableProps) {
  // Sub-circuito seleccionado para editar; al asignarlo abre SubCircuitForm en modo edición
  const [editingSubCircuit, setEditingSubCircuit] = useState<SubCircuit | null>(null);

  /**
   * Solicita confirmación nativa del navegador y elimina el sub-circuito.
   * Tras la eliminación exitosa invoca onDelete para refrescar la vista padre.
   */
  const handleDelete = async (sub: SubCircuit) => {
    if (!confirm(`Eliminar sub-circuito "${sub.name}"?`)) return;
    await circuitService.deleteSubCircuit(sub.id);
    onDelete();
  };

  const columns = [
    {
      key: 'status',
      header: 'Estado',
      render: (s: SubCircuit) => (
        <span className="flex items-center gap-1.5">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: CIRCUIT_STATUS_COLORS[s.status] || '#6b7280' }}
          />
          <span className="text-xs">{CIRCUIT_STATUS_LABELS[s.status] || s.status}</span>
        </span>
      ),
    },
    {
      key: 'name',
      header: 'Circuito',
      render: (s: SubCircuit) => <span className="font-medium">{s.name}</span>,
    },
    { key: 'description', header: 'Descripcion', className: 'hidden md:table-cell' },
    { key: 'itm', header: 'ITM', className: 'hidden sm:table-cell' },
    { key: 'mm2', header: 'MM2', className: 'hidden sm:table-cell' },
    { key: 'pi_kw', header: 'PI (kW)', render: (s: SubCircuit) => Number(s.pi_kw).toFixed(2), className: 'hidden lg:table-cell' },
    { key: 'fd', header: 'F.D', render: (s: SubCircuit) => Number(s.fd).toFixed(4), className: 'hidden lg:table-cell' },
    { key: 'md_kw', header: 'MD (kW)', render: (s: SubCircuit) => Number(s.md_kw).toFixed(2) },
    ...(isEditMode
      ? [{
          key: 'actions',
          header: 'Acciones',
          render: (s: SubCircuit) => (
            <div className="flex gap-1">
              {/* Botón editar: abre SubCircuitForm pre-llenado con los datos del sub-circuito */}
              <Button variant="ghost" size="sm" onClick={() => setEditingSubCircuit(s)} title="Editar sub-circuito">
                <Pencil size={14} />
              </Button>
              <Button variant="danger" size="sm" onClick={() => handleDelete(s)} title="Eliminar sub-circuito">
                <Trash2 size={14} />
              </Button>
            </div>
          ),
        }]
      : []),
  ];

  return (
    <>
      <Table
        columns={columns}
        data={subCircuits}
        rowKey={(s) => s.id}
      />
      {/* Modal de edición: se abre al hacer clic en el botón lápiz de una fila en modo edición */}
      {editingSubCircuit && (
        <SubCircuitForm
          circuitId={editingSubCircuit.circuit_id}
          editingSubCircuit={editingSubCircuit}
          onClose={() => setEditingSubCircuit(null)}
          onCreated={() => { setEditingSubCircuit(null); onDelete(); }}
        />
      )}
    </>
  );
}
