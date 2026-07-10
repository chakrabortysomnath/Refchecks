import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type {
  BiasAnalysis,
  AttackDefinition,
  DefenseDefinition,
} from '../api/types'

export function useBiasAnalysis(
  competitionId: number | null,
  attackDefinition: AttackDefinition,
  defenseDefinition: DefenseDefinition,
) {
  return useQuery({
    queryKey: [
      'bias-analysis',
      competitionId,
      attackDefinition,
      defenseDefinition,
    ],
    queryFn: () => {
      const params = new URLSearchParams({
        attack_definition: attackDefinition,
        defense_definition: defenseDefinition,
        // BiasMetrics has no per-definition cache column, so the backend
        // returns whichever definition was computed last unless we force a
        // recompute. recalculate=true makes the selected definitions take
        // effect. Results are cached per (competition, attack, defense) by
        // React Query, so switching back to a prior combo is instant.
        recalculate: 'true',
      })
      return apiFetch<BiasAnalysis>(
        `/api/competitions/${competitionId}/bias-analysis?${params}`,
      )
    },
    enabled: competitionId != null,
  })
}
