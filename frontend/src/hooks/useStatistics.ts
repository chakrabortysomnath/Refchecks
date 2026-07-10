import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { StatisticsResponse } from '../api/types'

// Heatmap + scatter data. Also the source of team_id -> team name (scatter_data
// carries both), which the bias table needs since bias-analysis rows only have
// team_id. Reused by the Phase 5 charts.
export function useStatistics(competitionId: number | null) {
  return useQuery({
    queryKey: ['statistics', competitionId],
    queryFn: () =>
      apiFetch<StatisticsResponse>(
        `/api/competitions/${competitionId}/statistics`,
      ),
    enabled: competitionId != null,
  })
}
