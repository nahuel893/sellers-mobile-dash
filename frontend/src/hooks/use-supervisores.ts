import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';

export function useSupervisores(sucursal: string | null) {
  return useQuery({
    queryKey: ['supervisores', sucursal],
    queryFn: () => api.getSupervisores(sucursal!),
    enabled: !!sucursal,
  });
}
