import type { Station } from '../../types';
import { STATION_STATUS_COLORS } from '../../config/constants';

interface StationNodeProps {
  station: Station;
  onClick: () => void;
  isSelected: boolean;
}

export default function StationNode({ station, onClick, isSelected }: StationNodeProps) {
  const color = STATION_STATUS_COLORS[station.status] || '#22c55e';

  return (
    <div
      className="flex flex-col items-center cursor-pointer group"
      onClick={onClick}
    >
      <div
        className={`w-8 h-8 rounded-full border-3 flex items-center justify-center transition-all ${
          isSelected ? 'scale-125 shadow-lg' : 'group-hover:scale-110'
        }`}
        style={{
          borderColor: color,
          backgroundColor: isSelected ? color : 'transparent',
        }}
      >
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
      <span
        className={`text-[10px] mt-1 text-center w-16 leading-tight ${
          isSelected ? 'font-bold text-[var(--text-primary)]' : 'text-[var(--text-muted)]'
        }`}
      >
        {station.name}
      </span>
    </div>
  );
}
