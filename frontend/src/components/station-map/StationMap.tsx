import { useState, useEffect } from 'react';
import { stationService } from '../../services/stationService';
import type { Station } from '../../types';
import StationModal from './StationModal';
import Spinner from '../ui/Spinner';

type LabelDir = 'top' | 'bottom' | 'left' | 'right' | 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';

interface StationPos {
  x: number;
  y: number;
  labelDir: LabelDir;
}

// Positions ordered from Bayovar (top-left) to Villa El Salvador (right)
// The API returns stations by order_index (1=VES, 26=Bayovar), we reverse for display
const STATION_POSITIONS: StationPos[] = [
  // SJL zone - steep zigzag descending
  { x: 35,   y: 48,  labelDir: 'top' },             // 0: Bayovar (L1)
  { x: 82,   y: 130, labelDir: 'left' },           // 1: Santa Rosa
  { x: 145,  y: 78,  labelDir: 'top' },            // 2: San Martin
  { x: 172,  y: 195, labelDir: 'left' },           // 3: San Carlos
  { x: 228,  y: 158, labelDir: 'top-right' },      // 4: Los Postes
  { x: 265,  y: 270, labelDir: 'left' },           // 5: Los Jardines
  { x: 322,  y: 222, labelDir: 'top-right' },      // 6: Piramide del Sol
  // La Victoria zone
  { x: 368,  y: 340, labelDir: 'left' },           // 7: Caja de Agua
  { x: 418,  y: 300, labelDir: 'top-right' },      // 8: Presbitero Maestro
  { x: 442,  y: 400, labelDir: 'left' },           // 9: El Angel
  { x: 485,  y: 350, labelDir: 'top' },            // 10: Miguel Grau
  { x: 525,  y: 435, labelDir: 'bottom' },         // 11: Gamarra
  // Central zone
  { x: 575,  y: 382, labelDir: 'top' },            // 12: Arriola
  { x: 622,  y: 448, labelDir: 'bottom' },         // 13: La Cultura
  { x: 670,  y: 395, labelDir: 'top' },            // 14: San Borja Sur
  { x: 705,  y: 452, labelDir: 'bottom' },         // 15: Angamos
  { x: 752,  y: 365, labelDir: 'top' },            // 16: Cabitos
  { x: 795,  y: 418, labelDir: 'bottom' },         // 17: Ayacucho
  // SJM zone - trending upward
  { x: 842,  y: 338, labelDir: 'top' },            // 18: Jorge Chavez
  { x: 875,  y: 385, labelDir: 'bottom-right' },   // 19: Atocongo
  { x: 932,  y: 290, labelDir: 'top' },            // 20: San Juan
  { x: 955,  y: 340, labelDir: 'bottom' },         // 21: Maria Auxiliadora
  // VES zone - final stretch
  { x: 1010, y: 265, labelDir: 'top' },            // 22: Villa Maria
  { x: 1042, y: 315, labelDir: 'bottom' },         // 23: Pumacahua
  { x: 1132, y: 240, labelDir: 'top' },            // 24: Parque Industrial
  { x: 1192, y: 310, labelDir: 'right' },          // 25: Villa El Salvador (L1)
];

const DISTRICTS = [
  { text: 'LIMA', x: 200, y: 95 },
  { text: 'LA VICTORIA', x: 520, y: 260 },
  { text: 'SAN JUAN DE MIRAFLORES', x: 820, y: 475 },
  { text: 'VILLA EL SALVADOR', x: 1120, y: 180 },
];

const STATUS_COLORS: Record<string, string> = {
  green: '#22C55E',
  yellow: '#F59E0B',
  red: '#EF4444',
};

type Anchor = 'middle' | 'start' | 'end';

function getLabelPos(pos: StationPos): { x: number; y: number; anchor: Anchor } {
  const off = 16;
  switch (pos.labelDir) {
    case 'top':          return { x: pos.x, y: pos.y - off, anchor: 'middle' };
    case 'bottom':       return { x: pos.x, y: pos.y + off + 12, anchor: 'middle' };
    case 'left':         return { x: pos.x - off, y: pos.y + 4, anchor: 'end' };
    case 'right':        return { x: pos.x + off, y: pos.y + 4, anchor: 'start' };
    case 'top-right':    return { x: pos.x + off, y: pos.y - 6, anchor: 'start' };
    case 'top-left':     return { x: pos.x - off, y: pos.y - 6, anchor: 'end' };
    case 'bottom-right': return { x: pos.x + off, y: pos.y + 16, anchor: 'start' };
    case 'bottom-left':  return { x: pos.x - off, y: pos.y + 16, anchor: 'end' };
    default:             return { x: pos.x, y: pos.y - off, anchor: 'middle' };
  }
}

