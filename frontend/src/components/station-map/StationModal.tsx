import { useNavigate } from 'react-router-dom';
import { X, Zap, Activity } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import type { Station } from '../../types';
import { STATION_STATUS_COLORS } from '../../config/constants';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

interface StationModalProps {
  station: Station | null;
  onClose: () => void;
}

export default function StationModal({ station, onClose }: StationModalProps) {
  const navigate = useNavigate();

  if (!station) return null;

  const consumed = Number(station.max_demand_kw);
  const available = Math.max(0, Number(station.available_power_kw));
  const chartData = [
    { name: 'Demanda', value: consumed },
    { name: 'Disponible', value: available },
  ];
  const chartColors = ['#ef4444', '#22c55e'];

  const statusColor =
    station.status === 'red' ? 'red' : station.status === 'yellow' ? 'yellow' : 'green';

  return (
    <div className="fixed top-0 right-0 h-full w-96 bg-[var(--card-bg)] border-l border-[var(--border-color)] shadow-2xl z-40 transform transition-transform overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[var(--border-color)]">
        <div>
          <h3 className="font-bold text-[var(--text-primary)]">{station.name}</h3>
          <p className="text-xs text-[var(--text-muted)]">{station.code}</p>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-[var(--hover-bg)] text-[var(--text-muted)] cursor-pointer"
        >
          <X size={18} />
        </button>
      </div>

      <div className="p-4 space-y-6">
        {/* Status */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-[var(--text-secondary)]">Estado:</span>
          <Badge color={statusColor}>
            {station.status === 'red'
              ? 'Debe energia'
              : station.status === 'yellow'
              ? 'Critico'
              : 'Operativo'}
          </Badge>
        </div>

        {/* Chart */}
        <div>
          <h4 className="text-sm font-medium text-[var(--text-primary)] mb-2">
            Maxima Demanda vs Potencia Disponible
          </h4>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {chartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={chartColors[index]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
              <span className="text-[var(--text-muted)]">Demanda: {consumed} kW</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
              <span className="text-[var(--text-muted)]">Disponible: {available} kW</span>
            </div>
          </div>
        </div>

        {/* Power details */}
        <div>
          <h4 className="text-sm font-medium text-[var(--text-primary)] mb-3">
            Detalle de Potencias
          </h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] rounded-lg">
              <div className="flex items-center gap-2">
                <Zap size={16} className="text-primary-500" />
                <span className="text-sm text-[var(--text-secondary)]">Capacidad del Transformador</span>
              </div>
              <span className="text-sm font-semibold text-[var(--text-primary)]">
                {Number(station.transformer_capacity_kw)} kW
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] rounded-lg">
              <div className="flex items-center gap-2">
                <Activity size={16} className="text-red-500" />
                <span className="text-sm text-[var(--text-secondary)]">Maxima Demanda</span>
              </div>
              <span className="text-sm font-semibold text-[var(--text-primary)]">
                {consumed} kW
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] rounded-lg">
              <div className="flex items-center gap-2">
                <Zap size={16} className="text-green-500" />
                <span className="text-sm text-[var(--text-secondary)]">Energia Disponible</span>
              </div>
              <span className="text-sm font-semibold" style={{ color: STATION_STATUS_COLORS[station.status] }}>
                {Number(station.available_power_kw)} kW
              </span>
            </div>
          </div>
        </div>

        {/* Action */}
        <Button
          className="w-full"
          onClick={() => { onClose(); navigate(`/stations/${station.id}`); }}
        >
          Ver Detalles de la Estacion
        </Button>
      </div>
    </div>
  );
}
