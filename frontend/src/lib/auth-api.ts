/**
 * Raw auth API calls — these use fetch directly, NOT apiFetch.
 * They are the auth layer itself and must NOT go through the interceptor.
 */

import type { AuthUser, LoginRequest, LoginResponse, TokenRefreshResponse } from '../types/api';

const AUTH_BASE = '/api/auth';

export const authApi = {
  login: async (creds: LoginRequest): Promise<LoginResponse> => {
    const res = await fetch(`${AUTH_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(creds),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({})) as { detail?: string };
      throw new Error(detail.detail ?? 'Credenciales inválidas');
    }
    return res.json() as Promise<LoginResponse>;
  },

  refresh: async (): Promise<TokenRefreshResponse> => {
    const res = await fetch(`${AUTH_BASE}/refresh`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Refresh failed');
    return res.json() as Promise<TokenRefreshResponse>;
  },

  logout: async (): Promise<void> => {
    await fetch(`${AUTH_BASE}/logout`, {
      method: 'POST',
      credentials: 'include',
    });
  },

  me: async (token: string): Promise<AuthUser> => {
    const res = await fetch(`${AUTH_BASE}/me`, {
      headers: { Authorization: `Bearer ${token}` },
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Unauthorized');
    return res.json() as Promise<AuthUser>;
  },
};
