import { useState, useEffect } from 'react';
import { Download } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../../config/api';
import Card from '../ui/Card';
import Button from '../ui/Button';

export default function ReportsView() {
  const [demandData, setDemandData] = useState<any[]>([]);
  const [requestsData, setRequestsData] = useState<any[]>([]);

  useEffect(() => {
    api.get('/reports/demand-evolution').then((res) => setDemandData(res.data));
    api.get('/reports/requests-per-station').then((res) => setRequestsData(res.data));
  }, []);

  const handleExport = async () => {
    const response = await api.get('/reports/export/excel', { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'reportes.xlsx';
    link.click();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-[var(--text-primary)]">Reportes</h2>
        <Button variant="secondary" size="sm" onClick={handleExport}>
          <Download size={16} className="mr-2" /> Exportar Excel
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6">
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
