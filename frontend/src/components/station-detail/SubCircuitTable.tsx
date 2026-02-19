import { Trash2 } from 'lucide-react';
import type { SubCircuit } from '../../types';
import { circuitService } from '../../services/circuitService';
import Table from '../ui/Table';
import Button from '../ui/Button';

interface SubCircuitTableProps {
  subCircuits: SubCircuit[];
  isEditMode: boolean;
  onDelete: () => void;
}

export default function SubCircuitTable({ subCircuits, isEditMode, onDelete }: SubCircuitTableProps) {
  const handleDelete = async (sub: SubCircuit) => {
    if (!confirm(`Eliminar sub-circuito "${sub.name}"?`)) return;
    await circuitService.deleteSubCircuit(sub.id);
    onDelete();
  };

  const columns = [
    {
      key: 'name',
      header: 'Circuito',
      render: (s: SubCircuit) => <span className="font-medium">{s.name}</span>,
    },
    { key: 'description', header: 'Descripcion' },
    { key: 'itm', header: 'ITM' },
    { key: 'mm2', header: 'MM2' },
    { key: 'pi_kw', header: 'PI (kW)', render: (s: SubCircuit) => Number(s.pi_kw).toFixed(2) },
    { key: 'fd', header: 'F.D', render: (s: SubCircuit) => Number(s.fd).toFixed(4) },
    { key: 'md_kw', header: 'MD (kW)', render: (s: SubCircuit) => Number(s.md_kw).toFixed(2) },
    ...(isEditMode
      ? [{
          key: 'actions',
          header: 'Acciones',
          render: (s: SubCircuit) => (
            <Button variant="danger" size="sm" onClick={() => handleDelete(s)}>
              <Trash2 size={14} />
            </Button>
          ),
        }]
      : []),
  ];

  return (
    <Table
      columns={columns}
      data={subCircuits}
      rowKey={(s) => s.id}
    />
  );
}
