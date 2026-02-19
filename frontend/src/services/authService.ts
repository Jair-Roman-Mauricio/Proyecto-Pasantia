import api from '../config/api';
import type { LoginResponse, UserBrief } from '../types';

export const authService = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/auth/login', { username, password });
    return data;
  },

  async getMe(): Promise<UserBrief> {
    const { data } = await api.get<UserBrief>('/auth/me');
    return data;
  },
};
