import { useEffect } from 'react'
import { useCompetitions } from '../hooks/useCompetitions'
import { useDefinitions } from '../hooks/useDefinitions'
import type { AttackDefinition, DefenseDefinition } from '../api/types'

interface Props {
  competitionId: number | null
  attackDefinition: AttackDefinition
  defenseDefinition: DefenseDefinition
  onCompetitionChange: (id: number) => void
  onAttackChange: (d: AttackDefinition) => void
  onDefenseChange: (d: DefenseDefinition) => void
}

const prettify = (key: string) =>
  key.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())

const selectClass =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm ' +
  'text-slate-900 shadow-sm focus:border-pitch-500 focus:outline-none ' +
  'focus:ring-1 focus:ring-pitch-500 disabled:bg-slate-100 disabled:text-slate-400'

export default function AnalysisControls({
  competitionId,
  attackDefinition,
  defenseDefinition,
  onCompetitionChange,
  onAttackChange,
  onDefenseChange,
}: Props) {
  const {
    data: competitions,
    isLoading: compLoading,
    isError: compError,
  } = useCompetitions()
  const { data: definitions, isLoading: defLoading } = useDefinitions()

  // Default to the first competition once the list loads.
  useEffect(() => {
    if (competitionId == null && competitions && competitions.length > 0) {
      onCompetitionChange(competitions[0].id)
    }
  }, [competitions, competitionId, onCompetitionChange])

  const attackKeys = definitions
    ? Object.keys(definitions.attack_definitions)
    : []
  const defenseKeys = definitions
    ? Object.keys(definitions.defense_definitions)
    : []

  return (
    <div className="rounded-xl bg-white ring-1 ring-slate-200 p-5">
      {compError && (
        <p className="mb-3 text-sm text-red-600">
          Couldn't load competitions. The API may be waking up — try reloading
          in a moment.
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {/* Competition */}
        <div>
          <label
            htmlFor="competition"
            className="block text-xs font-medium uppercase tracking-wide text-slate-500"
          >
            Competition
          </label>
          <select
            id="competition"
            className={`mt-1 ${selectClass}`}
            disabled={compLoading || !competitions?.length}
            value={competitionId ?? ''}
            onChange={(e) => onCompetitionChange(Number(e.target.value))}
          >
            {compLoading && <option>Loading…</option>}
            {competitions?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} {c.season}
              </option>
            ))}
          </select>
        </div>

        {/* Attack definition */}
        <div>
          <label
            htmlFor="attack"
            className="block text-xs font-medium uppercase tracking-wide text-slate-500"
          >
            Attack definition
          </label>
          <select
            id="attack"
            className={`mt-1 ${selectClass}`}
            disabled={defLoading}
            value={attackDefinition}
            onChange={(e) => onAttackChange(e.target.value as AttackDefinition)}
          >
            {attackKeys.map((k) => (
              <option key={k} value={k}>
                {prettify(k)}
              </option>
            ))}
          </select>
          {definitions && (
            <p className="mt-1 text-xs text-slate-400">
              {definitions.attack_definitions[attackDefinition]}
            </p>
          )}
        </div>

        {/* Defense definition */}
        <div>
          <label
            htmlFor="defense"
            className="block text-xs font-medium uppercase tracking-wide text-slate-500"
          >
            Defense definition
          </label>
          <select
            id="defense"
            className={`mt-1 ${selectClass}`}
            disabled={defLoading}
            value={defenseDefinition}
            onChange={(e) =>
              onDefenseChange(e.target.value as DefenseDefinition)
            }
          >
            {defenseKeys.map((k) => (
              <option key={k} value={k}>
                {prettify(k)}
              </option>
            ))}
          </select>
          {definitions && (
            <p className="mt-1 text-xs text-slate-400">
              {definitions.defense_definitions[defenseDefinition]}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
