import { useQuery } from '@tanstack/react-query';
import { ventasApi } from '../../lib/ventas-api-client';
import type { VentasClientesParams } from '../../types/ventas';

export function useVentasClientes(params: VentasClientesParams | null) {
  return useQuery({
    queryKey: ['ventas-clientes', params],
    queryFn: () => ventasApi.getClientesMapa(params!),
    enabled: params !== null,
    staleTime: 1000 * 60 * 5, // 5 min
  });
}
