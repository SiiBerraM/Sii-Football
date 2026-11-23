import csv, json
from sqlalchemy import select
from .config import LATEST_JSON, LATEST_CSV, DATA_DIR
from .db import engine, fetch_matches, now_iso, sports, competitions

API_DIR = DATA_DIR / "api" / "v1"
CSV_FIELDS = ["match_id", "sport", "competition", "date_utc", "status", "home_name", "home_code",
              "home_score", "away_name", "away_code", "away_score", "venue", "source_url",
              "is_stale", "source_updated_at"]


def flatten(m):
    return {"match_id": m["match_id"], "sport": m["sport"], "competition": m["competition"],
            "date_utc": m["date_utc"], "status": m["status"],
            "home_name": m["home_team"]["name"], "home_code": m["home_team"]["code"],
            "home_score": m["home_team"]["score"],
            "away_name": m["away_team"]["name"], "away_code": m["away_team"]["code"],
            "away_score": m["away_team"]["score"],
            "venue": m["venue"], "source_url": m["source_url"],
            "is_stale": m["is_stale"], "source_updated_at": m["source_updated_at"]}


def write_csv(rows, fp):
    w = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
    w.writeheader()
    for m in rows:
        w.writerow(flatten(m))


def _dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def write_static(rows, conn):
    """Static JSON API for GitHub Pages: data/api/v1/*.json"""
    sp = [dict(r._mapping) for r in conn.execute(select(sports).order_by(sports.c.code))]
    comps = [dict(r._mapping) for r in conn.execute(select(competitions).order_by(competitions.c.code))]
    gen = now_iso()

    def pack(items):
        return {"generated_at": gen, "count": len(items), "data": items}

    def split(ms):
        fx = [m for m in ms if m["status"] in ("scheduled", "live", "postponed")]
        rs = sorted([m for m in ms if m["status"] == "finished"],
                    key=lambda m: m["date_utc"] or "", reverse=True)
        return fx, rs

    fx, rs = split(rows)
    _dump(API_DIR / "sports.json", pack(sp))
    _dump(API_DIR / "competitions.json", pack(comps))
    _dump(API_DIR / "fixtures.json", pack(fx))
    _dump(API_DIR / "results.json", pack(rs))
    for s in sp:
        sub = [m for m in rows if m["sport"] == s["code"]]
        sfx, srs = split(sub)
        _dump(API_DIR / "sports" / s["code"] / "fixtures.json", pack(sfx))
        _dump(API_DIR / "sports" / s["code"] / "results.json", pack(srs))
        _dump(API_DIR / "sports" / s["code"] / "competitions.json",
              pack([c for c in comps if c["sport"] == s["code"]]))


def export_latest():
    with engine.connect() as c:
        rows = fetch_matches(c, limit=0)
        write_static(rows, c)
    LATEST_JSON.write_text(json.dumps({"generated_at": now_iso(), "count": len(rows), "matches": rows},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
    with open(LATEST_CSV, "w", newline="", encoding="utf-8") as f:
        write_csv(rows, f)
    return len(rows)
