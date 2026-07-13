// TypeScript mirrors of the backend Pydantic schemas (app/schemas.py).
// Keep these in sync with the API contracts.

export interface Competition {
  id: number
  name: string
  season: number
  country: string | null
  statsbomb_id: string
  created_at: string
  updated_at: string
}

export interface Team {
  id: number
  name: string
  country: string | null
  statsbomb_id: number
  created_at: string
}

export interface Match {
  id: number
  statsbomb_id: string
  competition_id: number
  home_team_id: number
  away_team_id: number
  home_team_name: string
  away_team_name: string
  match_date: string
  home_score: number | null
  away_score: number | null
  status: string | null
  created_at: string
  updated_at: string
}

export interface BiasMetrics {
  id: number
  competition_id: number
  team_id: number
  fouls_committed_count: number
  fouls_conceded_count: number
  total_attacks: number
  total_defenses: number
  fouls_per_attack: number
  fouls_per_defense: number
  chi_square_stat: number | null
  p_value: number | null
  is_significant: boolean
  calculated_at: string
}

export interface BiasAnalysis {
  competition_id: number
  analysis_date: string
  teams: BiasMetrics[]
}

export interface HeatmapDataPoint {
  team: string
  match_id: number
  match_description: string
  foul_ratio: number
  fouls_committed: number
  attacks: number
}

export interface ScatterDataPoint {
  team: string
  team_id: number
  attacks: number
  defenses: number
  fouls_committed: number
  match_importance: string
}

export interface StatisticsResponse {
  competition_id: number
  heatmap_data: HeatmapDataPoint[]
  scatter_data: ScatterDataPoint[]
}

export interface User {
  id: number
  email: string
  name: string
  google_id: string
  role: string
  created_at: string
  updated_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

// GET /api/definitions returns each definition key mapped to a human-readable
// description.
export interface DefinitionsResponse {
  attack_definitions: Record<string, string>
  defense_definitions: Record<string, string>
}

// Attack/defense definition option keys accepted by the bias-analysis endpoint.
export type AttackDefinition =
  | 'all_combined'
  | 'shots_only'
  | 'passes_only'
  | 'dribbles_only'

export type DefenseDefinition =
  | 'all_combined'
  | 'tackles_only'
  | 'blocks_only'
  | 'duels_only'

// ===== Favourability model (GET /api/competitions/{id}/favourability) =====

// Configurable decision-severity weights. Higher = a more consequential
// referee decision. Mirrors DEFAULT_WEIGHTS in favourability_calculator.py.
export interface SeverityWeights {
  penalty: number
  red: number
  yellow: number
  foul: number
  advantage: number
}

export const DEFAULT_WEIGHTS: SeverityWeights = {
  penalty: 5,
  red: 4,
  yellow: 2,
  foul: 1,
  advantage: 0.5,
}

// Count of fouls by severity tier (one direction: committed or awarded).
export type FoulBreakdown = Record<keyof SeverityWeights, number>

export interface FavourabilityTeam {
  team_id: number
  team_name: string
  matches_played: number
  defenses: number
  attacks: number
  weighted_fouls_committed: number
  weighted_fouls_awarded: number
  committed_breakdown: FoulBreakdown
  awarded_breakdown: FoulBreakdown
  expected_committed: number
  expected_awarded: number
  // Standardized residuals, signed so + = favoured.
  z_leniency: number // let off when defending
  z_protection: number // protected when attacking
  favourability: number // z_leniency + z_protection
  leniency_outlier: boolean
  protection_outlier: boolean
}

export interface FavourabilityResponse {
  competition_id: number
  attack_definition: string
  defense_definition: string
  weights: SeverityWeights
  rates: {
    weighted_fouls_per_defense: number
    weighted_fouls_per_attack: number
  }
  teams: FavourabilityTeam[]
}
