import { useQuery } from '@tanstack/react-query';
import * as api from '@/lib/api';

export const queryKeys = {
  voices: (params?: Record<string, string>) => ['voices', params ?? {}] as const,
  voice: (id: string) => ['voice', id] as const,
  filters: () => ['filters'] as const,
};

export function useVoices(params?: Record<string, string>) {
  return useQuery({
    queryKey: queryKeys.voices(params),
    queryFn: () => api.getVoices(params),
  });
}

export function useVoice(id: string) {
  return useQuery({
    queryKey: queryKeys.voice(id),
    queryFn: () => api.getVoice(id),
    enabled: !!id,
  });
}

export function useFilters() {
  return useQuery({
    queryKey: queryKeys.filters(),
    queryFn: () => api.getFilters(),
    staleTime: 60_000,
  });
}
