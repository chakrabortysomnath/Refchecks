import { useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import AnalysisControls from '../components/AnalysisControls'
import BiasTable from '../components/BiasTable'
import BiasScatter from '../components/BiasScatter'
import FoulHeatmap from '../components/FoulHeatmap'
import type { AttackDefinition, DefenseDefinition } from '../api/types'

export default function Dashboard() {
  const { user, logout } = useAuth()

  // Selection state that drives the bias table + charts in later phases.
  const [competitionId, setCompetitionId] = useState<number | null>(null)
  const [attackDefinition, setAttackDefinition] =
    useState<AttackDefinition>('all_combined')
  const [defenseDefinition, setDefenseDefinition] =
    useState<DefenseDefinition>('all_combined')

  return (
    <div className="min-h-full flex flex-col">
      <header className="bg-pitch-700 text-white">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-3">
          <span className="text-2xl">⚽</span>
          <h1 className="text-lg font-semibold tracking-tight">RefChecks</h1>
          <span className="hidden sm:inline text-sm text-pitch-100">
            Refereeing Bias Analysis
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
              Bias Analysis
            </h2>
            <p className="mt-1 text-slate-600">
              Choose a competition and how attacks / defenses are counted.
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

          <BiasTable
            competitionId={competitionId}
            attackDefinition={attackDefinition}
            defenseDefinition={defenseDefinition}
          />

          <BiasScatter competitionId={competitionId} />
          <FoulHeatmap competitionId={competitionId} />
        </div>
      </main>

      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        Data: Statsbomb Open Data · Built with React + Vite
      </footer>
    </div>
  )
}
