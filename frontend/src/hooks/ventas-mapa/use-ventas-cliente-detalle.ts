import { useQuery } from '@tanstack/react-query';
import { ventasApi } from '../../lib/ventas-api-client';

export function useVentasClienteDetalle(id_cliente: number | null) {
  return useQuery({
    queryKey: ['ventas-cliente-detalle', id_cliente],
    queryFn: () => ventasApi.getClienteDetalle(id_cliente!),
    enabled: id_cliente !== null && !isNaN(id_cliente),
    staleTime: 1000 * 60 * 5, // 5 min
  });
}
