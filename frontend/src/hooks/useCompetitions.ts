import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { Competition } from '../api/types'

export function useCompetitions() {
  return useQuery({
    queryKey: ['competitions'],
    queryFn: () => apiFetch<Competition[]>('/api/competitions'),
  })
}