export default function StationMap() {
  const [stations, setStations] = useState<Station[]>([]);
  const [selectedStation, setSelectedStation] = useState<Station | null>(null);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    stationService
      .getAll()
      .then(setStations)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    );
  }

  // API returns stations by order_index ascending (1=VES ... 26=Bayovar)
  // Reverse so index 0 = Bayovar (left) and index 25 = VES (right)
  const displayStations = [...stations].reverse();
  const pathPoints = STATION_POSITIONS.map(p => `${p.x},${p.y}`).join(' ');

  return (
    <div>
      <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">
        Mapa de la Linea 1 del Metro de Lima
      </h2>
      <p className="text-sm text-[var(--text-muted)] mb-4">
        26 estaciones &mdash; Bayovar a Villa El Salvador
      </p>

      <div className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-4 overflow-x-auto">
        <svg
          viewBox="0 0 1280 510"
          className="w-full min-w-[800px]"
          style={{ minHeight: '420px' }}
        >
          {/* District labels (faded background text) */}
          {DISTRICTS.map((d, i) => (
            <text
              key={i}
              x={d.x}
              y={d.y}
              fill="currentColor"
              className="text-[var(--text-muted)]"
              opacity={0.08}
              fontSize="30"
              fontWeight="bold"
              textAnchor="middle"
            >
              {d.text}
            </text>
          ))}

          {/* Green connection line */}
          <polyline
            points={pathPoints}
            fill="none"
            stroke="#86EFAC"
            strokeWidth="8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* L1 badge - Bayovar (start) */}
          <circle cx={STATION_POSITIONS[0].x} cy={STATION_POSITIONS[0].y} r="20" fill="#22C55E" />
          <text
            x={STATION_POSITIONS[0].x}
            y={STATION_POSITIONS[0].y + 6}
            textAnchor="middle"
            fill="white"
            fontSize="14"
            fontWeight="bold"
          >
            L1
          </text>

          {/* L1 badge - Villa El Salvador (end) */}
          <circle cx={STATION_POSITIONS[25].x} cy={STATION_POSITIONS[25].y} r="20" fill="#22C55E" />
          <text
            x={STATION_POSITIONS[25].x}
            y={STATION_POSITIONS[25].y + 6}
            textAnchor="middle"
            fill="white"
            fontSize="14"
            fontWeight="bold"
          >
            L1
          </text>

          {/* Station nodes and labels */}
          {displayStations.map((station, index) => {
            if (index >= STATION_POSITIONS.length) return null;
            const pos = STATION_POSITIONS[index];
            const isEndpoint = index === 0 || index === 25;
            const label = getLabelPos(pos);
            const isHovered = hoveredIndex === index;
            const isSelected = selectedStation?.id === station.id;
            const color = STATUS_COLORS[station.status] || STATUS_COLORS.green;

            return (
              <g
                key={station.id}
                className="cursor-pointer"
                onClick={() => setSelectedStation(station)}
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
              >
                {/* Invisible hit area */}
                <circle cx={pos.x} cy={pos.y} r="22" fill="transparent" />

                {/* Station dot (skip for L1 endpoints) */}
                {!isEndpoint && (
                  <>
                    {isHovered && (
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r="14"
                        fill={color}
                        opacity={0.25}
                      />
                    )}
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={isHovered ? 10 : 8}
                      fill={color}
                      stroke="white"
                      strokeWidth="2.5"
                    />
                  </>
                )}

                {/* Station name */}
                <text
                  x={label.x}
                  y={label.y}
                  textAnchor={label.anchor}
                  fill="currentColor"
                  className="text-[var(--text-primary)]"
                  fontSize={isHovered ? '11.5' : '10'}
                  fontWeight={isHovered || isSelected ? '700' : '500'}
                >
                  {station.name}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 mt-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-xs text-[var(--text-muted)]">Debe energia</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <span className="text-xs text-[var(--text-muted)]">Menos del 20% disponible</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-xs text-[var(--text-muted)]">Energia suficiente</span>
        </div>
      </div>

      {/* Station detail modal */}
      {selectedStation && (
        <StationModal
          station={selectedStation}
          onClose={() => setSelectedStation(null)}
        />
      )}
    </div>
  );
}
