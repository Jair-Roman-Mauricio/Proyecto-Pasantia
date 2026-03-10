import { useState, useEffect, useMemo } from 'react';
import { Download, Filter } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';
import api from '../../config/api';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';

export default function ReportsView() {
  const [demandData, setDemandData] = useState<any[]>([]);
  const [requestsData, setRequestsData] = useState<any[]>([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedStationId, setSelectedStationId] = useState<number | null>(null);

  const loadData = (start?: string, end?: string) => {
    const params: Record<string, string> = {};
    if (start) params.start_date = start;
    if (end) params.end_date = end;
    api.get('/reports/demand-evolution', { params }).then((res) => setDemandData(res.data));
    api.get('/reports/requests-per-station', { params }).then((res) => setRequestsData(res.data));
  };

  useEffect(() => {
    loadData();
  }, []);

  // Auto-select first station when data loads
  useEffect(() => {
    if (demandData.length > 0 && selectedStationId === null) {
      setSelectedStationId(demandData[0].station_id);
    }
  }, [demandData, selectedStationId]);

  const stationData = useMemo(() => {
    return demandData.find((d) => d.station_id === selectedStationId) ?? demandData[0] ?? null;
  }, [demandData, selectedStationId]);

  const stationChartData = useMemo(() => {
    if (!stationData) return [];
    return [
      { name: 'Demanda Actual', value: Number(stationData.max_demand_kw), fill: '#ef4444' },
      { name: 'Energia Disponible', value: Math.max(0, Number(stationData.available_power_kw)), fill: '#22c55e' },
    ];
  }, [stationData]);

  const handleFilter = () => {
    loadData(startDate || undefined, endDate || undefined);
  };

  const handleExport = async () => {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response = await api.get('/reports/export/excel', { params, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = startDate || endDate
        ? `reportes_${startDate || 'inicio'}_${endDate || 'fin'}.xlsx`
        : 'reportes.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Error al exportar el reporte. Intente nuevamente.');
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-3 mb-6">
        <h2 className="text-xl font-bold text-[var(--text-primary)]">Reportes</h2>
        <Button variant="secondary" size="sm" onClick={handleExport}>
          <Download size={16} className="mr-2" /> Exportar Excel
        </Button>
      </div>

      <Card>
        <div className="flex items-end gap-4 flex-wrap">
          <div className="w-48">
            <Input
              label="Desde"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div className="w-48">
            <Input
              label="Hasta"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <Button size="sm" onClick={handleFilter}>
            <Filter size={16} className="mr-1" /> Filtrar
          </Button>
          {(startDate || endDate) && (
            <Button variant="ghost" size="sm" onClick={() => { setStartDate(''); setEndDate(''); loadData(); }}>
              Limpiar
            </Button>
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 mt-6">
        {/* Grafico 1: Demanda por estacion */}
        <Card>
          <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
            <h3 className="text-sm font-medium text-[var(--text-secondary)]">
              Demanda vs Energia Disponible (kW)
            </h3>
            <select
              value={selectedStationId ?? ''}
              onChange={(e) => setSelectedStationId(Number(e.target.value))}
              className="text-sm px-3 py-1.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] cursor-pointer"
            >
              {demandData.map((d) => (
                <option key={d.station_id} value={d.station_id}>
                  {d.station_name}
                </option>
              ))}
            </select>
          </div>

          {stationData && (
            <div className="flex gap-6 text-xs text-[var(--text-muted)] mb-3">
              <span>Capacidad total: <strong className="text-[var(--text-primary)]">{Number(stationData.transformer_capacity_kw).toFixed(1)} kW</strong></span>
              <span>Estado: <strong className={stationData.status === 'green' ? 'text-green-500' : stationData.status === 'yellow' ? 'text-yellow-500' : 'text-red-500'}>
                {stationData.status === 'green' ? 'Energia suficiente' : stationData.status === 'yellow' ? 'Menos del 20% disponible' : 'Debe energia'}
              </strong></span>
            </div>
          )}

          <div className="h-80">
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={stationChartData} barCategoryGap="40%">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
                <YAxis stroke="var(--text-muted)" fontSize={11} unit=" kW" />
                <Tooltip
                  formatter={(value: number) => [`${value.toFixed(1)} kW`]}
                  contentStyle={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)' }}
                  cursor={{ fill: 'rgba(128,128,128,0.08)' }}
                />
                {stationData && (
                  <ReferenceLine
                    y={Number(stationData.transformer_capacity_kw)}
                    stroke="#6b7280"
                    strokeDasharray="6 3"
                    label={{ value: 'Cap. Max', position: 'insideTopRight', fontSize: 10, fill: 'var(--text-muted)' }}
                  />
                )}
                <Bar dataKey="value" name="kW" radius={[4, 4, 0, 0]}>
                  {stationChartData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Grafico 2: Solicitudes por estacion */}
        <Card>
          <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-4">Solicitudes de Opersac por Estacion</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={requestsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="station_name" stroke="var(--text-muted)" fontSize={10} interval={0} />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)' }}
                  cursor={{ fill: 'rgba(128,128,128,0.08)' }}
                />
                <Legend />
                <Bar dataKey="pending" name="Pendientes" fill="#eab308" />
                <Bar dataKey="approved" name="Aprobadas" fill="#22c55e" />
                <Bar dataKey="rejected" name="Rechazadas" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}
