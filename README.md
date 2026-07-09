# RefChecks Backend - Football Bias Analysis API

**Analyze refereeing bias using Statsbomb data and statistical significance testing.**

## Overview

RefChecks is a FastAPI-based backend for analyzing refereeing bias in football matches. It:

- Fetches match and event data from **Statsbomb Open Data** (GitHub)
- Calculates **foul metrics** by team and competition
- Performs **chi-square statistical tests** to detect bias
- Provides visualization data (heatmaps, scatter plots) for the frontend
- Supports **Google OAuth 2.0** authentication

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/chakrabortysomnath/Refchecks.git
cd Refchecks/backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Google OAuth credentials and database URL
```

**Required environment variables:**
```
DATABASE_URL=postgresql://user:password@localhost:5432/refchecks_db
GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<your-client-secret>
SECRET_KEY=<generate-with-openssl-rand-hex-32>
```

### 5. Setup Database

```bash
# Create PostgreSQL database
createdb refchecks_db

# Run migrations (if using Alembic, or just start the app)
python -m app.main
```

The database tables will be created automatically on app startup.

### 6. Load Statsbomb Data

```bash
python scripts/load_competition.py --competition "FIFA World Cup - 2022"
```

### 7. Start API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: **http://localhost:8000**  
Documentation: **http://localhost:8000/docs**

---

## API Endpoints

### Authentication
- `POST /auth/google` - Login with Google OAuth token
- `GET /auth/me` - Get current authenticated user

### Competitions
- `GET /api/competitions` - List all competitions
- `GET /api/competitions/{id}` - Get specific competition
- `GET /api/competitions/{id}/match-count` - Count matches in competition

### Matches
- `GET /api/competitions/{comp_id}/matches` - List matches in competition
- `GET /api/matches/{id}` - Get specific match
- `GET /api/matches/{id}/fouls` - Get fouls in a match

### Bias Analysis
- `GET /api/competitions/{id}/bias-analysis` - Get bias metrics for competition
  - Query params: `attack_definition`, `defense_definition`
- `GET /api/teams/{id}/bias` - Get bias for specific team
- `GET /api/definitions` - List available definitions

### Visualization Data
- `GET /api/competitions/{id}/statistics` - Get heatmap + scatter data
- `GET /api/competitions/{id}/heatmap` - Get heatmap data only
- `GET /api/competitions/{id}/scatter` - Get scatter data only

### Health
- `GET /health` - Health check
- `GET /` - API info

---

## Attack & Defense Definitions

Users can select different event classifications:

### Attack Definitions
- **all_combined**: Shots + Passes (final 3rd) + Dribbles + Carries
- **shots_only**: Shots only
- **passes_only**: Passes in final third
- **dribbles_only**: Dribbles + Carries

### Defense Definitions
- **all_combined**: Tackles + Interceptions + Blocks + Clearances + Duels (won)
- **tackles_only**: Tackles only
- **blocks_only**: Blocks + Clearances
- **duels_only**: Duels (won) only

---

## Database Schema

### Core Tables
- **competitions** - Tournament metadata
- **teams** - Team information
- **matches** - Match details
- **events** - All Statsbomb events
- **fouls** - Fouls from whistled events
- **users** - Authentication

### Cached Analysis
- **attack_events** - Cached attack counts per team/match
- **defense_events** - Cached defense counts per team/match
- **bias_metrics** - Cached bias analysis results

---

## Statistical Methods

### Chi-Square Goodness-of-Fit Test

Tests whether foul distribution across teams differs significantly from uniform expectation.

**Formula:**
```
χ² = Σ [(Observed_i - Expected_i)² / Expected_i]
```

**Interpretation:**
- **p < 0.05**: Evidence of significant bias (reject null hypothesis)
- **p ≥ 0.05**: No significant bias detected

### Foul Metrics

```
Fouls Per Attack = Fouls Committed / Total Attacks
Fouls Per Defense = Fouls Committed / Total Defenses
```

---

## Project Structure

```
app/
├── main.py                    # FastAPI entry point
├── config.py                  # Environment & OAuth config
├── database.py                # SQLAlchemy setup
├── models.py                  # ORM models (8 tables)
├── schemas.py                 # Pydantic request/response schemas
├── routes/
│   ├── auth.py               # Authentication endpoints
│   ├── competitions.py        # Competition endpoints
│   ├── matches.py            # Match endpoints
│   ├── bias.py               # Bias analysis endpoints
│   └── statistics.py         # Visualization endpoints
├── services/
│   ├── statsbomb_ingester.py # Fetch & parse Statsbomb data
│   ├── event_classifier.py   # Classify attacks/defenses
│   └── bias_calculator.py    # Calculate metrics & stats
└── utils/
    └── security.py           # JWT token handling

scripts/
└── load_competition.py        # CLI to load competition data
```

---

## Development

### Run Tests

```bash
pytest tests/
```

### Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Database Migrations (Optional with Alembic)

```bash
alembic init migrations
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## Deployment on Render

### 1. Push to GitHub

```bash
git add .
git commit -m "Initial RefChecks backend"
git push origin main
```

### 2. Create Render Web Service

- **Service**: Web Service
- **Repository**: `https://github.com/chakrabortysomnath/Refchecks`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 3. Add Environment Variables

In Render dashboard:

```
DATABASE_URL=postgresql://...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
SECRET_KEY=...
ENVIRONMENT=production
```

### 4. Create PostgreSQL Database

- **Service**: PostgreSQL
- **Name**: `refchecks_db`
- Copy connection string to `DATABASE_URL`

### 5. Deploy & Test

```bash
curl https://refchecks-api.onrender.com/health
```

---

## Troubleshooting

### Database Connection Error
```
Check DATABASE_URL format: postgresql://user:password@host:port/dbname
Ensure PostgreSQL is running and accessible
```

### Google OAuth Error
```
Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
Check Authorized redirect URIs in Google Cloud Console
Ensure token is recent (expires in 1 hour)
```

### Statsbomb Data Not Loaded
```
Check internet connection
Verify GitHub repo is accessible
Check logs for specific event parsing errors
```

---

## Next Steps

### Phase 2: User Submissions (v1.1)
- User submission form endpoint
- Voting/approval workflow
- Comment system for disputed fouls
- "Statsbomb Only" vs "Statsbomb + Approved" toggle

### Phase 3: Advanced Analytics
- Referee-specific bias tracking
- Match importance weighting
- Rolling window analysis
- Seasonal trends

---

## License

MIT

## Support

For issues, email: support@refchecks.com  
GitHub Issues: [chakrabortysomnath/Refchecks](https://github.com/chakrabortysomnath/Refchecks/issues)

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Status**: MVP - Ready for Production
