import { DEFAULT_WEIGHTS } from '../api/types'
import type { SeverityWeights } from '../api/types'

interface Props {
  weights: SeverityWeights
  onChange: (w: SeverityWeights) => void
}

// Ordered high → low so the UI reads like a severity ladder.
const FIELDS: { key: keyof SeverityWeights; label: string; hint: string }[] = [
  { key: 'penalty', label: 'Penalty', hint: 'Spot-kick awarded' },
  { key: 'red', label: 'Red / 2nd yellow', hint: 'Sending-off' },
  { key: 'yellow', label: 'Yellow', hint: 'Caution' },
  { key: 'foul', label: 'Ordinary foul', hint: 'Whistle, no card' },
  { key: 'advantage', label: 'Advantage', hint: 'Foul seen, play on' },
]

const isDefault = (w: SeverityWeights) =>
  FIELDS.every((f) => w[f.key] === DEFAULT_WEIGHTS[f.key])

export default function WeightControls({ weights, onChange }: Props) {
  const set = (key: keyof SeverityWeights, value: number) => {
    if (Number.isNaN(value) || value < 0) return
    onChange({ ...weights, [key]: value })
  }

  return (
    <div className="rounded-xl bg-white ring-1 ring-slate-200 p-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-700">
            Decision severity weights
          </h3>
          <p className="mt-0.5 text-xs text-slate-400">
            How much each referee decision counts. A penalty is a far bigger
            call than a midfield free kick — tune these and the analysis
            recomputes.
          </p>
        </div>
        <button
          onClick={() => onChange({ ...DEFAULT_WEIGHTS })}
          disabled={isDefault(weights)}
          className="shrink-0 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40"
        >
          Reset
        </button>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {FIELDS.map((f) => (
          <div key={f.key}>
            <label
              htmlFor={`w-${f.key}`}
              className="block text-xs font-medium text-slate-600"
            >
              {f.label}
            </label>
            <input
              id={`w-${f.key}`}
              type="number"
              min={0}
              step={0.5}
              value={weights[f.key]}
              onChange={(e) => set(f.key, e.target.valueAsNumber)}
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-900 shadow-sm focus:border-pitch-500 focus:outline-none focus:ring-1 focus:ring-pitch-500"
            />
            <p className="mt-1 text-[11px] leading-tight text-slate-400">
              {f.hint}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
