import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { stationService } from '../services/stationService';
import type { Station } from '../types';
import Button from '../components/ui/Button';
import Spinner from '../components/ui/Spinner';
import SummaryTab from '../components/station-detail/SummaryTab';
import UnifilarTab from '../components/station-detail/UnifilarTab';
import BarsCircuitsTab from '../components/station-detail/BarsCircuitsTab';

type Tab = 'summary' | 'unifilar' | 'bars';

export default function StationDetailPage() {
  const { stationId } = useParams<{ stationId: string }>();
  const navigate = useNavigate();
  const [station, setStation] = useState<Station | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('unifilar');
  const [isLoading, setIsLoading] = useState(true);

  const refreshStation = useCallback(() => {
    if (stationId) {
      stationService.getById(Number(stationId)).then(setStation);
    }
  }, [stationId]);

  useEffect(() => {
    if (stationId) {
      stationService
        .getById(Number(stationId))
        .then(setStation)
        .catch(() => navigate('/'))
        .finally(() => setIsLoading(false));
    }
  }, [stationId, navigate]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!station) return null;

  const tabs: { id: Tab; label: string }[] = [
    { id: 'summary', label: 'Resumen' },
    { id: 'unifilar', label: 'Mapa Unifilar' },
    { id: 'bars', label: 'Barras y Circuitos' },
  ];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
          <ArrowLeft size={18} />
        </Button>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center text-white font-bold">
            L1
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">
              Estacion {station.name}
            </h1>
            <p className="text-sm text-[var(--text-muted)]">{station.code}</p>
          </div>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="flex gap-1 mb-6 bg-[var(--bg-primary)] rounded-lg p-1 border border-[var(--border-color)] w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer ${
              activeTab === tab.id
                ? 'bg-primary-600 text-white'
                : 'text-[var(--text-secondary)] hover:bg-[var(--hover-bg)]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'summary' && <SummaryTab station={station} />}
      {activeTab === 'unifilar' && <UnifilarTab station={station} />}
      {activeTab === 'bars' && <BarsCircuitsTab station={station} onStationChanged={refreshStation} />}
    </div>
  );
}
