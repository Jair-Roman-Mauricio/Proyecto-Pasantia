import { useState } from 'react';
import { circuitService } from '../../services/circuitService';
import Modal from '../ui/Modal';
import Input from '../ui/Input';
import Button from '../ui/Button';

interface SubCircuitFormProps {
  circuitId: number;
  onClose: () => void;
  onCreated: () => void;
}

export default function SubCircuitForm({ circuitId, onClose, onCreated }: SubCircuitFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [itm, setItm] = useState('');
  const [mm2, setMm2] = useState('');
  const [piKw, setPiKw] = useState('');
  const [fd, setFd] = useState('1.0');
  const [mdKw, setMdKw] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const piNum = parseFloat(piKw) || 0;
  const fdNum = parseFloat(fd) || 1;
  const calculatedMd = (piNum * fdNum).toFixed(2);

  const handlePiChange = (val: string) => {
    setPiKw(val);
    const pi = parseFloat(val) || 0;
    setMdKw((pi * fdNum).toFixed(2));
  };

  const handleFdChange = (val: string) => {
    setFd(val);
    const f = parseFloat(val) || 1;
    setMdKw((piNum * f).toFixed(2));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !piKw) return;
    setIsSubmitting(true);
    try {
      await circuitService.createSubCircuit(circuitId, {
        name,
        description: description || undefined,
        itm: itm || undefined,
        mm2: mm2 || undefined,
        pi_kw: parseFloat(piKw),
        fd: parseFloat(fd),
        md_kw: parseFloat(mdKw) || parseFloat(calculatedMd),
      });
      onCreated();
    } catch (error) {
      console.error('Error creating sub-circuit:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} title="Agregar Sub-circuito" size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Denominacion *"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Ej: Alumbrado zona A"
          required
        />
        <Input
          label="Descripcion"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Descripcion del sub-circuito"
        />
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="ITM"
            value={itm}
            onChange={(e) => setItm(e.target.value)}
            placeholder="Ej: 3x20A"
          />
          <Input
            label="MM2"
            value={mm2}
            onChange={(e) => setMm2(e.target.value)}
            placeholder="Ej: 3x4"
          />
        </div>
        <div className="grid grid-cols-3 gap-4">
          <Input
            label="PI (kW) *"
            type="number"
            step="0.01"
            value={piKw}
            onChange={(e) => handlePiChange(e.target.value)}
            placeholder="0.00"
            required
          />
          <Input
            label="F.D"
            type="number"
            step="0.0001"
            value={fd}
            onChange={(e) => handleFdChange(e.target.value)}
            placeholder="1.0"
          />
          <Input
            label="MD (kW)"
            type="number"
            step="0.01"
            value={mdKw || calculatedMd}
            onChange={(e) => setMdKw(e.target.value)}
            placeholder="Auto"
          />
        </div>
        <p className="text-xs text-[var(--text-muted)]">
          MD se calcula automaticamente como PI x F.D = {calculatedMd} kW
        </p>
        <div className="flex gap-2 justify-end">
          <Button variant="secondary" type="button" onClick={onClose}>Cancelar</Button>
          <Button type="submit" disabled={!name || !piKw || isSubmitting}>
            {isSubmitting ? 'Creando...' : 'Crear Sub-circuito'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
