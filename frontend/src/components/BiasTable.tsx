import { useMemo, useState } from 'react'
import { useBiasAnalysis } from '../hooks/useBiasAnalysis'
import { useStatistics } from '../hooks/useStatistics'
import type {
  AttackDefinition,
  BiasMetrics,
  DefenseDefinition,
} from '../api/types'

interface Props {
  competitionId: number | null
  attackDefinition: AttackDefinition
  defenseDefinition: DefenseDefinition
}

type Row = BiasMetrics & {
  teamName: string
  // Computed client-side: the two infringement-bias measures.
  infr_defense: number // fouls committed ÷ defenses
  infr_attack: number // fouls conceded ÷ attacks
}

type SortKey =
  | 'teamName'
  | 'fouls_committed_count'
  | 'fouls_conceded_count'
  | 'total_attacks'
  | 'total_defenses'
  | 'infr_defense'
  | 'infr_attack'

const COLUMNS: {
  key: SortKey
  label: string
  numeric: boolean
  desc: string
}[] = [
  {
    key: 'teamName',
    label: 'Team',
    numeric: false,
    desc: 'The team; metrics are aggregated across all of its matches in the competition.',
  },
  {
    key: 'fouls_committed_count',
    label: 'Fouls committed',
    numeric: true,
    desc: 'Total fouls this team was penalised for committing.',
  },
  {
    key: 'fouls_conceded_count',
    label: 'Fouls conceded',
    numeric: true,
    desc: 'Total fouls awarded to this team (committed against them by opponents).',
  },
  {
    key: 'total_attacks',
    label: 'Attacks',
    numeric: true,
    desc: 'Count of attacking actions, per the selected attack definition.',
  },
  {
    key: 'total_defenses',
    label: 'Defenses',
    numeric: true,
    desc: 'Count of defensive actions, per the selected defense definition.',
  },
  {
    key: 'infr_defense',
    label: 'Infringement Bias (Defense)',
    numeric: true,
    desc: 'Fouls the team committed ÷ its defensive actions — how much it infringes when defending. Higher means more fouls relative to how much it defends.',
  },
  {
    key: 'infr_attack',
    label: 'Infringement Bias (Attack)',
    numeric: true,
    desc: 'Fouls opponents committed against the team ÷ its attacking actions — how much it gets fouled when attacking. Higher means it draws more fouls relative to how much it attacks.',
  },
]

const ratio = (n: number) => n.toFixed(3)
const pretty = (n: number | null) =>
  n == null ? '—' : n < 0.0001 ? n.toExponential(2) : n.toFixed(4)

