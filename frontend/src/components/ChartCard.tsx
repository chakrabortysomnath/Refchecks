import type { ReactNode } from 'react'

interface Props {
  title: string
  subtitle?: string
  isLoading?: boolean
  isError?: boolean
  isEmpty?: boolean
  children: ReactNode
}

export default function ChartCard({
  title,
  subtitle,
  isLoading,
  isError,
  isEmpty,
  children,
}: Props) {
  return (
    <div className="rounded-xl bg-white ring-1 ring-slate-200 p-5">
      <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      {subtitle && <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>}

      <div className="mt-4">
        {isLoading ? (
          <div className="flex items-center gap-3 py-10 text-slate-500">
            <span className="h-4 w-4 rounded-full border-2 border-slate-300 border-t-pitch-600 animate-spin" />
            Loading chart… (the API may be waking up)
          </div>
        ) : isError ? (
          <p className="py-10 text-sm text-red-600">
            Couldn't load chart data. Try reloading in a moment.
          </p>
        ) : isEmpty ? (
          <p className="py-10 text-sm text-slate-400">No data to plot.</p>
        ) : (
          children
        )}
      </div>
    </div>
  )
}
