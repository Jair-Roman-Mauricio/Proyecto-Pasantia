import { useState } from 'react';
import { Upload, Camera } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { Station } from '../../types';
import { useAuth } from '../../context/AuthContext';
import { IMAGE_JUSTIFICATION_REASONS } from '../../config/constants';
import api from '../../config/api';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Modal from '../ui/Modal';

interface SummaryTabProps {
  station: Station;
}

export default function SummaryTab({ station }: SummaryTabProps) {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [showUpload, setShowUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [justification, setJustification] = useState('');
  const [imageKey, setImageKey] = useState(0);
  const [hasImage, setHasImage] = useState(true);

  const consumed = Number(station.max_demand_kw);
  const available = Math.max(0, Number(station.available_power_kw));

  const chartData = [
    { name: 'Potencia Consumida', value: consumed },
    { name: 'Potencia Disponible', value: available },
  ];
  const colors = ['#ef4444', '#22c55e'];

  const handleUpload = async () => {
    if (!selectedFile || !justification) return;
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('justification', justification);
    try {
      await api.post(`/images/transformer/${station.id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setShowUpload(false);
      setSelectedFile(null);
      setJustification('');
      setHasImage(true);
      setImageKey((k) => k + 1);
    } catch (error) {
      console.error('Error uploading image:', error);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-[var(--text-secondary)]">
            Foto del Transformador
          </h3>
          {isAdmin && (
            <Button variant="secondary" size="sm" onClick={() => setShowUpload(true)}>
              <Upload size={14} className="mr-1" />
              {hasImage ? 'Cambiar Foto' : 'Subir Foto'}
            </Button>
          )}
        </div>

        <div className="aspect-video bg-[var(--bg-secondary)] rounded-lg flex items-center justify-center overflow-hidden">
          {hasImage ? (
            <img
              key={imageKey}
              src={`/api/v1/images/transformer/${station.id}?v=${imageKey}`}
              alt={`Transformador - ${station.name}`}
              className="max-h-full max-w-full object-contain rounded-lg"
              onError={() => setHasImage(false)}
            />
          ) : (
            <div
              className={`flex flex-col items-center gap-3 text-[var(--text-muted)] ${isAdmin ? 'cursor-pointer hover:text-[var(--text-secondary)]' : ''}`}
              onClick={isAdmin ? () => setShowUpload(true) : undefined}
            >
              <Camera size={40} strokeWidth={1.5} />
              <p className="text-sm">No hay imagen disponible</p>
              {isAdmin && (
                <p className="text-xs text-primary-500">Click para subir una foto</p>
              )}
            </div>
          )}
        </div>
      </Card>

      <Card>
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-4">
          Potencia Disponible vs Consumida
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
                label={({ value }) => `${value} kW`}
              >
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `${value} kW`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Upload Modal */}
      <Modal isOpen={showUpload} onClose={() => setShowUpload(false)} title="Foto del Transformador" size="md">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
              Seleccionar imagen
            </label>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-[var(--text-primary)]"
            />
            {selectedFile && (
              <p className="text-xs text-[var(--text-muted)] mt-1">
                {selectedFile.name} ({(selectedFile.size / 1024).toFixed(0)} KB)
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
              Justificacion del cambio
            </label>
            <select
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]"
            >
              <option value="">Seleccione una razon</option>
              {IMAGE_JUSTIFICATION_REASONS.map((reason) => (
                <option key={reason} value={reason}>{reason}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setShowUpload(false)}>Cancelar</Button>
            <Button onClick={handleUpload} disabled={!selectedFile || !justification}>
              Subir Imagen
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
