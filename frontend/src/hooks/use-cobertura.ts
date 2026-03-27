import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';

export function useCobertura(sucursal?: string, supervisor?: string, vendedor?: string) {
  return useQuery({
    queryKey: ['cobertura', sucursal, supervisor, vendedor],
    queryFn: () => api.getCobertura(sucursal, supervisor, vendedor),
    enabled: !!sucursal || !!vendedor,
  });
}
