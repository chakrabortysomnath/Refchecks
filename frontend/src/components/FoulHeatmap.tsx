import { useMemo } from 'react'
import type { Data, Layout } from 'plotly.js'
import Plot from './Plot'
import ChartCard from './ChartCard'
import { useStatistics } from '../hooks/useStatistics'
import type { HeatmapDataPoint } from '../api/types'

export default function FoulHeatmap({
  competitionId,
}: {
  competitionId: number | null
}) {
  const { data, isLoading, isError } = useStatistics(competitionId)

  const { plotData, layout, teamCount } = useMemo(() => {
    const points = data?.heatmap_data ?? []

    // Group each team's matches (backend returns them ordered by match date).
    const byTeam = new Map<string, HeatmapDataPoint[]>()
    for (const p of points) {
      const arr = byTeam.get(p.team) ?? []
      arr.push(p)
      byTeam.set(p.team, arr)
    }

    // Alphabetical top-to-bottom (Plotly y grows upward, so reverse).
    const teams = [...byTeam.keys()].sort().reverse()
    const maxMatches = teams.length
      ? Math.max(...[...byTeam.values()].map((a) => a.length))
      : 0
    const x = Array.from({ length: maxMatches }, (_, i) => `Match ${i + 1}`)

    const z: (number | null)[][] = []
    const customdata: string[][] = []
    for (const team of teams) {
      const pts = byTeam.get(team)!
      const zRow: (number | null)[] = []
      const cRow: string[] = []
      for (let i = 0; i < maxMatches; i++) {
        zRow.push(i < pts.length ? pts[i].foul_ratio : null)
        cRow.push(i < pts.length ? pts[i].match_description : '')
      }
      z.push(zRow)
      customdata.push(cRow)
    }

    // Plotly's types are strict and version-sensitive; build plain objects and
    // cast at the boundary (runtime shape follows the Plotly JS API).
    const trace = {
      type: 'heatmap',
      x,
      y: teams,
      z,
      customdata,
      colorscale: 'YlOrRd',
      hoverongaps: false,
      colorbar: { title: { text: 'Foul ratio' } },
      hovertemplate:
        '%{y} — %{customdata}<br>Foul ratio: %{z:.3f}<extra></extra>',
    }

    const layout = {
      height: Math.max(360, teams.length * 22 + 120),
      margin: { l: 120, r: 20, t: 10, b: 40 },
      xaxis: { side: 'top', fixedrange: true },
      yaxis: { automargin: true, fixedrange: true },
    }

    return {
      plotData: [trace] as unknown as Data[],
      layout: layout as unknown as Partial<Layout>,
      teamCount: teams.length,
    }
  }, [data])

  if (competitionId == null) return null

  return (
    <ChartCard
      title="Foul heatmap"
      subtitle="Foul ratio (fouls committed ÷ attacks) per team across each of their matches"
      isLoading={isLoading}
      isError={isError}
      isEmpty={teamCount === 0}
    >
      <Plot
        data={plotData}
        layout={layout}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
        useResizeHandler
      />
    </ChartCard>
  )
}
