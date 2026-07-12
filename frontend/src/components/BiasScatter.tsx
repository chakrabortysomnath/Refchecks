import { useMemo, useState } from 'react'
import type { Data, Layout } from 'plotly.js'
import Plot from './Plot'
import ChartCard from './ChartCard'
import { useStatistics } from '../hooks/useStatistics'

type XMode = 'attacks' | 'defenses'

export default function BiasScatter({
  competitionId,
}: {
  competitionId: number | null
}) {
  const { data, isLoading, isError } = useStatistics(competitionId)
  const [xMode, setXMode] = useState<XMode>('attacks')

  const points = data?.scatter_data ?? []

  const { plotData, layout } = useMemo(() => {
    const n = points.length
    const defenses = points.map((p) => p.defenses)
    const minD = defenses.length ? Math.min(...defenses) : 0
    const maxD = defenses.length ? Math.max(...defenses) : 1
    const span = maxD - minD || 1

    // Bubble size scaled by defensive volume; distinct colour per team.
    const sizes = points.map((p) => 10 + ((p.defenses - minD) / span) * 30)
    const colors = points.map(
      (_, i) => `hsl(${Math.round((i * 360) / (n || 1))}, 70%, 50%)`,
    )

    const trace = {
      type: 'scatter',
      mode: 'markers',
      x: points.map((p) => (xMode === 'attacks' ? p.attacks : p.defenses)),
      y: points.map((p) => p.fouls_committed),
      text: points.map((p) => p.team),
      customdata: points.map((p) => [p.attacks, p.defenses]),
      marker: {
        size: sizes,
        color: colors,
        line: { width: 1, color: 'white' },
        opacity: 0.85,
      },
      hovertemplate:
        `<b>%{text}</b><br>${xMode === 'attacks' ? 'Attacks' : 'Defenses'}: %{x}<br>` +
        'Fouls committed: %{y}<br>Attacks: %{customdata[0]} · Defenses: %{customdata[1]}<extra></extra>',
    }

    const layout = {
      height: 460,
      margin: { l: 60, r: 20, t: 10, b: 50 },
      xaxis: { title: { text: xMode === 'attacks' ? 'Attacks' : 'Defenses' } },
      yaxis: { title: { text: 'Fouls committed' } },
      hovermode: 'closest',
    }

    return {
      plotData: [trace] as unknown as Data[],
      layout: layout as unknown as Partial<Layout>,
    }
  }, [points, xMode])

  if (competitionId == null) return null

  const btn = (mode: XMode, label: string) => (
    <button
      key={mode}
      onClick={() => setXMode(mode)}
      className={
        'px-3 py-1.5 ' +
        (xMode === mode
          ? 'bg-pitch-600 text-white'
          : 'bg-white text-slate-600 hover:bg-slate-50')
      }
    >
      {label}
    </button>
  )

  return (
    <ChartCard
      title="Attacks vs. fouls committed"
      subtitle="Bubble size = defensive actions · colour = team · hover for details"
      isLoading={isLoading}
      isError={isError}
      isEmpty={points.length === 0}
    >
      <div className="mb-3 inline-flex overflow-hidden rounded-lg text-sm ring-1 ring-slate-200">
        {btn('attacks', 'X: Attacks')}
        {btn('defenses', 'X: Defenses')}
      </div>
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
