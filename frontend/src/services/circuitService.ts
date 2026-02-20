import api from '../config/api';
import type { Circuit, SubCircuit, BarPowerSummary } from '../types';

export const circuitService = {
  async getByBar(barId: number): Promise<Circuit[]> {
    const { data } = await api.get<Circuit[]>(`/circuits/bar/${barId}`);
    return data;
  },

  async getById(id: number): Promise<Circuit> {
    const { data } = await api.get<Circuit>(`/circuits/${id}`);
    return data;
  },

  async create(barId: number, circuit: Partial<Circuit> & { force?: boolean }): Promise<Circuit> {
    const { data } = await api.post<Circuit>(`/circuits/bar/${barId}`, circuit);
    return data;
  },

  async update(id: number, circuit: Partial<Circuit>): Promise<Circuit> {
    const { data } = await api.put<Circuit>(`/circuits/${id}`, circuit);
    return data;
  },

  async updateStatus(id: number, status: string): Promise<Circuit> {
    const { data } = await api.put<Circuit>(`/circuits/${id}/status`, { status });
    return data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/circuits/${id}`);
  },

  async getSubCircuits(circuitId: number): Promise<SubCircuit[]> {
    const { data } = await api.get<SubCircuit[]>(`/sub-circuits/circuit/${circuitId}`);
    return data;
  },

  async createSubCircuit(circuitId: number, sub: Partial<SubCircuit>): Promise<SubCircuit> {
    const { data } = await api.post<SubCircuit>(`/sub-circuits/circuit/${circuitId}`, sub);
    return data;
  },

  async deleteSubCircuit(id: number): Promise<void> {
    await api.delete(`/sub-circuits/${id}`);
  },

  async updateSubCircuitStatus(id: number, status: string): Promise<SubCircuit> {
    const { data } = await api.put<SubCircuit>(`/sub-circuits/${id}/status`, { status });
    return data;
  },

  async getBarPowerSummary(barId: number): Promise<BarPowerSummary> {
    const { data } = await api.get<BarPowerSummary>(`/bars/${barId}/power-summary`);
    return data;
  },
};
