import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';

export function useDiasHabiles() {
  return useQuery({
    queryKey: ['dias-habiles'],
    queryFn: api.getDiasHabiles,
    staleTime: 1000 * 60 * 60, // 1 hora (solo cambia una vez al día)
  });
}
