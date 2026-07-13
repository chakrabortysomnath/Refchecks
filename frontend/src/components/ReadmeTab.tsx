// Static "How it works" write-up shown in the README tab. Explains the
// approach, the methodology, and how to drive the dashboard. Kept in sync with
// favourability_calculator.py (methodology) and the Dashboard controls.

const Section = ({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) => (
  <section className="space-y-2">
    <h3 className="text-base font-semibold text-slate-900">{title}</h3>
    <div className="space-y-2 text-sm leading-relaxed text-slate-600">
      {children}
    </div>
  </section>
)

export default function ReadmeTab() {
  return (
    <div className="rounded-xl bg-white ring-1 ring-slate-200 p-6 sm:p-8">
      <div className="max-w-3xl space-y-7">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">
            How RefChecks works
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Measuring whether referees favoured particular teams — and how to
            read the dashboard.
          </p>
        </div>

        <Section title="The question">
          <p>
            Did the referees systematically <strong>favour</strong> some teams?
            A favoured team is one that is <em>let off</em> when defending
            (fewer fouls called against it than its play warrants) and{' '}
            <em>protected</em> when attacking (more fouls awarded to it than its
            play warrants). RefChecks turns that intuition into a single,
            comparable number per team.
          </p>
        </Section>

        <Section title="The approach">
          <p>
            All data comes from{' '}
            <a
              href="https://github.com/statsbomb/open-data"
              target="_blank"
              rel="noreferrer"
              className="text-pitch-700 underline"
            >
              Statsbomb Open Data
            </a>{' '}
            — every foul, shot, tackle and pass from the competition. The core
            idea is <strong>normalisation</strong>: raw foul counts are
            misleading because teams that defend deeply commit more fouls, teams
            that attack more get fouled more, and teams that go far in a
            tournament simply play more games. So instead of counting fouls, we
            compare each team's fouls against what a <em>neutral</em> referee
            would be expected to give for that team's own attacking and
            defending volume.
          </p>
        </Section>

        <Section title="The logic, step by step">
          <ol className="list-decimal space-y-2 pl-5">
            <li>
              <strong>Weight each decision by severity.</strong> A penalty is a
              far bigger call than a midfield free kick. Every foul is weighted
              — penalty 5, red / second yellow 4, yellow 2, ordinary foul 1,
              advantage-played 0.5 (all adjustable). A foul that is both a
              penalty and a card counts once, at the higher weight.
            </li>
            <li>
              <strong>Measure volume.</strong> Each team's attacking and
              defending actions are counted using the attack/defense definitions
              you choose (e.g. shots only, tackles only, or everything
              combined).
            </li>
            <li>
              <strong>Set the neutral baseline.</strong> Across the whole
              competition we compute the average weighted fouls per defensive
              action and per attacking action — the rate a fair referee would
              apply to everyone.
            </li>
            <li>
              <strong>Compare expected vs actual.</strong> Applying those rates
              to a team's own volume gives how many weighted fouls it{' '}
              <em>should</em> have committed and been awarded. The gap between
              expected and actual is the signal.
            </li>
            <li>
              <strong>Standardise into z-scores.</strong> Each gap is converted
              to a standardized (Poisson) residual so teams are comparable and
              genuine outliers stand out (|z| ≥ 2):
              <ul className="mt-1 list-disc space-y-1 pl-5">
                <li>
                  <strong>Leniency</strong> — let off when defending.
                </li>
                <li>
                  <strong>Protection</strong> — protected when attacking.
                </li>
              </ul>
            </li>
            <li>
              <strong>Combine.</strong> The{' '}
              <strong>Favourability index = Leniency + Protection</strong>.
              Positive = net favoured, negative = net disadvantaged.
            </li>
          </ol>
        </Section>

        <Section title="Using the dashboard">
          <ul className="list-disc space-y-2 pl-5">
            <li>
              <strong>Competition &amp; definitions</strong> — pick the
              competition and how attacks/defenses are counted. Definitions
              change the volume denominators, so they change the results.
            </li>
            <li>
              <strong>Decision severity weights</strong> — tune how much each
              type of decision matters, then click{' '}
              <strong>Apply / Refresh</strong> to recompute. An “Updating…”
              spinner shows while data is loading.
            </li>
            <li>
              <strong>Hide small samples</strong> — teams with fewer than 4
              matches (e.g. group-stage exits) have noisy scores; the filter
              hides them. It only affects the view — the neutral baseline is
              still built from every team.
            </li>
            <li>
              <strong>Favourability leaderboard</strong> — the headline. Bars
              right/green = favoured, left/red = disadvantaged. ● marks a
              statistical outlier.
            </li>
            <li>
              <strong>Favoured vs policed quadrant</strong> — protection (x) vs
              leniency (y). Top-right = most favoured, bottom-left = most
              policed; dotted lines are the ±2σ outlier thresholds.
            </li>
            <li>
              <strong>Per-team breakdown</strong> — actual vs expected figures,
              both z-scores, and penalty/red counts for vs against, so you can
              see whether an index is driven by big calls or by volume.
            </li>
            <li>
              <strong>Wake backend</strong> — the API sleeps when idle; if data
              won't load, this button spins it back up (a cold start can take up
              to a minute) and reloads everything.
            </li>
          </ul>
        </Section>

        <Section title="What it can and can't tell you">
          <p>
            This measures the <em>rate</em> of refereeing decisions relative to
            how much a team plays — a strong <strong>proxy</strong> for bias,
            not proof of intent. It is built only from fouls Statsbomb recorded,
            so it cannot see fouls the referee <em>missed</em> or gave
            incorrectly. Outliers are worth a closer look, not a verdict; and
            with few matches, scores are noisier — hence the sample-size filter.
          </p>
        </Section>
      </div>
    </div>
  )
}
