# RefChecks Frontend

React + Vite + TypeScript single-page app for the RefChecks refereeing bias
analysis tool. Talks to the FastAPI backend and renders the bias dashboard,
foul heatmap, and attacks-vs-fouls scatter plot.

## Stack

- React 18 + Vite 5 + TypeScript
- Tailwind CSS for styling
- TanStack Query for data fetching / caching
- Plotly.js for the heatmap and scatter plot
- `@react-oauth/google` for Google login → backend JWT

## Environment variables

Vite inlines `VITE_*` variables **at build time**, so they must be set before
the build runs. See `.env.example`.

| Variable                | Purpose                                            |
| ----------------------- | -------------------------------------------------- |
| `VITE_API_URL`          | Base URL of the backend API (no trailing slash)    |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth Client ID (same one the backend uses) |

## Deployment (Render Static Site)

Defined as a Blueprint in the repo-root `render.yaml`:

- **Root directory:** `frontend`
- **Build command:** `npm install && npm run build`
- **Publish directory:** `dist`
- **SPA rewrite:** `/*` → `/index.html`

### First-time setup order

1. Sync the Blueprint in Render → creates the `refchecks-frontend` static site.
2. Set `VITE_API_URL` and `VITE_GOOGLE_CLIENT_ID` in the site's Environment.
3. Trigger a redeploy so the vars are baked into the bundle.
4. Add the site's `*.onrender.com` URL to the backend's `CORS_ORIGINS`.
5. Add the same URL to Google Cloud Console → Authorized JavaScript origins.

> Manual fallback if the Blueprint isn't used: create a Static Site pointing at
> this repo with the settings above.

## Scripts

- `npm run dev` — local dev server (requires Node; not available on the
  maintainer's machine — builds are validated on Render)
- `npm run build` — type-check + production build to `dist/`
- `npm run preview` — preview the production build locally
