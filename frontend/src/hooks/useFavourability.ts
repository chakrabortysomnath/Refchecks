import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type {
  AttackDefinition,
  DefenseDefinition,
  FavourabilityResponse,
  SeverityWeights,
} from '../api/types'

// Severity-weighted favourability model. Weights are part of the query key so
// adjusting them refetches; keepPreviousData avoids a flash of empty charts
// while the (recomputed, can-be-slow) response is in flight.
export function useFavourability(
  competitionId: number | null,
  attack: AttackDefinition,
  defense: DefenseDefinition,
  weights: SeverityWeights,
) {
  return useQuery({
    queryKey: ['favourability', competitionId, attack, defense, weights],
    queryFn: () => {
      const params = new URLSearchParams({
        attack_definition: attack,
        defense_definition: defense,
        w_penalty: String(weights.penalty),
        w_red: String(weights.red),
        w_yellow: String(weights.yellow),
        w_foul: String(weights.foul),
        w_advantage: String(weights.advantage),
      })
      return apiFetch<FavourabilityResponse>(
        `/api/competitions/${competitionId}/favourability?${params}`,
      )
    },
    enabled: competitionId != null,
    placeholderData: keepPreviousData,
  })
}
