import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { wakeBackend } from '../api/client'

type Status = 'idle' | 'waking' | 'awake' | 'down'

// On Render's free tier the backend sleeps when idle, so the first load after a
// while can fail or hang. This control pings /health to wake it, then refetches
// every query once it's up.
export default function BackendStatus() {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<Status>('idle')

  const wake = async () => {
    setStatus('waking')
    const ok = await wakeBackend()
    if (ok) {
      setStatus('awake')
      // API is live again — refetch competitions, definitions, favourability…
      queryClient.invalidateQueries()
    } else {
      setStatus('down')
    }
  }

  return (
    <div className="rounded-xl bg-slate-50 ring-1 ring-slate-200 px-5 py-3 flex flex-wrap items-center gap-3">
      <button
        onClick={wake}
        disabled={status === 'waking'}
        className="shrink-0 rounded-lg bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50 flex items-center gap-2"
      >
        {status === 'waking' && (
          <span className="h-3.5 w-3.5 rounded-full border-2 border-white/40 border-t-white animate-spin" />
        )}
        {status === 'waking' ? 'Waking backend…' : 'Wake backend'}
      </button>
      <span className="text-xs text-slate-500">
        {status === 'waking' &&
          'Contacting the API — a cold start can take up to a minute.'}
        {status === 'awake' && '✅ Backend is awake — data reloaded.'}
        {status === 'down' &&
          '⚠️ Still no response. Give it a moment and try again.'}
        {status === 'idle' &&
          'Data not loading? The free-tier API may be asleep — wake it here.'}
      </span>
    </div>
  )
}
