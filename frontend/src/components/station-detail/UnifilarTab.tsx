/**
 * Pestaña del mapa unifilar de una estación.
 * Muestra la imagen del diagrama unifilar cargada en el servidor (si existe).
 * Los administradores pueden subir o reemplazar la imagen con una justificación registrada.
 */
import { useState, useEffect, useRef } from 'react';
import { Upload } from 'lucide-react';
import type { Station } from '../../types';
import { useAuth } from '../../context/AuthContext';
import { IMAGE_JUSTIFICATION_REASONS } from '../../config/constants';
import api from '../../config/api';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Modal from '../ui/Modal';

/** Props de la pestaña del mapa unifilar */
interface UnifilarTabProps {
  /** Estación cuyo diagrama unifilar se visualiza y gestiona */
  station: Station;
}

export default function UnifilarTab({ station }: UnifilarTabProps) {
  const { user } = useAuth();
  const [showUpload, setShowUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [justification, setJustification] = useState('');
  // Incrementar imageKey fuerza un re-fetch de la imagen tras reemplazarla
  const [imageKey, setImageKey] = useState(0);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  // Guarda la URL blob anterior para revocarla al recibir la nueva y liberar memoria
  const prevBlobUrl = useRef<string | null>(null);
  const isAdmin = user?.role === 'admin';

  // Obtiene la imagen del mapa unifilar como blob (evita CORS y problemas de caché)
  useEffect(() => {
    let cancelled = false;
    api.get(`/images/unifilar/${station.id}`, { responseType: 'blob' })
      .then((res) => {
        if (cancelled) return;
        // 204 = sin imagen subida; no se intenta crear un blob URL vacío
        if (res.status === 204) { setBlobUrl(null); return; }
        const url = URL.createObjectURL(res.data);
        if (prevBlobUrl.current) URL.revokeObjectURL(prevBlobUrl.current);
        prevBlobUrl.current = url;
        setBlobUrl(url);
      })
      .catch(() => {
        if (!cancelled) setBlobUrl(null);
      });
    return () => { cancelled = true; };
  }, [station.id, imageKey]);

  /**
   * Envía la imagen del mapa unifilar al servidor con justificación de cambio.
   * Tras la subida exitosa incrementa imageKey para disparar la recarga de la imagen.
   */
  const handleUpload = async () => {
    if (!selectedFile || !justification) return;
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('justification', justification);
    try {
      await api.post(`/images/unifilar/${station.id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setShowUpload(false);
      setSelectedFile(null);
      setJustification('');
      setImageKey((k) => k + 1);
    } catch (error) {
      console.error('Error uploading image:', error);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">
          Estacion {station.name} - Mapa Unifilar
        </h3>
        {isAdmin && (
          <Button variant="secondary" size="sm" onClick={() => setShowUpload(true)}>
            <Upload size={16} className="mr-2" />
            Actualizar Mapa Unifilar
          </Button>
        )}
      </div>

      <Card>
        <div className="min-h-[400px] flex items-center justify-center">
          {blobUrl ? (
            <img
              src={blobUrl}
              alt={`Mapa unifilar - ${station.name}`}
              className="max-w-full max-h-[600px] object-contain"
            />
          ) : (
            <p className="text-[var(--text-muted)]">
              No hay mapa unifilar disponible para esta estacion
            </p>
          )}
        </div>
      </Card>

      <Modal isOpen={showUpload} onClose={() => setShowUpload(false)} title="Actualizar Mapa Unifilar" size="md">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Seleccionar imagen</label>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-[var(--text-primary)]"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Justificacion del cambio</label>
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
            <Button onClick={handleUpload} disabled={!selectedFile || !justification}>Subir Imagen</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
