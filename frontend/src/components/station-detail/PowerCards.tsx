import { Zap, Activity, Gauge, Battery } from 'lucide-react';
import type { BarPowerSummary } from '../../types';
import Card from '../ui/Card';

interface PowerCardsProps {
  summary: BarPowerSummary;
}

export default function PowerCards({ summary }: PowerCardsProps) {
  const cards = [
    {
      label: 'Potencia Instalada Total',
      value: `${summary.total_installed_power_kw.toFixed(1)} kW`,
      icon: Zap,
      color: 'text-blue-500',
    },
    {
      label: 'Maxima Demanda Total',
      value: `${summary.total_max_demand_kw.toFixed(1)} kW`,
      icon: Activity,
      color: 'text-red-500',
    },
    {
      label: 'Capacidad Max Tablero',
      value: `${summary.max_board_capacity_kw.toFixed(1)} kW / ${summary.max_board_capacity_a.toFixed(1)} A`,
      icon: Gauge,
      color: 'text-yellow-500',
    },
    {
      label: 'Potencia Disponible',
      value: `${summary.available_power_kw.toFixed(1)} kW`,
      icon: Battery,
      color: summary.available_power_kw >= 0 ? 'text-green-500' : 'text-red-500',
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-3">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.label} className="!p-3">
            <div className="flex items-center gap-2 mb-1">
              <Icon size={16} className={card.color} />
              <span className="text-xs text-[var(--text-muted)]">{card.label}</span>
            </div>
            <p className="text-lg font-bold text-[var(--text-primary)]">{card.value}</p>
          </Card>
        );
      })}
    </div>
  );
}