export default function BiasTable({
  competitionId,
  attackDefinition,
  defenseDefinition,
}: Props) {
  const bias = useBiasAnalysis(
    competitionId,
    attackDefinition,
    defenseDefinition,
  )
  const stats = useStatistics(competitionId)

  const [sortKey, setSortKey] = useState<SortKey>('infr_attack')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const nameMap = useMemo(() => {
    const m = new Map<number, string>()
    stats.data?.scatter_data.forEach((s) => m.set(s.team_id, s.team))
    return m
  }, [stats.data])

  const rows = useMemo<Row[]>(() => {
    const teams = bias.data?.teams ?? []
    return teams.map((t) => ({
      ...t,
      teamName: nameMap.get(t.team_id) ?? `Team ${t.team_id}`,
      infr_defense:
        t.total_defenses > 0 ? t.fouls_committed_count / t.total_defenses : 0,
      infr_attack:
        t.total_attacks > 0 ? t.fouls_conceded_count / t.total_attacks : 0,
    }))
  }, [bias.data, nameMap])

  const sorted = useMemo(() => {
    const arr = [...rows]
    arr.sort((a, b) => {
      const cmp =
        sortKey === 'teamName'
          ? a.teamName.localeCompare(b.teamName)
          : (a[sortKey] as number) - (b[sortKey] as number)
      return sortDir === 'asc' ? cmp : -cmp
    })
    return arr
  }, [rows, sortKey, sortDir])

  const toggleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir(key === 'teamName' ? 'asc' : 'desc')
    }
  }

  if (competitionId == null) return null

  if (bias.isLoading) {
    return (
      <div className="rounded-xl bg-white ring-1 ring-slate-200 p-8">
        <div className="flex items-center gap-3 text-slate-500">
          <span className="h-4 w-4 rounded-full border-2 border-slate-300 border-t-pitch-600 animate-spin" />
          Calculating bias analysis… recomputes for the selected definitions, so
          this can take a few seconds (and the API may be waking up).
        </div>
      </div>
    )
  }

  if (bias.isError) {
    return (
      <div className="rounded-xl bg-white ring-1 ring-slate-200 p-8">
        <p className="text-sm text-red-600">
          Couldn't load the bias analysis.{' '}
          {bias.error instanceof Error ? bias.error.message : ''}
        </p>
        <button
          onClick={() => bias.refetch()}
          className="mt-3 rounded-lg bg-pitch-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-pitch-700"
        >
          Retry
        </button>
      </div>
    )
  }

  const summary = rows[0] // chi-square/p-value are competition-wide (identical across teams)

  return (
    <div className="space-y-4">
      {/* Competition-wide significance banner */}
      {summary && (
        <div className="rounded-xl bg-white ring-1 ring-slate-200 p-5">
          <div className="flex flex-wrap items-center gap-x-8 gap-y-2">
            <div>
              <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Chi-square (χ²)
              </div>
              <div className="text-lg font-semibold text-slate-900">
                {summary.chi_square_stat == null
                  ? '—'
                  : summary.chi_square_stat.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                p-value
              </div>
              <div className="text-lg font-semibold text-slate-900">
                {pretty(summary.p_value)}
              </div>
            </div>
            <div>
              <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Result
              </div>
              <span
                className={
                  'mt-0.5 inline-block rounded-full px-2.5 py-0.5 text-sm font-medium ' +
                  (summary.is_significant
                    ? 'bg-red-100 text-red-700'
                    : 'bg-green-100 text-green-700')
                }
              >
                {summary.is_significant
                  ? 'Significant bias (p < 0.05)'
                  : 'No significant bias'}
              </span>
            </div>
          </div>
          <p className="mt-3 text-xs text-slate-400">
            This is a single <strong>competition-wide</strong> test of whether
            fouls are evenly distributed across all teams — not a per-team
            result. The same χ²/p-value applies to the whole competition.
          </p>
        </div>
      )}

      {/* Per-team table */}
      <div className="rounded-xl bg-white ring-1 ring-slate-200 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-700">
            Per-team metrics
          </h3>
          {bias.isFetching && (
            <span className="text-xs text-slate-400">Updating…</span>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-slate-500">
                {COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => toggleSort(col.key)}
                    title={col.desc}
                    className={
                      'cursor-pointer select-none px-4 py-2 font-medium whitespace-nowrap ' +
                      (col.numeric ? 'text-right' : 'text-left')
                    }
                  >
                    {col.label}
                    {sortKey === col.key && (
                      <span className="ml-1 text-slate-400">
                        {sortDir === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((r) => (
                <tr
                  key={r.team_id}
                  className="border-t border-slate-100 hover:bg-slate-50"
                >
                  <td className="px-4 py-2 font-medium text-slate-900 whitespace-nowrap">
                    {r.teamName}
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums">
                    {r.fouls_committed_count}
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums">
                    {r.fouls_conceded_count}
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums">
                    {r.total_attacks}
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums">
                    {r.total_defenses}
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums">
                    {ratio(r.infr_defense)}
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums">
                    {ratio(r.infr_attack)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Column legend */}
        <dl className="border-t border-slate-100 px-5 py-4 grid gap-x-8 gap-y-2 sm:grid-cols-2">
          {COLUMNS.map((col) => (
            <div key={col.key} className="flex gap-2 text-xs">
              <dt className="font-medium text-slate-600 whitespace-nowrap">
                {col.label}
              </dt>
              <dd className="text-slate-400">{col.desc}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  )
}
