import { useEffect, useState } from 'react'
import { apiFetch, API_URL } from './api/client'

type Health = { status: string; environment?: string; api_version?: string }

/**
 * Phase 1 scaffold landing page.
 *
 * This renders without any auth or configured env vars so the very first
 * Render deploy is verifiable before CORS / Google OAuth are wired up.
 * The Google login gate and dashboard routes are added in later phases.
 */
export default function App() {
  const [health, setHealth] = useState<'checking' | 'ok' | 'down'>('checking')

  useEffect(() => {
    let cancelled = false
    apiFetch<Health>('/health')
      .then(() => !cancelled && setHealth('ok'))
      .catch(() => !cancelled && setHealth('down'))
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="min-h-full flex flex-col">
      <header className="bg-pitch-700 text-white">
        <div className="mx-auto max-w-5xl px-4 py-4 flex items-center gap-3">
          <span className="text-2xl">⚽</span>
          <h1 className="text-xl font-semibold tracking-tight">RefChecks</h1>
          <span className="ml-auto text-sm text-pitch-100">
            Refereeing Bias Analysis
          </span>
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto max-w-5xl px-4 py-16">
          <div className="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200 p-10 text-center">
            <h2 className="text-3xl font-bold text-slate-900">
              Football refereeing bias, measured.
            </h2>
            <p className="mt-4 text-slate-600 max-w-2xl mx-auto">
              Do fouls awarded against a team correlate suspiciously with how
              much they attack versus defend? RefChecks runs a chi-square
              significance test over Statsbomb open event data to find out.
            </p>

            <div className="mt-8 inline-flex items-center gap-2 rounded-full bg-slate-100 px-4 py-2 text-sm">
              <span
                className={
                  'inline-block h-2.5 w-2.5 rounded-full ' +
                  (health === 'ok'
                    ? 'bg-green-500'
                    : health === 'down'
                      ? 'bg-red-500'
                      : 'bg-amber-400 animate-pulse')
                }
              />
              <span className="text-slate-700">
                {health === 'checking' && 'Contacting API…'}
                {health === 'ok' && 'API connected'}
                {health === 'down' &&
                  'API unreachable (cold start or config pending)'}
              </span>
            </div>

            <p className="mt-8 text-xs text-slate-400">
              Sign-in and the analysis dashboard are coming in the next build
              phases. API base:{' '}
              <code className="text-slate-500">{API_URL || '(not set)'}</code>
            </p>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        Data: Statsbomb Open Data · Built with React + Vite
      </footer>
    </div>
  )
}
