import { useQuery } from '@tanstack/react-query';
import { ventasApi } from '../../lib/ventas-api-client';
import type { VentasComproParams } from '../../types/ventas';

/**
 * Hook para cargar datos de compro/no-compro.
 * Solo activo cuando params !== null (modo compro seleccionado).
 */
export function useVentasCompro(params: VentasComproParams | null) {
  return useQuery({
    queryKey: ['ventas-compro', params],
    queryFn: () => ventasApi.getCompro(params!),
    enabled: params !== null,
    staleTime: 1000 * 60 * 5, // 5 min
  });
}
