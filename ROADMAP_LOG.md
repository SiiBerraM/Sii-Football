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

## Session 01 - Termux
- Reminder: run termux-setup-storage at the start of each session
- Project copied to ~/sii, deps installed (python-cryptography via pkg)
- API tested locally, GitHub repo created: SiiBerraM/Sii-Football
- GitHub Actions workflow ran successfully
- Next: add real sources, tests, deploy to Render

## Session 01 - Part 2
- Added scrapers/ibsa_text.py (IBSA results PDF parser) and updated pdf_scraper.py
- blindfootball.sport is unreachable (DNS fails on phone and GitHub); used web.archive.org snapshot URL instead
- First real source working: ibsa-wc-2018-madrid = 44 matches, 0 skipped
- WAFF site publishes schedules as images, not scrapable; planned manual_matches.json source
- Lesson: always test a source URL from the real runner before trusting it
- Next: more IBSA PDFs, current-year sources, manual source, tests, deploy to Render

## Session 01 - Part 3
- Render and HuggingFace Docker Spaces both require a payment card/PRO: rejected (zero-cost rule)
- Built static JSON API on GitHub Pages: data/api/v1/{sports,competitions,fixtures,results}.json and per-sport files
- Public base URL: https://siiberram.github.io/Sii-Football/data/api/v1/
- Removed demo seed matches; DB has 44 real IBSA 2018 matches
- Workflow now commits the whole data folder
- Lesson: verify hosting free-tier terms (card/PRO) before planning around them
- Lesson: bot commits cause push conflicts, use git pull --rebase and take generated data files
- Next: more IBSA sources, current-year sources, manual_matches source for WAFF 2026, tests, optional Vercel/Cloudflare dynamic API with keys

## Session 01 - Part 4
- Added source type "manual" (config/manual_waff2026.json) for tournaments whose sites publish images only
- WAFF 2026 source: 1 verified match so far (Ghana 3-1 USA), more to add after verification
- Mistake fixed: a patch zip overwrote sources.json with an old copy; restored IBSA source via a python one-liner
- Lesson: build patches from the latest synced copy, and prefer small in-place edits over replacing shared config files
- Lesson: download/transfer of zip files from chat is unreliable on phone; prefer commands typed in Termux
- Now: 2 real sources, 45 matches
- Next: verified WAFF 2026 results, more IBSA PDFs, tests, optional dynamic API with keys
