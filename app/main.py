import io
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Depends, Query, Body
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from .config import OWNER_NAME, OWNER_EMAIL, LATEST_JSON, LATEST_CSV, DEFAULT_RATE_LIMIT
from .db import init_db, engine, sports, competitions, fetch_matches, source_status
from .security import require_key, require_admin, create_key
from .exporter import write_csv


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title="Sii-Football Data API",
              description="Free open football data API - disability football first (Amputee, Blind, Deaf, Powerchair, Para).",
              version="1.0.0", lifespan=lifespan, contact={"name": OWNER_NAME, "email": OWNER_EMAIL})


class Team(BaseModel):
    name: str
    code: str = ""
    score: Optional[int] = None


class Match(BaseModel):
    match_id: str
    sport: str
    competition: str
    date_utc: Optional[str]
    status: str
    home_team: Team
    away_team: Team
    venue: str = ""
    source_url: str = ""
    is_stale: bool = False
    source_updated_at: Optional[str]


@app.get("/", include_in_schema=False)
def root():
    return {"name": "Sii-Football Data API", "owner": OWNER_NAME, "docs": "/docs", "version": "1.0.0"}


@app.get("/health", include_in_schema=False)
def health():
    with engine.connect() as c:
        src = [dict(r._mapping) for r in c.execute(select(source_status))]
    return {"status": "ok", "sources": src}


@app.get("/v1/sports", dependencies=[Depends(require_key)])
def list_sports():
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(select(sports).order_by(sports.c.code))]


@app.get("/v1/competitions", dependencies=[Depends(require_key)])
def list_competitions(sport: Optional[str] = None):
    q = select(competitions).order_by(competitions.c.code)
    if sport:
        q = q.where(competitions.c.sport == sport)
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(q)]


def _matches(statuses, sport, competition, date_from, date_to, limit, offset, desc=False):
    with engine.connect() as c:
        return fetch_matches(c, sport, competition, statuses, date_from, date_to, limit, offset, desc)


@app.get("/v1/fixtures", response_model=list[Match], dependencies=[Depends(require_key)])
def fixtures(sport: Optional[str] = None, competition: Optional[str] = None,
             date_from: Optional[str] = Query(None, description="ISO UTC e.g. 2026-01-01T00:00:00Z"),
             date_to: Optional[str] = None, limit: int = Query(100, le=500), offset: int = 0):
    return _matches(["scheduled", "live", "postponed"], sport, competition, date_from, date_to, limit, offset)


@app.get("/v1/results", response_model=list[Match], dependencies=[Depends(require_key)])
def results(sport: Optional[str] = None, competition: Optional[str] = None,
            date_from: Optional[str] = None, date_to: Optional[str] = None,
            limit: int = Query(100, le=500), offset: int = 0):
    return _matches(["finished"], sport, competition, date_from, date_to, limit, offset, desc=True)


@app.get("/v1/export/csv", dependencies=[Depends(require_key)])
def export_csv(sport: Optional[str] = None, competition: Optional[str] = None):
    rows = _matches(None, sport, competition, None, None, 0, 0)
    buf = io.StringIO()
    write_csv(rows, buf)
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=sii_football.csv"})


@app.get("/v1/latest.json", dependencies=[Depends(require_key)])
def latest_json():
    return FileResponse(LATEST_JSON, media_type="application/json")


@app.get("/v1/latest.csv", dependencies=[Depends(require_key)])
def latest_csv():
    return FileResponse(LATEST_CSV, media_type="text/csv")


class KeyRequest(BaseModel):
    owner: str
    rate_limit: int = DEFAULT_RATE_LIMIT


@app.post("/v1/admin/keys", dependencies=[Depends(require_admin)])
def new_key(req: KeyRequest = Body(...)):
    return {"api_key": create_key(req.owner, req.rate_limit), "note": "Store it now; it is not shown again."}
