import { useMemo } from 'react'
import type { Data, Layout } from 'plotly.js'
import Plot from './Plot'
import ChartCard from './ChartCard'
import type { FavourabilityTeam } from '../api/types'

interface Props {
  teams: FavourabilityTeam[]
  isLoading?: boolean
  isError?: boolean
}

// Zero-centered diverging bars: favoured teams push green to the right,
// disadvantaged push red to the left. This is the headline "who got the
// decisions" view.
export default function FavourabilityLeaderboard({
  teams,
  isLoading,
  isError,
}: Props) {
  const { plotData, layout } = useMemo(() => {
    // API returns most-favoured first; Plotly's horizontal bars grow upward, so
    // reverse to put the most-favoured team at the TOP.
    const ordered = [...teams].reverse()

    const y = ordered.map((t) => t.team_name)
    const x = ordered.map((t) => t.favourability)
    const customdata = ordered.map((t) => [
      t.z_leniency,
      t.z_protection,
      t.leniency_outlier || t.protection_outlier ? '  ●' : '',
    ])

    const trace = {
      type: 'bar',
      orientation: 'h',
      x,
      y,
      customdata,
      marker: {
        color: x,
        colorscale: 'RdYlGn',
        cmid: 0,
        line: { color: 'rgba(15,23,42,0.15)', width: 1 },
      },
      hovertemplate:
        '<b>%{y}</b>%{customdata[2]}<br>' +
        'Favourability: %{x:.2f}<br>' +
        'Leniency (defending): %{customdata[0]:+.2f}<br>' +
        'Protection (attacking): %{customdata[1]:+.2f}' +
        '<extra></extra>',
    }

    const layout = {
      height: Math.max(360, ordered.length * 20 + 90),
      margin: { l: 130, r: 24, t: 10, b: 44 },
      bargap: 0.35,
      xaxis: {
        title: { text: '← disadvantaged   ·   Favourability index   ·   favoured →' },
        zeroline: true,
        zerolinecolor: '#475569',
        zerolinewidth: 2,
        fixedrange: true,
      },
      yaxis: { automargin: true, fixedrange: true, tickfont: { size: 11 } },
    }

    return {
      plotData: [trace] as unknown as Data[],
      layout: layout as unknown as Partial<Layout>,
    }
  }, [teams])

  return (
    <ChartCard
      title="Favourability leaderboard"
      subtitle="Net referee favour per team = leniency when defending + protection when attacking (standardized). ● marks a statistical outlier (|z| ≥ 2 on either side)."
      isLoading={isLoading}
      isError={isError}
      isEmpty={teams.length === 0}
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
