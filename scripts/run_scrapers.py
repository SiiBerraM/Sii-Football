import json, sys, traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import update, select, insert
from app.config import CONFIG_DIR, STALE_AFTER_HOURS
from app.db import engine, init_db, upsert_match, matches, source_status, now_iso
from app.exporter import export_latest
from scrapers.base import fetch
from scrapers.registry import PARSERS
from scrapers.normalize import rows_to_matches


def record(conn, sid, ok, err, count):
    vals = {"last_run": now_iso()}
    row = conn.execute(select(source_status).where(source_status.c.source_id == sid)).first()
    fails = (row.consecutive_failures or 0) if row else 0
    if ok:
        vals.update(last_success=now_iso(), last_error=None, consecutive_failures=0, rows_parsed=count)
    else:
        vals.update(last_error=err[:1000], consecutive_failures=fails + 1)
    if row:
        conn.execute(update(source_status).where(source_status.c.source_id == sid).values(**vals))
    else:
        conn.execute(insert(source_status).values(source_id=sid, **vals))


def run_source(src):
    sid = src["id"]
    try:
        if src["type"] == "manual":
            rows = json.loads((CONFIG_DIR / src["file"]).read_text(encoding="utf-8"))
        else:
            content = fetch(src["url"])
            rows = PARSERS[src["type"]](content, src)
        found, skipped = rows_to_matches(rows, src, now_iso())
        if not found:
            raise RuntimeError(f"0 valid rows (raw={len(rows)}, skipped={skipped})")
        with engine.begin() as c:
            for m in found:
                upsert_match(c, m)
            record(c, sid, True, "", len(found))
        print(f"[OK]   {sid}: {len(found)} matches ({skipped} skipped)")
    except Exception as e:
        print(f"[FAIL] {sid}: {e}")
        traceback.print_exc()
        with engine.begin() as c:
            c.execute(update(matches).where(matches.c.source_id == sid).values(is_stale=True))
            record(c, sid, False, str(e), 0)


def mark_old_stale():
    limit = (datetime.now(timezone.utc) - timedelta(hours=STALE_AFTER_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with engine.begin() as c:
        c.execute(update(matches).where(matches.c.source_id != "seed",
                                        matches.c.source_updated_at < limit).values(is_stale=True))


def main():
    init_db()
    cfg = json.loads((CONFIG_DIR / "sources.json").read_text(encoding="utf-8"))
    for src in cfg["sources"]:
        if src.get("enabled"):
            run_source(src)
        else:
            print(f"[SKIP] {src['id']} (disabled)")
    mark_old_stale()
    print(f"Exported {export_latest()} matches to latest.json / latest.csv")


if __name__ == "__main__":
    main()
