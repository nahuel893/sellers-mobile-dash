import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';

export function useSupervisor(slug: string | undefined, sucursal?: string | null) {
  return useQuery({
    queryKey: ['supervisor', slug, sucursal],
    queryFn: () => api.getSupervisor(slug!, sucursal ?? undefined),
    enabled: !!slug,
  });
}
