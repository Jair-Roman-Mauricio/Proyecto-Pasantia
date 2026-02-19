import { useState, useEffect } from 'react';
import * as XLSX from 'xlsx';
import type { Circuit, SubCircuit } from '../../types';
import { circuitService } from '../../services/circuitService';
import Modal from '../ui/Modal';
import Table from '../ui/Table';
import Button from '../ui/Button';
import Spinner from '../ui/Spinner';

interface DeleteCircuitModalProps {
  circuit: Circuit | null;
  barName: string;
  onCancel: () => void;
  onConfirm: () => void;
}

export default function DeleteCircuitModal({ circuit, barName, onCancel, onConfirm }: DeleteCircuitModalProps) {
  const [subCircuits, setSubCircuits] = useState<SubCircuit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (circuit) {
      setIsLoading(true);
      circuitService.getSubCircuits(circuit.id)
        .then(setSubCircuits)
        .catch(() => setSubCircuits([]))
        .finally(() => setIsLoading(false));
    }
  }, [circuit]);

  if (!circuit) return null;

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await circuitService.delete(circuit.id);
      onConfirm();
    } catch (error) {
      console.error('Error deleting circuit:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDownloadExcel = () => {
    const data = subCircuits.map((s) => ({
      'Circuito': s.name,
      'Descripcion': s.description || '',
      'ITM': s.itm || '',
      'MM2': s.mm2 || '',
      'PI (kW)': Number(s.pi_kw).toFixed(2),
      'F.D': Number(s.fd).toFixed(4),
      'MD (kW)': Number(s.md_kw).toFixed(2),
    }));

    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Sub-circuitos');
    XLSX.writeFile(wb, `${circuit.name}_sub-circuitos.xlsx`);
  };

  const columns = [
    { key: 'name', header: 'Circuito', render: (s: SubCircuit) => <span className="font-medium">{s.name}</span> },
    { key: 'description', header: 'Descripcion' },
    { key: 'itm', header: 'ITM' },
    { key: 'mm2', header: 'MM2' },
    { key: 'pi_kw', header: 'PI (kW)', render: (s: SubCircuit) => Number(s.pi_kw).toFixed(2) },
    { key: 'fd', header: 'F.D', render: (s: SubCircuit) => Number(s.fd).toFixed(4) },
    { key: 'md_kw', header: 'MD (kW)', render: (s: SubCircuit) => Number(s.md_kw).toFixed(2) },
  ];

  if (isLoading) {
    return (
      <Modal isOpen onClose={onCancel} title="Eliminar Circuito" size="sm">
        <div className="flex justify-center py-8">
          <Spinner size="lg" />
        </div>
      </Modal>
    );
  }

  if (subCircuits.length === 0) {
    return (
      <Modal isOpen onClose={onCancel} title="Eliminar Circuito" size="sm">
        <div className="space-y-4">
          <p className="text-[var(--text-secondary)]">
            ¿Eliminar circuito <strong>"{circuit.name}"</strong> de la barra <strong>"{barName}"</strong>?
          </p>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={onCancel}>Cancelar</Button>
            <Button variant="danger" onClick={handleDelete} disabled={isDeleting}>
              {isDeleting ? 'Eliminando...' : 'Eliminar'}
            </Button>
          </div>
        </div>
      </Modal>
    );
  }

  return (
    <Modal isOpen onClose={onCancel} title="Confirmar Eliminacion de Circuito" size="lg">
      <div className="space-y-4">
        <div className="text-[var(--text-secondary)]">
          <p>
            Circuito: <strong className="text-[var(--text-primary)]">{circuit.name}</strong>
          </p>
          <p>
            Barra: <strong className="text-[var(--text-primary)]">{barName}</strong>
          </p>
        </div>

        <div>
          <p className="text-sm text-[var(--text-muted)] mb-2">
            Este circuito contiene {subCircuits.length} sub-circuito{subCircuits.length > 1 ? 's' : ''} que tambien seran eliminados:
          </p>
          <div className="max-h-64 overflow-y-auto">
            <Table
              columns={columns}
              data={subCircuits}
              rowKey={(s) => s.id}
            />
          </div>
        </div>

        <div className="flex gap-2 justify-end">
          <Button variant="secondary" onClick={onCancel}>Cancelar</Button>
          <Button variant="secondary" onClick={handleDownloadExcel}>Descargar Excel</Button>
          <Button variant="danger" onClick={handleDelete} disabled={isDeleting}>
            {isDeleting ? 'Eliminando...' : 'Estoy seguro de eliminar'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
