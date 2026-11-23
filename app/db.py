import json
from datetime import datetime, timezone
from sqlalchemy import (create_engine, MetaData, Table, Column, String, Integer,
                        Boolean, Text, select, insert, update, and_)
from .config import DATABASE_URL, CONFIG_DIR

_kw = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {"pool_pre_ping": True}
engine = create_engine(DATABASE_URL, future=True, **_kw)
metadata = MetaData()

sports = Table("sports", metadata,
    Column("code", String(40), primary_key=True), Column("name", String(120), nullable=False),
    Column("description", Text))

competitions = Table("competitions", metadata,
    Column("code", String(80), primary_key=True), Column("sport", String(40), nullable=False, index=True),
    Column("name", String(200), nullable=False), Column("country", String(80)), Column("season", String(20)))

matches = Table("matches", metadata,
    Column("match_id", String(40), primary_key=True),
    Column("sport", String(40), nullable=False, index=True),
    Column("competition", String(80), nullable=False, index=True),
    Column("date_utc", String(32), index=True),
    Column("status", String(20), nullable=False, index=True),
    Column("home_name", String(200)), Column("home_code", String(20)), Column("home_score", Integer),
    Column("away_name", String(200)), Column("away_code", String(20)), Column("away_score", Integer),
    Column("venue", String(250)), Column("source_url", Text),
    Column("source_id", String(80), index=True),
    Column("is_stale", Boolean, nullable=False, default=False),
    Column("source_updated_at", String(32)))

api_keys = Table("api_keys", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("key_hash", String(64), unique=True, nullable=False),
    Column("owner", String(200)), Column("rate_limit", Integer, default=60),
    Column("active", Boolean, default=True), Column("created_at", String(32)))

source_status = Table("source_status", metadata,
    Column("source_id", String(80), primary_key=True),
    Column("last_run", String(32)), Column("last_success", String(32)),
    Column("last_error", Text), Column("consecutive_failures", Integer, default=0),
    Column("rows_parsed", Integer, default=0))


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def init_db():
    metadata.create_all(engine)
    seed_file = CONFIG_DIR / "seed.json"
    if not seed_file.exists():
        return
    seed = json.loads(seed_file.read_text(encoding="utf-8"))
    with engine.begin() as c:
        if not c.execute(select(sports.c.code).limit(1)).first():
            c.execute(insert(sports), seed.get("sports", []))
        if not c.execute(select(competitions.c.code).limit(1)).first():
            c.execute(insert(competitions), seed.get("competitions", []))
        if not c.execute(select(matches.c.match_id).limit(1)).first():
            for m in seed.get("matches", []):
                m["source_updated_at"] = now_iso()
                upsert_match(c, m)


def upsert_match(conn, m):
    row = {
        "match_id": m["match_id"], "sport": m["sport"], "competition": m["competition"],
        "date_utc": m["date_utc"], "status": m["status"],
        "home_name": m["home_team"]["name"], "home_code": m["home_team"].get("code", ""),
        "home_score": m["home_team"].get("score"),
        "away_name": m["away_team"]["name"], "away_code": m["away_team"].get("code", ""),
        "away_score": m["away_team"].get("score"),
        "venue": m.get("venue", ""), "source_url": m.get("source_url", ""),
        "source_id": m.get("source_id", "seed"), "is_stale": bool(m.get("is_stale", False)),
        "source_updated_at": m.get("source_updated_at"),
    }
    exists = conn.execute(select(matches.c.match_id).where(matches.c.match_id == row["match_id"])).first()
    if exists:
        conn.execute(update(matches).where(matches.c.match_id == row["match_id"]).values(**row))
    else:
        conn.execute(insert(matches).values(**row))
    for code, name in ((m["sport"], m["sport"]),):
        if not conn.execute(select(sports.c.code).where(sports.c.code == code)).first():
            conn.execute(insert(sports).values(code=code, name=name.title()))
    if not conn.execute(select(competitions.c.code).where(competitions.c.code == m["competition"])).first():
        conn.execute(insert(competitions).values(code=m["competition"], sport=m["sport"], name=m["competition"]))


def row_to_match(r):
    return {
        "match_id": r.match_id, "sport": r.sport, "competition": r.competition,
        "date_utc": r.date_utc, "status": r.status,
        "home_team": {"name": r.home_name, "code": r.home_code or "", "score": r.home_score},
        "away_team": {"name": r.away_name, "code": r.away_code or "", "score": r.away_score},
        "venue": r.venue or "", "source_url": r.source_url or "",
        "is_stale": bool(r.is_stale), "source_updated_at": r.source_updated_at,
    }


def fetch_matches(conn, sport=None, competition=None, statuses=None,
                  date_from=None, date_to=None, limit=100, offset=0, desc=False):
    conds = []
    if sport: conds.append(matches.c.sport == sport)
    if competition: conds.append(matches.c.competition == competition)
    if statuses: conds.append(matches.c.status.in_(statuses))
    if date_from: conds.append(matches.c.date_utc >= date_from)
    if date_to: conds.append(matches.c.date_utc <= date_to)
    q = select(matches)
    if conds: q = q.where(and_(*conds))
    q = q.order_by(matches.c.date_utc.desc() if desc else matches.c.date_utc.asc())
    if limit: q = q.limit(limit).offset(offset)
    return [row_to_match(r) for r in conn.execute(q)]
