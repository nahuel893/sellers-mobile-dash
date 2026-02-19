import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';

export function useVendedor(slug: string | undefined) {
  return useQuery({
    queryKey: ['vendedor', slug],
    queryFn: () => api.getVendedor(slug!),
    enabled: !!slug,
  });
}
