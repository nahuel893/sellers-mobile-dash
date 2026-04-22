import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api-client';
import type { WeatherResponse } from '../types/api';

export function useWeather(city = 'salta') {
  return useQuery<WeatherResponse>({
    queryKey: ['weather', city],
    queryFn: () => api.getWeather(city),
    staleTime: 1000 * 60 * 10,        // 10 min
    refetchInterval: 1000 * 60 * 10,  // 10 min
  });
}
