import api from '../config/api';
import type { Station, PowerSummary, Bar } from '../types';

/**
 * Servicio de estaciones.
 * Encapsula las peticiones HTTP relacionadas con las estaciones de la Línea 1 del Metro.
 */
export const stationService = {
  /**
   * Obtiene la lista completa de estaciones registradas en el sistema.
   *
   * @returns Una promesa que resuelve con un arreglo de objetos `Station`.
   */
  async getAll(): Promise<Station[]> {
    const { data } = await api.get<Station[]>('/stations');
    return data;
  },

  /**
   * Obtiene los datos de una estación específica por su identificador único.
   *
   * @param id - Identificador numérico de la estación.
   * @returns Una promesa que resuelve con el objeto `Station` correspondiente.
   */
  async getById(id: number): Promise<Station> {
    const { data } = await api.get<Station>(`/stations/${id}`);
    return data;
  },

  /**
   * Obtiene el resumen de potencia eléctrica de una estación.
   * Incluye métricas como potencia activa, reactiva y corriente total de la estación.
   *
   * @param id - Identificador numérico de la estación.
   * @returns Una promesa que resuelve con el objeto `PowerSummary` de la estación.
   */
  async getPowerSummary(id: number): Promise<PowerSummary> {
    const { data } = await api.get<PowerSummary>(`/stations/${id}/power-summary`);
    return data;
  },

  /**
   * Obtiene las barras eléctricas asociadas a una estación.
   * Las barras agrupan los circuitos que comparten un mismo punto de alimentación.
   *
   * @param stationId - Identificador numérico de la estación propietaria de las barras.
   * @returns Una promesa que resuelve con un arreglo de objetos `Bar`.
   */
  async getBars(stationId: number): Promise<Bar[]> {
    const { data } = await api.get<Bar[]>(`/bars/station/${stationId}`);
    return data;
  },
};
