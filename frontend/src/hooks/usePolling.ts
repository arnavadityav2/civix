import { useQuery } from '@tanstack/react-query';

export function usePolling<T>(
  queryKey: unknown[],
  queryFn: () => Promise<T>,
  intervalMs = 3000,
  enabled = true
) {
  return useQuery<T>({
    queryKey,
    queryFn,
    refetchInterval: intervalMs,
    enabled,
  });
}
