import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';

export function useDashboard(supervisor: string | null, sucursal: string | null) {
  return useQuery({
    queryKey: ['dashboard', supervisor, sucursal],
    queryFn: () => api.getDashboard(supervisor!, sucursal!),
    enabled: !!supervisor && !!sucursal,
  });
}
