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

const axisRange = (vals: number[]) => {
  const m = Math.max(2.5, ...vals.map((v) => Math.abs(v))) * 1.15
  return [-m, m]
}

// Two axes of favour: x = protection when attacking, y = leniency when
// defending. Top-right = most favoured, bottom-left = most policed. ±2σ bands
// mark where a team becomes a genuine outlier on that axis.
export default function FavouredQuadrant({ teams, isLoading, isError }: Props) {
  const { plotData, layout } = useMemo(() => {
    const x = teams.map((t) => t.z_protection)
    const y = teams.map((t) => t.z_leniency)
    const size = teams.map(
      (t) => t.weighted_fouls_committed + t.weighted_fouls_awarded,
    )
    const maxSize = Math.max(1, ...size)

    const trace = {
      type: 'scatter',
      mode: 'markers+text',
      x,
      y,
      text: teams.map((t) => t.team_name),
      textposition: 'top center',
      textfont: { size: 9, color: '#475569' },
      customdata: teams.map((t) => [t.favourability]),
      marker: {
        size: size.map((s) => 8 + (s / maxSize) * 22),
        color: teams.map((t) => t.favourability),
        colorscale: 'RdYlGn',
        cmid: 0,
        line: { color: 'rgba(15,23,42,0.25)', width: 1 },
        opacity: 0.85,
      },
      hovertemplate:
        '<b>%{text}</b><br>' +
        'Protection (attacking): %{x:+.2f}<br>' +
        'Leniency (defending): %{y:+.2f}<br>' +
        'Favourability: %{customdata[0]:+.2f}<extra></extra>',
    }

    const rx = axisRange(x)
    const ry = axisRange(y)

    // ±2σ outlier bands + zero cross-hairs.
    const line = (
      x0: number,
      y0: number,
      x1: number,
      y1: number,
      color: string,
      dash?: string,
    ) => ({
      type: 'line',
      x0,
      y0,
      x1,
      y1,
      line: { color, width: dash ? 1 : 2, dash: dash ?? 'solid' },
      layer: 'below',
    })

    const layout = {
      height: 520,
      margin: { l: 60, r: 24, t: 10, b: 50 },
      xaxis: {
        title: { text: '← policed when attacking   ·   Protection   ·   protected →' },
        range: rx,
        zeroline: false,
        fixedrange: true,
      },
      yaxis: {
        title: { text: '← policed when defending · Leniency · let off →' },
        range: ry,
        zeroline: false,
        fixedrange: true,
      },
      shapes: [
        line(0, ry[0], 0, ry[1], '#94a3b8'),
        line(rx[0], 0, rx[1], 0, '#94a3b8'),
        line(2, ry[0], 2, ry[1], '#cbd5e1', 'dot'),
        line(-2, ry[0], -2, ry[1], '#cbd5e1', 'dot'),
        line(rx[0], 2, rx[1], 2, '#cbd5e1', 'dot'),
        line(rx[0], -2, rx[1], -2, '#cbd5e1', 'dot'),
      ],
      annotations: [
        {
          x: rx[1],
          y: ry[1],
          text: 'most favoured',
          showarrow: false,
          xanchor: 'right',
          yanchor: 'top',
          font: { size: 11, color: '#16a34a' },
        },
        {
          x: rx[0],
          y: ry[0],
          text: 'most policed',
          showarrow: false,
          xanchor: 'left',
          yanchor: 'bottom',
          font: { size: 11, color: '#dc2626' },
        },
      ],
    }

    return {
      plotData: [trace] as unknown as Data[],
      layout: layout as unknown as Partial<Layout>,
    }
  }, [teams])

  return (
    <ChartCard
      title="Favoured vs policed"
      subtitle="Each team on two axes of referee favour. Bubble size = total weighted decisions involving the team. Dotted lines mark ±2σ outlier thresholds."
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
