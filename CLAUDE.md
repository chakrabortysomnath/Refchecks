# RefChecks — Project Context for Claude Code

**Read this file fully before making changes.** This project has a working, deployed backend with several hard-won bug fixes baked in. Section 4 (Known Gotchas) exists specifically to stop you from reintroducing bugs that were already found and fixed in production.

---

## 1. What This Project Is

RefChecks is a football (soccer) refereeing bias analysis tool. It uses Statsbomb's free open event data to calculate whether fouls awarded against a team correlate suspiciously with how much they attack vs. defend, using a chi-square significance test. Long-term vision includes crowdsourced submission of missed/incorrect foul calls with a voting/approval workflow (NOT built yet — see Section 6).

**Owner**: Somnath (chakrabortysomnath on GitHub)
**Repo**: https://github.com/chakrabortysomnath/Refchecks
**Deployment**: Render (free tier — no Shell access, see Section 5)

---

## 2. Current State (as of this handoff)

✅ **Backend is fully built, deployed, and verified working end-to-end.**
✅ **Frontend is built** (React + Vite dashboard, through "Phase 5"). See Section 6 for exactly what exists and what's still deferred.

The backend has successfully:
- Deployed on Render as a FastAPI web service (Python 3.11)
- Connected to a Render PostgreSQL database
- Loaded the complete 2022 FIFA World Cup dataset (64/64 matches, all events, all fouls) from Statsbomb's public GitHub data
- Verified bias-analysis output produces sensible, real numbers for all 32 teams (fouls committed/conceded, attack/defense counts, chi-square stat, p-value)

**Live API base URL**: `https://fefchecks-api.onrender.com` (note the `fef` spelling — this is the actual Render hostname, not a typo)
**Interactive API docs**: `https://fefchecks-api.onrender.com/docs` (Swagger UI — useful for testing any endpoint by hand)

**Frontend**: built under `frontend/` and deployed as a Render Static Site (defined by the repo-root `render.yaml` blueprint). The frontend is validated and built **only on Render** — it is not run or type-checked locally.

---

