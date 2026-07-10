import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { DefinitionsResponse } from '../api/types'

export function useDefinitions() {
  return useQuery({
    queryKey: ['definitions'],
    queryFn: () => apiFetch<DefinitionsResponse>('/api/definitions'),
    // Definitions are static config — never goes stale within a session.
    staleTime: Infinity,
  })
}
