import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';

/** List of vendedor names (strings) supervised by the given supervisor. */
export function useVendedoresPorSupervisor(
  supervisor: string | null | undefined,
  sucursal: string = '1',
) {
  return useQuery<string[]>({
    queryKey: ['vendedores', supervisor, sucursal],
    queryFn: () => api.getVendedores(supervisor!, sucursal),
    enabled: !!supervisor,
    staleTime: 1000 * 60 * 10,
  });
}
