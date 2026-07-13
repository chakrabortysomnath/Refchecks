import { useMemo, useState } from 'react'
import type { FavourabilityTeam } from '../api/types'

interface Props {
  teams: FavourabilityTeam[]
}

type SortKey =
  | 'team_name'
  | 'favourability'
  | 'z_leniency'
  | 'z_protection'
  | 'weighted_fouls_committed'
  | 'weighted_fouls_awarded'

const COLUMNS: {
  key: SortKey
  label: string
  numeric: boolean
  desc: string
}[] = [
  { key: 'team_name', label: 'Team', numeric: false, desc: 'Team, aggregated across all its matches.' },
  {
    key: 'favourability',
    label: 'Favourability',
    numeric: true,
    desc: 'Net referee favour = leniency + protection (standardized). Positive = favoured, negative = disadvantaged.',
  },
  {
    key: 'z_leniency',
    label: 'Leniency (def)',
    numeric: true,
    desc: 'Standardized gap between expected and actual weighted fouls called against the team. Positive = let off when defending.',
  },
  {
    key: 'z_protection',
    label: 'Protection (att)',
    numeric: true,
    desc: 'Standardized gap between actual and expected weighted fouls awarded to the team. Positive = protected when attacking.',
  },
  {
    key: 'weighted_fouls_committed',
    label: 'Wtd committed (exp)',
    numeric: true,
    desc: 'Severity-weighted fouls called against the team, with the neutral-referee expectation for its defensive volume in parentheses.',
  },
  {
    key: 'weighted_fouls_awarded',
    label: 'Wtd awarded (exp)',
    numeric: true,
    desc: 'Severity-weighted fouls awarded to the team, with the neutral-referee expectation for its attacking volume in parentheses.',
  },
]

const signed = (n: number) => (n >= 0 ? `+${n.toFixed(2)}` : n.toFixed(2))

// Color a z-score: green favoured, red disadvantaged, stronger past ±2.
const zClass = (z: number) => {
  if (z >= 2) return 'text-green-700 font-semibold'
  if (z > 0) return 'text-green-600'
  if (z <= -2) return 'text-red-700 font-semibold'
  if (z < 0) return 'text-red-600'
  return 'text-slate-500'
}

export default function FavourabilityTable({ teams }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('favourability')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const sorted = useMemo(() => {
    const arr = [...teams]
    arr.sort((a, b) => {
      const cmp =
        sortKey === 'team_name'
          ? a.team_name.localeCompare(b.team_name)
          : (a[sortKey] as number) - (b[sortKey] as number)
      return sortDir === 'asc' ? cmp : -cmp
    })
    return arr
  }, [teams, sortKey, sortDir])

  const toggleSort = (key: SortKey) => {
    if (key === sortKey) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else {
      setSortKey(key)
      setSortDir(key === 'team_name' ? 'asc' : 'desc')
    }
  }

  if (teams.length === 0) return null

  return (
    <div className="rounded-xl bg-white ring-1 ring-slate-200 overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-100">
        <h3 className="text-sm font-semibold text-slate-700">
          Per-team breakdown
        </h3>
        <p className="mt-0.5 text-xs text-slate-400">
          Big-call columns show penalties / red cards so you can tell whether a
          team's index is driven by match-defining decisions or by volume.
        </p>
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
              <th
                className="px-4 py-2 text-right font-medium whitespace-nowrap"
                title="Penalties and red cards awarded TO the team (for) vs called AGAINST it."
              >
                Big calls for / against
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((t) => (
              <tr
                key={t.team_id}
                className="border-t border-slate-100 hover:bg-slate-50"
              >
                <td className="px-4 py-2 font-medium text-slate-900 whitespace-nowrap">
                  {t.team_name}
                </td>
                <td
                  className={
                    'px-4 py-2 text-right tabular-nums ' +
                    zClass(t.favourability)
                  }
                >
                  {signed(t.favourability)}
                </td>
                <td
                  className={
                    'px-4 py-2 text-right tabular-nums ' + zClass(t.z_leniency)
                  }
                >
                  {signed(t.z_leniency)}
                </td>
                <td
                  className={
                    'px-4 py-2 text-right tabular-nums ' + zClass(t.z_protection)
                  }
                >
                  {signed(t.z_protection)}
                </td>
                <td className="px-4 py-2 text-right tabular-nums text-slate-700">
                  {t.weighted_fouls_committed.toFixed(1)}{' '}
                  <span className="text-slate-400">
                    ({t.expected_committed.toFixed(1)})
                  </span>
                </td>
                <td className="px-4 py-2 text-right tabular-nums text-slate-700">
                  {t.weighted_fouls_awarded.toFixed(1)}{' '}
                  <span className="text-slate-400">
                    ({t.expected_awarded.toFixed(1)})
                  </span>
                </td>
                <td className="px-4 py-2 text-right tabular-nums text-slate-600 whitespace-nowrap">
                  <span title="Penalties / reds awarded to the team">
                    {t.awarded_breakdown.penalty}P·{t.awarded_breakdown.red}R
                  </span>
                  <span className="text-slate-300"> / </span>
                  <span title="Penalties / reds called against the team">
                    {t.committed_breakdown.penalty}P·{t.committed_breakdown.red}R
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <dl className="border-t border-slate-100 px-5 py-4 grid gap-x-8 gap-y-2 sm:grid-cols-2">
        {COLUMNS.filter((c) => c.numeric).map((col) => (
          <div key={col.key} className="flex gap-2 text-xs">
            <dt className="font-medium text-slate-600 whitespace-nowrap">
              {col.label}
            </dt>
            <dd className="text-slate-400">{col.desc}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
