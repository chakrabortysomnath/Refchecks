import { useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import AnalysisControls from '../components/AnalysisControls'
import WeightControls from '../components/WeightControls'
import FavourabilityLeaderboard from '../components/FavourabilityLeaderboard'
import FavouredQuadrant from '../components/FavouredQuadrant'
import FavourabilityTable from '../components/FavourabilityTable'
import { useFavourability } from '../hooks/useFavourability'
import { DEFAULT_WEIGHTS } from '../api/types'
import type {
  AttackDefinition,
  DefenseDefinition,
  SeverityWeights,
} from '../api/types'

export default function Dashboard() {
  const { user, logout } = useAuth()

  const [competitionId, setCompetitionId] = useState<number | null>(null)
  const [attackDefinition, setAttackDefinition] =
    useState<AttackDefinition>('all_combined')
  const [defenseDefinition, setDefenseDefinition] =
    useState<DefenseDefinition>('all_combined')
  const [weights, setWeights] = useState<SeverityWeights>({ ...DEFAULT_WEIGHTS })

  const fav = useFavourability(
    competitionId,
    attackDefinition,
    defenseDefinition,
    weights,
  )
  const teams = fav.data?.teams ?? []
  const mostFavoured = teams[0]
  const mostPoliced = teams[teams.length - 1]

  return (
    <div className="min-h-full flex flex-col">
      <header className="bg-pitch-700 text-white">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-3">
          <span className="text-2xl">⚽</span>
          <h1 className="text-lg font-semibold tracking-tight">RefChecks</h1>
          <span className="hidden sm:inline text-sm text-pitch-100">
            Refereeing Favourability Analysis
          </span>

          {user && (
            <div className="ml-auto flex items-center gap-3">
              <span className="text-sm text-pitch-100 hidden sm:inline">
                {user.name}
              </span>
              <button
                onClick={logout}
                className="rounded-lg bg-pitch-900/40 px-3 py-1.5 text-sm font-medium hover:bg-pitch-900/60 transition"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 py-8 space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">
              Which teams did the referees favour?
            </h2>
            <p className="mt-1 text-slate-600">
              Each foul is weighted by how big a decision it was, then compared
              against what a neutral referee would be expected to give for a
              team's own attacking and defending volume. Teams that are{' '}
              <span className="font-medium text-green-700">let off</span> when
              defending and{' '}
              <span className="font-medium text-green-700">protected</span> when
              attacking score positive.
            </p>
          </div>

          <AnalysisControls
            competitionId={competitionId}
            attackDefinition={attackDefinition}
            defenseDefinition={defenseDefinition}
            onCompetitionChange={setCompetitionId}
            onAttackChange={setAttackDefinition}
            onDefenseChange={setDefenseDefinition}
          />

          <WeightControls weights={weights} onChange={setWeights} />

          {/* Headline insight */}
          {mostFavoured && mostPoliced && (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl bg-green-50 ring-1 ring-green-200 p-5">
                <div className="text-xs font-medium uppercase tracking-wide text-green-700">
                  Most favoured
                </div>
                <div className="mt-1 text-xl font-bold text-slate-900">
                  {mostFavoured.team_name}
                </div>
                <div className="mt-0.5 text-sm text-slate-600">
                  Favourability {mostFavoured.favourability >= 0 ? '+' : ''}
                  {mostFavoured.favourability.toFixed(2)}
                </div>
              </div>
              <div className="rounded-xl bg-red-50 ring-1 ring-red-200 p-5">
                <div className="text-xs font-medium uppercase tracking-wide text-red-700">
                  Most policed
                </div>
                <div className="mt-1 text-xl font-bold text-slate-900">
                  {mostPoliced.team_name}
                </div>
                <div className="mt-0.5 text-sm text-slate-600">
                  Favourability {mostPoliced.favourability >= 0 ? '+' : ''}
                  {mostPoliced.favourability.toFixed(2)}
                </div>
              </div>
            </div>
          )}

          <FavourabilityLeaderboard
            teams={teams}
            isLoading={fav.isLoading}
            isError={fav.isError}
          />

          <FavouredQuadrant
            teams={teams}
            isLoading={fav.isLoading}
            isError={fav.isError}
          />

          <FavourabilityTable teams={teams} />

          <p className="text-xs text-slate-400">
            Measured from Statsbomb's recorded fouls only — it captures the rate
            of decisions relative to how much a team attacks and defends, a proxy
            for bias. It cannot see fouls the referee missed or wrongly gave.
            The chi-square test in earlier versions was competition-wide; this
            model produces a genuine per-team outlier signal instead (|z| ≥ 2).
          </p>
        </div>
      </main>

      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        Data: Statsbomb Open Data · Built with React + Vite
      </footer>
    </div>
  )
}
