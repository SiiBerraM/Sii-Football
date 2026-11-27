# Sii-Football Data API
Free & open football data API. Phase 1: disability football (Amputee, Blind, Deaf, Powerchair, Para).
Owner: **Berra** — noreply@users.noreply.github.com — 100% free stack.

## Run locally
    pip install -r requirements.txt
    cp .env.example .env   # set ADMIN_API_KEY
    export ADMIN_API_KEY=your-secret
    python scripts/run_scrapers.py
    uvicorn app.main:app --reload

## API key
    python scripts/create_api_key.py my-app
    curl -H "X-API-Key: KEY" http://localhost:8000/v1/fixtures

Endpoints: /v1/sports /v1/competitions /v1/fixtures /v1/results /v1/export/csv /v1/latest.json /v1/latest.csv /docs

## Add a source
Edit `config/sources.json` (type html|pdf, url, sport, competition, columns) and set `enabled: true`.

## Free deployment
- Data: GitHub Actions (`.github/workflows/update.yml`) every 6h, commits latest.json/latest.csv.
- API: Render free (`render.yaml`) / Hugging Face Spaces (Dockerfile). Free Postgres: Supabase/Neon via DATABASE_URL.
