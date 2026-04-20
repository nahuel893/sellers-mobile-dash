import { useQuery } from '@tanstack/react-query';
import { ventasApi } from '../../lib/ventas-api-client';
import type { VentasZonasParams } from '../../types/ventas';

export function useVentasZonas(params: VentasZonasParams | null) {
  return useQuery({
    queryKey: ['ventas-zonas', params],
    queryFn: () => ventasApi.getZonas(params!),
    enabled: params !== null,
    staleTime: 1000 * 60 * 5, // 5 min
  });
}