## 3. Tech Stack & Architecture
Backend:  FastAPI (Python 3.11) + SQLAlchemy + PostgreSQL
Auth:     Google OAuth 2.0 + JWT
Data:     Statsbomb Open Data (https://github.com/statsbomb/open-data) — free, no API key
Stats:    SciPy (chi-square goodness-of-fit test)
Deploy:   Render (backend web service + PostgreSQL, both free tier)
Frontend: BUILT — React + Vite + TypeScript + Tailwind + TanStack Query + Plotly, deployed as Render Static Site (see Section 6)

### Backend file structure (already built, don't recreate)
app/
├── main.py                  # FastAPI entry point, router registration, CORS
├── config.py                # Settings (env vars), Google OAuth config
├── database.py              # SQLAlchemy engine/session setup
├── models.py                # 9 ORM models (see Section 3a)
├── schemas.py                # Pydantic request/response schemas
├── routes/
│   ├── auth.py               # Google OAuth login, JWT issuance
│   ├── competitions.py       # GET/POST /api/competitions
│   ├── matches.py            # GET /api/matches, /api/competitions/{id}/matches
│   ├── bias.py                # GET /api/competitions/{id}/bias-analysis (the core feature)
│   ├── statistics.py         # GET /api/competitions/{id}/statistics (heatmap/scatter data)
│   └── admin.py               # TEMPORARY setup endpoints (see Section 5 — decide fate of this)
├── services/
│   ├── statsbomb_ingester.py # Fetches + parses Statsbomb JSON into DB
│   ├── event_classifier.py    # Maps raw events to "attack"/"defense" categories
│   └── bias_calculator.py     # Computes fouls/attacks/defenses ratios + chi-square
└── utils/
└── security.py            # JWT create/verify

### 3a. Database Schema (9 tables, already created and populated)

- **competitions** — tournament metadata (currently has 1 row: 2022 World Cup)
- **teams** — team info (32 rows for World Cup)
- **matches** — match details, home/away team + score (64 rows)
- **events** — every Statsbomb event (~100k+ rows: passes, shots, tackles, fouls, etc.)
- **fouls** — subset of events that are "Foul Committed" type, with `team_fouls_id` (who committed) and `team_fouls_against_id` (who it was committed against — see Gotcha #2)
- **attack_events** / **defense_events** — cache tables, currently NOT actively used (bias_calculator queries `events` directly via `event_classifier.py` instead of these caches — this is a known inefficiency, not a bug, and could be optimized later if performance becomes an issue)
- **bias_metrics** — cached per-team, per-competition results: fouls committed/conceded, attacks, defenses, ratios, chi-square stat, p-value, is_significant
- **users** — Google OAuth users (id, google_id, email, name, role)

### 3b. Core API Endpoints (all verified working)
GET  /health                                          — health check
GET  /docs                                             — Swagger UI
POST /auth/google                                      — Google OAuth login → JWT
GET  /auth/me                                          — current user (requires Bearer token)
GET  /api/competitions                                 — list competitions
GET  /api/competitions/{id}                             — one competition
GET  /api/competitions/{id}/match-count                 — quick match count check
GET  /api/competitions/{id}/matches                     — list matches in competition
GET  /api/matches/{id}                                  — single match
GET  /api/matches/{id}/fouls                            — fouls in a match, split by team
GET  /api/competitions/{id}/bias-analysis               — THE CORE ENDPOINT
?attack_definition=all_combined|shots_only|passes_only|dribbles_only
?defense_definition=all_combined|tackles_only|blocks_only|duels_only
Returns per-team: fouls_committed_count, fouls_conceded_count, total_attacks,
total_defenses, fouls_per_attack, fouls_per_defense, chi_square_stat, p_value,
is_significant
GET  /api/teams/{id}/bias?competition_id={id}           — bias for one team
GET  /api/definitions                                    — lists available attack/defense definition options
GET  /api/competitions/{id}/statistics                   — heatmap_data + scatter_data (pre-shaped for charts)
GET  /api/competitions/{id}/heatmap                       — heatmap_data only
GET  /api/competitions/{id}/scatter                       — scatter_data only

---

## 4. Known Gotchas — Read Before Touching Backend Code

These are real bugs that were found and fixed during initial deployment. **Do not reintroduce them** if refactoring `statsbomb_ingester.py` or `bias_calculator.py`.

### Gotcha #1: Statsbomb JSON has inconsistent key shapes for "team"
- In `matches.json`, team info uses **prefixed** keys: `home_team_id`, `home_team_name`, `country`.
- In `events.json`, team info uses **plain** keys: `id`, `name`.
- `get_or_create_team()` expects the **plain** shape. `load_match_data()` normalizes the prefixed match-level shape into plain before calling it. If you touch this code, preserve that normalization step.

### Gotcha #2: `team_fouls_against_id` requires match context
- A foul event on its own only tells you which team committed it, not who it was committed against.
- The fix: `load_match_data()` passes `home_team.id` and `away_team.id` down through `load_event_data()` → `create_foul_record()`, which computes "whichever team is NOT the one that committed the foul" as the team fouled against.
- If you ever bulk-reload fouls without this context threaded through, `team_fouls_against_id` will silently be `NULL` again. There's an admin endpoint (`POST /api/admin/backfill-fouls-against`) that can retroactively fix this from existing Match records if it ever regresses.

### Gotcha #3: `foul_committed.type` and `.card` are nested dicts, not strings
- Statsbomb gives `{"id": 24, "name": "Handball"}`, but the DB columns (`foul_type`, `card_type`) are plain strings.
- `create_foul_record()` extracts `.get("name")` from these nested dicts. Don't pass the dict directly — Postgres will throw `can't adapt type 'dict'`.

### Gotcha #4: A single bad insert can silently cascade and fail dozens of subsequent inserts
- SQLAlchemy sessions enter a broken state after a failed flush, until `db.rollback()` is called.
- `load_event_data()`'s exception handler calls `db.rollback()` for exactly this reason. If you remove it "to clean up the code," you will reintroduce a bug where one malformed event corrupts the loading of every subsequent event in that match.

### Gotcha #5: `db.merge()` on an object with no primary key set tries to INSERT, not UPDATE
- This bit us hard: `calculate_team_bias()` used to always construct a fresh `BiasMetrics()` object and call `db.merge()`. Since a unique constraint exists on `(competition_id, team_id)`, this always failed silently (caught by a `try/except`) whenever a row already existed — meaning recalculation never actually persisted.
- **Fixed** by always querying for the existing row first, and mutating it in place if found, rather than constructing-and-merging a new instance. If you touch `bias_calculator.py`, preserve this "look up, then update in place OR insert new" pattern — do not go back to `db.merge()` with a fresh instance.

### Gotcha #6: The chi-square test is competition-wide, not per-team
- `perform_chi_square_test()` computes ONE test statistic testing "are fouls evenly distributed across all 32 teams?" — it is NOT a per-team test.
- The same `chi_square_stat`/`p_value` value is intentionally written to every team's row in `bias_metrics`. This is a deliberate simplification, documented in code comments. If a future design wants genuine per-team significance testing (e.g., comparing each team's foul rate to their own attack/defense volume), that requires new logic — don't assume the existing field represents that.

### Gotcha #7: Statsbomb's repo is `statsbomb/open-data`, not `statsbomb/StatsBombOpenData`
- The correct raw base URL is `https://raw.githubusercontent.com/statsbomb/open-data/master/data`. An earlier version of this code used a wrong (non-existent) repo name that 404'd. If any hardcoded URLs to Statsbomb reappear, verify against this.

### Gotcha #8: Timestamps are `HH:MM:SS.mmm`, not `MM:SS`
- Event timestamps in Statsbomb JSON are formatted as full `HH:MM:SS.mmm` strings (representing time within that period, resetting each half), not `MM:SS`. `load_event_data()` parses this correctly into total seconds. Don't naively split on `:` and take the first segment.

### Gotcha #9: Render's free tier has no Shell access
- This is why `app/routes/admin.py` exists — HTTP-triggerable endpoints protected by a query-param secret key (`ADMIN_SETUP_KEY` env var) that do what you'd normally do via `python scripts/xyz.py` in a Shell. See Section 5 for what to do with this file going forward.
- `scripts/load_competition.py` exists as a CLI equivalent but **cannot actually be run** on this deployment target since there's no Shell — it's effectively dead code unless the hosting plan changes.

### Gotcha #10: Swagger UI / browser can serve stale cached GET responses
- When debugging, if a GET response looks suspiciously identical to a previous one (down to timestamps) after you've made a change that should affect it, don't trust it — verify with `curl` from a terminal, which bypasses browser caching.

---

## 5. The `admin.py` Question — Decide This Early

`app/routes/admin.py` contains five endpoints used to bootstrap the database on a Shell-less Render free tier:
POST /api/admin/init-db
GET  /api/admin/list-competitions
POST /api/admin/load-competition
POST /api/admin/backfill-fouls-against
POST /api/admin/recalculate-bias
These are protected only by a shared-secret query param (`ADMIN_SETUP_KEY` env var in Render), which is fine for initial setup but not great long-term hygiene. Options going forward:
1. **Leave them** — low risk if the secret key is strong and not committed anywhere, useful for loading future competitions (e.g., 2024 Euro) later.
2. **Remove/disable them** now that initial setup is done, and switch to a proper migration/seed workflow if the hosting plan ever upgrades to include Shell access.

No urgent action needed, but don't casually delete this file without checking whether more competitions will be loaded via it in the future.

---

## 6. Frontend — Built (Phase 5)

**The frontend is built.** It lives under `frontend/` and is deployed as a Render Static Site defined by the repo-root `render.yaml` blueprint. It is built and validated **only on Render** (the maintainer has no local Node toolchain) — do not assume a local dev/build step exists.

### What's built and working
- **Stack**: React 18 + Vite 5 + TypeScript + Tailwind + TanStack Query + Plotly (`react-plotly.js`)
- **Competition selector + attack/defense definition selectors** (`AnalysisControls`), driven by `/api/definitions`
- **Per-team bias metrics table** (`BiasTable`) — fouls committed/conceded, attacks, defenses, two client-computed "infringement bias" ratios, sortable columns, header tooltips + a column legend, plus a competition-wide χ²/p-value significance banner (correctly labelled as competition-wide, not per-team — see Gotcha #6)
- **Scatter plot** (`BiasScatter`) and **foul heatmap** (`FoulHeatmap`), both Plotly, fed by `/api/competitions/{id}/statistics`
- **Responsive** layout (desktop + mobile)
- Config via `VITE_API_URL` (and `VITE_GOOGLE_CLIENT_ID`), inlined at build time.

### Deferred: the Google OAuth login gate
- The full auth stack exists (`AuthContext`, `LoginPage`, `ProtectedRoute`, `@react-oauth/google`) but is **intentionally disabled** — the dashboard renders ungated because the bias-analysis endpoints are public. See `frontend/src/App.tsx`.
- To re-enable later: wrap the `/` route in `<ProtectedRoute>` (and restore the `GoogleOAuthProvider`/`AuthProvider` wrappers), then set `VITE_GOOGLE_CLIENT_ID` and add the frontend origin to Google Cloud Console. **Not wanted right now** per product owner.

### Remaining deploy-time steps (done in Render/Google, not in code)
- Sync the `render.yaml` blueprint → creates the `refchecks-frontend` static site.
- Set `VITE_API_URL` (`https://fefchecks-api.onrender.com`) + `VITE_GOOGLE_CLIENT_ID`, then redeploy (Vite inlines these at build time).
- Add the resulting `*.onrender.com` URL to the backend's `CORS_ORIGINS`, or browser API calls will be blocked.

### Explicitly NOT in scope yet (Phase 2, future work)
- User-submitted foul entries (missed/incorrect calls)
- Voting/approval workflow (3-approver consensus)
- Comment/dispute threads
- "Statsbomb only" vs. "Statsbomb + approved" toggle
- Cross-competition aggregate analysis
- Referee-specific tracking (explicitly declined by product owner)

### Design context worth knowing
- Original plan called for Plotly.js for heatmap/scatter — no hard requirement, use whatever renders cleanly in React (Plotly, Recharts, D3, etc. all acceptable)
- Data volume is small (32 teams, 64 matches) — no pagination/virtualization concerns
- No real-time requirements — this is post-match retrospective analysis, batch-loaded

---

## 7. Environment Variables Reference

Backend `.env` (already configured in Render, don't need to recreate unless setting up local dev):
DATABASE_URL=<Render PostgreSQL connection string>
GOOGLE_CLIENT_ID=<configured>
GOOGLE_CLIENT_SECRET=<configured>
SECRET_KEY=<JWT signing key>
ADMIN_SETUP_KEY=<shared secret for admin.py endpoints>
ENVIRONMENT=production
CORS_ORIGINS=<needs updating once frontend URL exists>

**Important**: Once the frontend is deployed, update `CORS_ORIGINS` in Render's backend environment variables to include the frontend's URL, or API calls from the browser will be blocked.

Frontend `.env` (see `frontend/.env.example`):
VITE_API_URL=https://fefchecks-api.onrender.com
VITE_GOOGLE_CLIENT_ID=<same client ID as backend>

---

## 8. Deployment Notes

- Backend and frontend are separate Render services, same GitHub repo
- Backend: Web Service, Python runtime, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Frontend: Static Site (`render.yaml` blueprint), `npm install && npm run build`, publish directory `dist` — builds only on Render, not locally
- Free tier constraints: no Shell, spins down on inactivity (cold start delay on first request after idle)
- Google OAuth redirect URIs need updating in Google Cloud Console once frontend URL is known

---

## 9. How to Verify Backend Is Still Healthy

Quick smoke test before building against it:
```bash
curl https://fefchecks-api.onrender.com/health
curl https://fefchecks-api.onrender.com/api/competitions
curl "https://fefchecks-api.onrender.com/api/competitions/1/bias-analysis"
```
Expect: healthy status, one competition (2022 World Cup), and 32 teams with non-null `fouls_conceded_count` and `p_value`. If any of this looks wrong, re-read Section 4 before debugging from scratch.
