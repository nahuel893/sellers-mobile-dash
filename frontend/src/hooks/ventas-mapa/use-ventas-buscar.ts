import { useQuery } from '@tanstack/react-query';
import { ventasApi } from '../../lib/ventas-api-client';

/**
 * Hook para buscar clientes por nombre/ID en el mapa.
 *
 * - Solo activo cuando debouncedQ.length >= 2.
 * - El debounce (300ms) se maneja externamente en el componente
 *   para mantener el hook simple y reutilizable.
 */
export function useVentasBuscar(debouncedQ: string, limit = 50) {
  return useQuery({
    queryKey: ['ventas-buscar', debouncedQ, limit],
    queryFn: () => ventasApi.buscarClientes(debouncedQ, limit),
    enabled: debouncedQ.length >= 2,
    staleTime: 1000 * 60 * 2, // 2 min — resultados de búsqueda son volátiles
    placeholderData: [],
  });
}
