import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';
import type { DeltaResponse } from '../types/api';

export function useAvanceDelta(
  slug: string | null | undefined,
  categoria = 'CERVEZAS',
) {
  return useQuery<DeltaResponse>({
    queryKey: ['delta', slug, categoria],
    queryFn: () => api.getDelta(slug!, categoria),
    enabled: !!slug,
    staleTime: 1000 * 60 * 5, // 5 min
  });
}
