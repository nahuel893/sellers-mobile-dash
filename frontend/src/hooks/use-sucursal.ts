import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';

export function useSucursal(id: string | undefined) {
  return useQuery({
    queryKey: ['sucursal', id],
    queryFn: () => api.getSucursal(id!),
    enabled: !!id,
  });
}
