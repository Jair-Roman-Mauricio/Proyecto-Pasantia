import api from '../config/api';
import type { Station, PowerSummary, Bar } from '../types';

export const stationService = {
  async getAll(): Promise<Station[]> {
    const { data } = await api.get<Station[]>('/stations');
    return data;
  },

  async getById(id: number): Promise<Station> {
    const { data } = await api.get<Station>(`/stations/${id}`);
    return data;
  },

  async getPowerSummary(id: number): Promise<PowerSummary> {
    const { data } = await api.get<PowerSummary>(`/stations/${id}/power-summary`);
    return data;
  },

  async getBars(stationId: number): Promise<Bar[]> {
    const { data } = await api.get<Bar[]>(`/bars/station/${stationId}`);
    return data;
  },
};
