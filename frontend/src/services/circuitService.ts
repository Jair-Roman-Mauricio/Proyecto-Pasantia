/**
 * @file circuitService.ts
 * Capa de acceso a datos para circuitos y subcircuitos eléctricos de las barras
 * de la Línea 1 del Metro de Lima. Todas las funciones realizan llamadas HTTP
 * a través de la instancia Axios configurada en `config/api` y devuelven promesas
 * tipadas con las interfaces definidas en `types/index.ts`.
 */

import api from '../config/api';
import type { Circuit, SubCircuit, BarPowerSummary } from '../types';

/**
 * Servicio de circuitos y subcircuitos eléctricos.
 * Encapsula las operaciones CRUD sobre circuitos asociados a barras eléctricas,
 * sus subcircuitos derivados y el resumen de potencia por barra.
 */
export const circuitService = {
  /**
   * Obtiene todos los circuitos pertenecientes a una barra eléctrica.
   *
   * @param barId - Identificador numérico de la barra.
   * @returns Una promesa que resuelve con un arreglo de objetos `Circuit`.
   */
  async getByBar(barId: number): Promise<Circuit[]> {
    const { data } = await api.get<Circuit[]>(`/circuits/bar/${barId}`);
    return data;
  },

  /**
   * Obtiene los datos de un circuito específico por su identificador único.
   *
   * @param id - Identificador numérico del circuito.
   * @returns Una promesa que resuelve con el objeto `Circuit` correspondiente.
   */
  async getById(id: number): Promise<Circuit> {
    const { data } = await api.get<Circuit>(`/circuits/${id}`);
    return data;
  },

  /**
   * Crea un nuevo circuito dentro de una barra eléctrica.
   * La propiedad `force` del payload permite omitir validaciones de capacidad si se requiere.
   *
   * @param barId   - Identificador de la barra a la que pertenecerá el circuito.
   * @param circuit - Datos parciales del circuito a crear; puede incluir `force: true`
   *                  para forzar la creación ignorando advertencias del servidor.
   * @returns Una promesa que resuelve con el objeto `Circuit` creado por el backend.
   */
  async create(barId: number, circuit: Partial<Circuit> & { force?: boolean }): Promise<Circuit> {
    const { data } = await api.post<Circuit>(`/circuits/bar/${barId}`, circuit);
    return data;
  },

  /**
   * Actualiza los datos de un circuito existente (edición parcial).
   *
   * @param id      - Identificador numérico del circuito a modificar.
   * @param circuit - Campos del circuito que se desean actualizar.
   * @returns Una promesa que resuelve con el objeto `Circuit` actualizado.
   */
  async update(id: number, circuit: Partial<Circuit>): Promise<Circuit> {
    const { data } = await api.put<Circuit>(`/circuits/${id}`, circuit);
    return data;
  },

  /**
   * Actualiza únicamente el estado operativo de un circuito (p. ej. `'active'`, `'inactive'`).
   *
   * @param id     - Identificador numérico del circuito.
   * @param status - Nuevo estado a asignar al circuito.
   * @returns Una promesa que resuelve con el objeto `Circuit` con el estado actualizado.
   */
  async updateStatus(id: number, status: string): Promise<Circuit> {
    const { data } = await api.put<Circuit>(`/circuits/${id}/status`, { status });
    return data;
  },

  /**
   * Elimina un circuito del sistema de forma permanente.
   *
   * @param id - Identificador numérico del circuito a eliminar.
   * @returns Una promesa que resuelve sin valor al completarse la eliminación.
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/circuits/${id}`);
  },

  /**
   * Obtiene los subcircuitos derivados de un circuito padre.
   *
   * @param circuitId - Identificador numérico del circuito padre.
   * @returns Una promesa que resuelve con un arreglo de objetos `SubCircuit`.
   */
  async getSubCircuits(circuitId: number): Promise<SubCircuit[]> {
    const { data } = await api.get<SubCircuit[]>(`/sub-circuits/circuit/${circuitId}`);
    return data;
  },

  /**
   * Crea un nuevo subcircuito dentro de un circuito padre.
   *
   * @param circuitId - Identificador del circuito al que pertenecerá el subcircuito.
   * @param sub       - Datos parciales del subcircuito a crear.
   * @returns Una promesa que resuelve con el objeto `SubCircuit` creado por el backend.
   */
  async createSubCircuit(circuitId: number, sub: Partial<SubCircuit>): Promise<SubCircuit> {
    const { data } = await api.post<SubCircuit>(`/sub-circuits/circuit/${circuitId}`, sub);
    return data;
  },

  /**
   * Actualiza los datos técnicos de un subcircuito existente (edición parcial).
   *
   * @param id   - Identificador numérico del subcircuito a modificar.
   * @param data - Campos del subcircuito que se desean actualizar.
   * @returns Una promesa que resuelve con el objeto `SubCircuit` actualizado.
   */
  async updateSubCircuit(id: number, data: Partial<SubCircuit>): Promise<SubCircuit> {
    const { data: res } = await api.put<SubCircuit>(`/sub-circuits/${id}`, data);
    return res;
  },

  /**
   * Elimina un subcircuito del sistema de forma permanente.
   *
   * @param id - Identificador numérico del subcircuito a eliminar.
   * @returns Una promesa que resuelve sin valor al completarse la eliminación.
   */
  async deleteSubCircuit(id: number): Promise<void> {
    await api.delete(`/sub-circuits/${id}`);
  },

  /**
   * Actualiza únicamente el estado operativo de un subcircuito.
   *
   * @param id     - Identificador numérico del subcircuito.
   * @param status - Nuevo estado a asignar al subcircuito.
   * @returns Una promesa que resuelve con el objeto `SubCircuit` con el estado actualizado.
   */
  async updateSubCircuitStatus(id: number, status: string): Promise<SubCircuit> {
    const { data } = await api.put<SubCircuit>(`/sub-circuits/${id}/status`, { status });
    return data;
  },

  /**
   * Obtiene el resumen de potencia eléctrica de una barra, calculado a partir
   * de los circuitos activos que la componen.
   *
   * @param barId - Identificador numérico de la barra eléctrica.
   * @returns Una promesa que resuelve con el objeto `BarPowerSummary`.
   */
  async getBarPowerSummary(barId: number): Promise<BarPowerSummary> {
    const { data } = await api.get<BarPowerSummary>(`/bars/${barId}/power-summary`);
    return data;
  },
};
