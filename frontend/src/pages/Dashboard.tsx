import { useAuth } from '../auth/AuthContext'

export default function Dashboard() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-full flex flex-col">
      <header className="bg-pitch-700 text-white">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-3">
          <span className="text-2xl">⚽</span>
          <h1 className="text-lg font-semibold tracking-tight">RefChecks</h1>
          <span className="hidden sm:inline text-sm text-pitch-100">
            Refereeing Bias Analysis
          </span>

          {user && (
            <div className="ml-auto flex items-center gap-3">
              <span className="text-sm text-pitch-100 hidden sm:inline">
                {user.name}
              </span>
              <button
                onClick={logout}
                className="rounded-lg bg-pitch-900/40 px-3 py-1.5 text-sm font-medium hover:bg-pitch-900/60 transition"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 py-10">
          <h2 className="text-2xl font-bold text-slate-900">
            Welcome{user ? `, ${user.name.split(' ')[0]}` : ''} 👋
          </h2>
          <p className="mt-2 text-slate-600">
            You're signed in. The competition selector, bias metrics table, and
            heatmap / scatter visualizations arrive in the next build phases.
          </p>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              'Competition & definition selectors',
              'Per-team bias metrics table',
              'Foul heatmap (team × match)',
              'Attacks vs. fouls scatter plot',
            ].map((title) => (
              <div
                key={title}
                className="rounded-xl bg-white ring-1 ring-slate-200 p-5 text-slate-400"
              >
                <div className="text-sm font-medium text-slate-700">
                  {title}
                </div>
                <div className="mt-2 text-xs">Coming soon</div>
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        Data: Statsbomb Open Data · Built with React + Vite
      </footer>
    </div>
  )
}
