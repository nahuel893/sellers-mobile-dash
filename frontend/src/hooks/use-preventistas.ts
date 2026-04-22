import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';
import type { Preventista } from '../types/api';

export function usePreventistas(sucursal = 1) {
  return useQuery<Preventista[]>({
    queryKey: ['preventistas', sucursal],
    queryFn: () => api.getPreventistas(sucursal),
    staleTime: 1000 * 60 * 10, // 10 min
  });
}
