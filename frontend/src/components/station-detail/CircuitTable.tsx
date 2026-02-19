import { Trash2, Eye } from 'lucide-react';
import type { Circuit } from '../../types';
import { CIRCUIT_STATUS_COLORS } from '../../config/constants';
import { circuitService } from '../../services/circuitService';
import Table from '../ui/Table';
import Button from '../ui/Button';

interface CircuitTableProps {
  circuits: Circuit[];
  isEditMode: boolean;
  onDelete: () => void;
  showDenomination?: boolean;
}

export default function CircuitTable({ circuits, isEditMode, onDelete, showDenomination = true }: CircuitTableProps) {
  const handleDelete = async (circuit: Circuit) => {
    if (!confirm(`Eliminar circuito "${circuit.name}"?`)) return;
    await circuitService.delete(circuit.id);
    onDelete();
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
            <Button variant="danger" size="sm" onClick={() => handleDelete(c)}>
              <Trash2 size={14} />
            </Button>
          ),
        }]
      : [{
          key: 'actions',
          header: 'Acciones',
          render: (_c: Circuit) => (
            <Button variant="ghost" size="sm">
              <Eye size={14} className="mr-1" /> Ver
            </Button>
          ),
        }]),
  ];

  return (
    <Table
      columns={columns}
      data={circuits}
      rowKey={(c) => c.id}
      rowClassName={(c) => {
        if (c.status === 'reserve_r') return 'bg-yellow-50 dark:bg-yellow-900/10';
        if (c.status === 'reserve_equipped_re') return 'bg-blue-50 dark:bg-blue-900/10';
        return '';
      }}
    />
  );
}
