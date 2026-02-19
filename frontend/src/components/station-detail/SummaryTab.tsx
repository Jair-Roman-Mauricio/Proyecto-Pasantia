import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { Station } from '../../types';
import Card from '../ui/Card';

interface SummaryTabProps {
  station: Station;
}

export default function SummaryTab({ station }: SummaryTabProps) {
  const consumed = Number(station.max_demand_kw);
  const available = Math.max(0, Number(station.available_power_kw));

  const chartData = [
    { name: 'Potencia Consumida', value: consumed },
    { name: 'Potencia Disponible', value: available },
  ];
  const colors = ['#ef4444', '#22c55e'];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-4">
          Foto del Transformador
        </h3>
        <div className="aspect-video bg-[var(--bg-secondary)] rounded-lg flex items-center justify-center">
          <img
            src={`/api/v1/images/transformer/${station.id}`}
            alt="Transformador"
            className="max-h-full max-w-full object-contain rounded-lg"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
          <p className="text-sm text-[var(--text-muted)]">No hay imagen disponible</p>
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
    </div>
  );
}
