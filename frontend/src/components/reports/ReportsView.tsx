import { useState, useEffect } from 'react';
import { Download, Filter } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../../config/api';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';

export default function ReportsView() {
  const [demandData, setDemandData] = useState<any[]>([]);
  const [requestsData, setRequestsData] = useState<any[]>([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

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

  const handleFilter = () => {
    loadData(startDate || undefined, endDate || undefined);
  };

  const handleExport = async () => {
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
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
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
        <Card>
          <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-4">Evolucion de Demanda Electrica (kW)</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={demandData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="station_code" stroke="var(--text-muted)" fontSize={11} />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="max_demand_kw" name="Demanda Real" stroke="#ef4444" strokeWidth={2} />
                <Line type="monotone" dataKey="transformer_capacity_kw" name="Capacidad Maxima" stroke="#22c55e" strokeWidth={2} strokeDasharray="5 5" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-4">Solicitudes de Opersac por Estacion</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={requestsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="station_name" stroke="var(--text-muted)" fontSize={10} angle={-45} textAnchor="end" height={80} />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip />
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
