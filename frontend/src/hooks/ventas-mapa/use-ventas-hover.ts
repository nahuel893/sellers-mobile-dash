import { useQuery } from '@tanstack/react-query';
import { ventasApi } from '../../lib/ventas-api-client';

interface UseVentasHoverParams {
  id_cliente: number | null;
  fecha_ini: string;
  fecha_fin: string;
}

export function useVentasHover({ id_cliente, fecha_ini, fecha_fin }: UseVentasHoverParams) {
  return useQuery({
    queryKey: ['ventas-hover', id_cliente, fecha_ini, fecha_fin],
    queryFn: () =>
      ventasApi.getHoverCliente({
        id_cliente: id_cliente!,
        fecha_ini,
        fecha_fin,
      }),
    enabled: id_cliente !== null,
    staleTime: 1000 * 60 * 5,
  });
}
