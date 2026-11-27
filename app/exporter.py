import csv, json
from .config import LATEST_JSON, LATEST_CSV
from .db import engine, fetch_matches, now_iso

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


def export_latest():
    with engine.connect() as c:
        rows = fetch_matches(c, limit=0)
    LATEST_JSON.write_text(json.dumps({"generated_at": now_iso(), "count": len(rows), "matches": rows},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
    with open(LATEST_CSV, "w", newline="", encoding="utf-8") as f:
        write_csv(rows, f)
    return len(rows)
