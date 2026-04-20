import {
  createContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';
import { useNavigate } from 'react-router';
import { useQueryClient } from '@tanstack/react-query';
import type { AuthUser, LoginRequest } from '../types/api';
import { authApi } from '../lib/auth-api';
import {
  setAccessTokenGetter,
  setAccessTokenSetter,
  setAuthFailureHandler,
} from '../lib/api-client';

// ---------------------------------------------------------------------------
// Context shape
// ---------------------------------------------------------------------------

export interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login(credentials: LoginRequest): Promise<void>;
  logout(): Promise<void>;
  refresh(): Promise<boolean>;
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextValue | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Register module-level setters so api-client can attach the token to requests
  // and call back into this context on auth failure.
  useEffect(() => {
    setAccessTokenGetter(() => accessToken);
    setAccessTokenSetter((t) => setAccessToken(t));
    setAuthFailureHandler(() => {
      setUser(null);
      setAccessToken(null);
      queryClient.clear();
      navigate('/login');
    });
  }, [accessToken, navigate, queryClient]);

  // Session restore: on first mount try to refresh via the httpOnly cookie.
  useEffect(() => {
    authApi
      .refresh()
      .then(({ access_token }) => {
        setAccessToken(access_token);
        return authApi.me(access_token);
      })
      .then((u) => setUser(u))
      .catch(() => {
        // Cookie absent or expired → stay unauthenticated
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (credentials: LoginRequest): Promise<void> => {
    const { access_token, user: u } = await authApi.login(credentials);
    setAccessToken(access_token);
    setUser(u);
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    await authApi.logout().catch(() => {});
    setUser(null);
    setAccessToken(null);
    queryClient.clear();
    navigate('/login');
  }, [navigate, queryClient]);

  const refresh = useCallback(async (): Promise<boolean> => {
    try {
      const { access_token } = await authApi.refresh();
      setAccessToken(access_token);
      const u = await authApi.me(access_token);
      setUser(u);
      return true;
    } catch {
      return false;
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}
