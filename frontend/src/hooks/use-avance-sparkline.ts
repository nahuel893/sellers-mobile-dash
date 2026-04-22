import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';
import type { SparklineResponse } from '../types/api';

export function useAvanceSparkline(
  slug: string | null | undefined,
  dias = 18,
  categoria = 'CERVEZAS',
) {
  return useQuery<SparklineResponse>({
    queryKey: ['sparkline', slug, dias, categoria],
    queryFn: () => api.getSparkline(slug!, dias, categoria),
    enabled: !!slug,
    staleTime: 1000 * 60 * 5, // 5 min
  });
}
