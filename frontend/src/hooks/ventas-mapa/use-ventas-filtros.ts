import { useQuery } from '@tanstack/react-query';
import { ventasApi } from '../../lib/ventas-api-client';

export function useVentasFiltros() {
  return useQuery({
    queryKey: ['ventas-filtros-opciones'],
    queryFn: ventasApi.getFiltrosOpciones,
    staleTime: 1000 * 60 * 10, // 10 min — opciones cambian poco
  });
}
