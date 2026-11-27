# ROADMAP_LOG — Sii-Football Data API
Owner: Berra (berramouhcine13@gmail.com) | Local folder: Downloads/Berra projet/Siifootball

## Session 01 — 2026-11-23
### Where we started
Project brief file (اوامر_المشروع_والافكار_الاضافية.pdf) read; its text is badly garbled (Arabic RTL encoding), so requirements were taken from the chat brief.

### Done
- Folder structure: app/, scrapers/, scripts/, config/, data/, assets/, docs/, .github/workflows/
- DB layer (SQLAlchemy Core): SQLite local / PostgreSQL via DATABASE_URL. Tables: sports, competitions, matches, api_keys, source_status.
- FastAPI: /v1/sports, /v1/competitions, /v1/fixtures, /v1/results, /v1/export/csv, /v1/latest.json|csv, admin key creation.
- Free API keys (SHA-256 hashed) + in-memory per-key rate limit (default 60/min).
- Modular scrapers: HTML (BeautifulSoup4+requests), PDF (pdfplumber tables, PyMuPDF text fallback), config-driven via config/sources.json.
- Normalized standard JSON; error isolation per source; is_stale set on failure or when older than 48h.
- latest.json / latest.csv generation; GitHub Actions every 6h; Dockerfile, Procfile, render.yaml.
- App icon: assets/icon.svg.
### Decisions
- Dates stored as ISO-UTC strings (portable). match_id = sha1(sport|competition|date|home|away)[:16].
- Sources shipped DISABLED (placeholder URLs) — real URLs must be verified and added. Seed demo matches included.
- Rate limit is in-memory (fine for 1 free instance; use Redis later if scaled).
### Next
1. Find real sources per sport (IBSA, WAFF, FIPFA, IFCPF, ICSD) and fill sources.json.
2. Tests (pytest) for parsers with saved HTML/PDF samples.
3. Push to GitHub, enable Actions, deploy on Render + Supabase.
4. Landing page + docs, then expand to all leagues.
### Reusable lessons
- Config-driven scrapers: new source = JSON entry, no code.
- Always wrap each source in try/except and flag is_stale rather than failing the run.
- Keep a single normalize layer so any source maps to one schema.
