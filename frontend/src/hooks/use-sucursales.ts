import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';

export function useSucursales() {
  return useQuery({
    queryKey: ['sucursales'],
    queryFn: api.getSucursales,
    staleTime: 1000 * 60 * 60,
  });
}
