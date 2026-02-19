import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';

export function useMapa(slug: string | undefined, sucursal?: string | null) {
  return useQuery({
    queryKey: ['mapa', slug, sucursal],
    queryFn: () => api.getMapa(slug!, sucursal ?? undefined),
    enabled: !!slug,
  });
}
